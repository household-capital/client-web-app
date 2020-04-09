# Python Imports
import json
import base64
import math

# Django Imports
from django.conf import settings
from django.utils import timezone

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.api_AMAL import apiAMAL
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Logging import write_applog
from apps.lib.site_DataMapping import mapLoanToFacility, mapRolesToFacility, mapPropertyToFacility, mapPurposesToFacility, \
    mapValuationsToFacility, mapTransToFacility

from apps.case.models import Case
from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, FacilityPurposes, FacilityEvents


# SERVICING TASKS

@app.task(name="AMAL_Funded_Data")
def fundedData(*arg, **kwargs):
    ''' Task to updated funded information from AMALs XChange API'''

    if "Transactions" in kwargs:
        Transactions = kwargs["Transactions"]
    else:
        Transactions = True

    write_applog("INFO", 'Servicing', 'Tasks-fundedData', 'Starting AMAL Data Extract')

    amalAPI = apiAMAL()
    response = amalAPI.openAPI(True)

    if response['status'] != "Ok":
        write_applog("ERROR", 'Servicing', 'Tasks-fundedData', response['responseText'])

    # Loop through all Facility Objects and update AMAL Infomation
    qs = Facility.objects.all()
    for loan in qs:

        # Get Funded Data
        response = amalAPI.getFundedData(loan.amalID)

        if response['status'] != "Ok":
            write_applog("ERROR", 'Servicing', 'Tasks-fundedData', response['responseText'])
        else:
            for (item, value) in response['data'].items():
                setattr(loan, item, value)
        loan.save()

        # Get Transaction Data
        if Transactions:
            response = amalAPI.getTransactionData(loan.amalID)

            if response['status'] != "Ok":
                write_applog("ERROR", 'Servicing', 'Tasks-fundedData',
                             'Could not retrieve transactions - ' + str(loan.amalID))
            else:
                write_applog("INFO", 'Servicing', 'Tasks-fundedData', 'Retrieving transactions - ' + str(loan.amalID))

                for transaction in response['data']:
                    if transaction['ghosted'] == False:

                        transObj, created = FacilityTransactions.objects.get_or_create(
                            tranRef=transaction['tranRef'],
                            facility=loan
                        )

                        if created:
                            payload= mapTransToFacility(loan, transaction)
                            transObj.update(**payload)

                    else:
                        #Ghosted transactions include reversals so attempt to remove existing transactions
                        try:
                            qs=FacilityTransactions.objects.filter(facility=loan, tranRef=transaction['tranRef'])
                            qs.delete()
                        except FacilityTransactions.DoesNotExist:
                            pass

        # Additional Items - independent loop, post-update
        qs = Facility.objects.all()
        for loan in qs:
            if not loan.maxDrawdownDate and loan.settlementDate:
                loan.maxDrawdownDate = loan.settlementDate + timezone.timedelta(days=365)

            #Check approved amounts agree
            if (loan.totalLoanAmount - loan.approvedAmount) > 1:
                loan.amalReconciliation = False
            else:
                loan.amalReconciliation = True

            #Check for limit breaches
            if (loan.advancedAmount - loan.approvedAmount) > 1:
                loan.amalBreach = True
            else:
                loan.amalBreach = False


            loan.save()

    write_applog("INFO", 'Servicing', 'Tasks-fundedData', 'Finishing AMAL Data Extract')

    return 'Task completed successfully'


@app.task(name="Servicing_Synch")
def sfSynch():
    '''Updates Facility with Salesforce Loan Object Information'''

    qsFacility = Facility.objects.all()
    sfAPI = apiSalesforce()
    statusResult = sfAPI.openAPI(True)

    # Loop through all SF Loan Objects and update Facility
    listObj = sfAPI.getLoanObjList()

    if listObj['status'] == 'Ok':

        for index, loan in listObj['data'].iterrows():

            caseObj = Case.objects.filter(sfOpportunityID=loan['Opportunity__c']).get()

            loanDict = sfAPI.getLoanObjExtract(caseObj.sfOpportunityID)['data']

            if loanDict['Loan.Status__c'] != 'Inactive':

                payload = mapLoanToFacility(caseObj, loanDict)

                if qsFacility.filter(sfID__exact=loanDict['Loan.Id']):
                    payload.pop('sfID')
                    qsFacility.filter(sfID__exact=loanDict['Loan.Id']).update(**payload)
                else:
                    facilityObj = Facility.objects.create(**payload)

    return 'Task completed successfully'


@app.task(name="Servicing_Detail_Synch")
def sfDetailSynch():
    '''Updates related Facility objects with Salesforce Loan Object Information'''

    #Get Querysets
    qsFacility = Facility.objects.all()
    qsFacilityRoles = FacilityRoles.objects.all()
    qsFacilityProperty = FacilityProperty.objects.all()
    qsValuations = FacilityPropertyVal.objects.all()
    qsPurposes = FacilityPurposes.objects.all()


    # Get SF Table Data
    sfAPI = apiSalesforce()
    statusResult = sfAPI.openAPI(True)
    sfRole = sfAPI.getLoanObjRoles()['data']
    sfContact = sfAPI.getLoanObjContacts()['data']
    sfPropertyLinks = sfAPI.getLoanObjPropertyLinks()['data']
    sfProperties = sfAPI.getLoanObjProperties()['data']
    sfPurposes = sfAPI.getLoanObjPurposes()['data']

    for loan in qsFacility:

        # ROLES
        roleTable = sfRole.query('Loan__c == "' + str(loan.sfID) + '"', inplace=False)

        for index, role in roleTable.iterrows():
            contactTable = sfContact.query('Id == "' + str(role['Contact__c']) + '"', inplace=False)
            for ind, contact in contactTable.iterrows():

                payload = mapRolesToFacility(loan, contact, role)

                if qsFacilityRoles.filter(sfContactID__exact=contact['Id']):
                    payload.pop('sfContactID')
                    qsFacilityRoles.filter(sfContactID__exact=contact['Id']).update(**payload)
                else:
                    FacilityRoles.objects.create(**payload)


        # PROPERTIES

        propertyRefTable = sfPropertyLinks.query('Loan__c == "' + str(loan.sfID) + '"', inplace=False)

        # Nested loop required because of property links
        for index, property in propertyRefTable.iterrows():
            propertyID = property['Property__c']

            propertyObjTable = sfProperties.query('Id =="' + str(propertyID) + '"', inplace=False)

            for index2, propertyObj in propertyObjTable.iterrows():

                payload = mapPropertyToFacility(loan,propertyObj)

                if qsFacilityProperty.filter(sfPropertyID__exact=propertyObj['Id']):
                    payload.pop('sfPropertyID')
                    qsFacilityProperty.filter(sfPropertyID__exact=propertyObj['Id']).update(**payload)
                else:
                    FacilityProperty.objects.create(**payload)

                # Pretend separate valuation object in SF
                propertyRef = qsFacilityProperty.filter(sfPropertyID__exact=propertyObj['Id']).get()

                payload = mapValuationsToFacility(propertyRef, propertyObj)

                if qsValuations.filter(property=propertyRef):
                    payload.pop('property')
                    qsValuations.filter(property=propertyRef).update(**payload)
                else:
                    FacilityPropertyVal.objects.create(**payload)


        # PURPOSES
        purposesTable = sfPurposes.query('Loan__c == "' + str(loan.sfID) + '"', inplace=False)

        for index, purpose in purposesTable.iterrows():

            payload = mapPurposesToFacility(loan, purpose)

            if qsPurposes.filter(sfPurposeID=purpose['Id']):
                payload.pop('facility')
                qsPurposes.filter(sfPurposeID=purpose['Id']).update(**payload)
            else:
                FacilityPurposes.objects.create(**payload)


        # EVENTS (TEMP)
        try:
            qs = FacilityEvents.objects.filter(facility=loan).get()
        except FacilityEvents.DoesNotExist:
            if loan.settlementDate:
                FacilityEvents.objects.create(facility=loan, eventType=1, eventDate=loan.settlementDate, eventNotes="Facility established. Initial loan drawdown.")
        except FacilityEvents.MultipleObjectsReturned:
            pass



