# Python Imports
import datetime
import json
import base64
import math
from datetime import timedelta

# Django Imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.db.models import Q, F

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.api_AMAL import apiAMAL
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError
from apps.lib.site_Enums import facilityStatusEnum
from apps.lib.site_DataMapping import mapLoanToFacility, mapRolesToFacility, mapPropertyToFacility, \
    mapPurposesToFacility, \
    mapValuationsToFacility, mapTransToFacility

from apps.case.models import Case
from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, \
    FacilityPurposes, FacilityEvents

from apps.operational.decorators import email_admins_on_failure

# SERVICING TASKS

@app.task(name="AMAL_Funded_Data")
@email_admins_on_failure(task_name="AMAL_Funded_Data")
def fundedData(*arg, **kwargs):
    """Task to updated funded information from AMALs XChange API"""

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

                        if created or (transaction['balance'] != transObj.balance):
                            payload = mapTransToFacility(loan, transaction)
                            # Update object
                            for attr, value in payload.items():
                                setattr(transObj, attr, value)
                            transObj.save()

                    else:
                        # Ghosted transactions include reversals so attempt to remove existing transactions
                        qs = FacilityTransactions.objects.filter(facility=loan, tranRef=transaction['tranRef'])

                        if qs.exists():
                            # A reversal
                            qs.delete()

                            # Test notification of reversal
                            text = "A reversal has occurred for " + str(loan.sfLoanName) + "  |  " + str(
                                transaction['tranRef'])
                            from_email = settings.DEFAULT_FROM_EMAIL
                            subject = "AMAL Reversal - Servicing Notification"
                            to = [settings.ADMINS[0][1],
                                  'sue.moorhen@householdcapital.com',
                                  'jay.sewell@householdcapital.com']
                            msg = EmailMultiAlternatives(subject, text, from_email, to)
                            msg.send()

                        else:
                            # Did not exist in the database - a real ghosted transaction (not reverasl)
                            pass

        # Additional Items - independent loop, post-update
        qs = Facility.objects.all()
        for loan in qs:
            if not loan.maxDrawdownDate and loan.settlementDate:
                loan.maxDrawdownDate = loan.settlementDate + timezone.timedelta(days=365)

            # Check approved amounts agree
            if abs(loan.totalLoanAmount - loan.approvedAmount) > 1:
                loan.amalReconciliation = False
            else:
                loan.amalReconciliation = True

            # Check for limit breaches
            if (loan.advancedAmount - loan.approvedAmount) > 1:
                loan.amalBreach = True
            else:
                loan.amalBreach = False

            loan.save()

    write_applog("INFO", 'Servicing', 'Tasks-fundedData', 'Finishing AMAL Data Extract')

    return 'Task completed successfully'


@app.task(name="Servicing_Synch")
@email_admins_on_failure(task_name='Servicing_Synch')
def sfSynch():
    """Updates Facility with Salesforce Loan Object Information"""

    qsFacility = Facility.objects.all()

    sfAPI = apiSalesforce()
    statusResult = sfAPI.openAPI(True)

    qsFacility = Facility.objects.all()

    sfAPI = apiSalesforce()
    statusResult = sfAPI.openAPI(True)

    # Get SF Extracts
    sfListObj = sfAPI.getLoanObjList()['data']
    sfListLinkObj = sfAPI.getLoanLinkList()['data']

    # Loop through all SF Loan Objects and update Facility
    for index, loan in sfListObj.iterrows():
        sfOpp = sfListLinkObj.query('Loan__c == "' + loan["Id"] + '"', inplace=False)
        sfOpportunityId = sfOpp['Opportunity__c'].iloc[0]

        caseObj = Case.objects.filter(deleted_on__isnull=True, sfOpportunityID=sfOpportunityId).get()

        # Currently using LoanObj and Case to build Facility
        payload = mapLoanToFacility(caseObj, loan)

        if qsFacility.filter(sfID__exact=loan['Id']):
            payload.pop('sfID')
            qsFacility.filter(sfID__exact=loan['Id']).update(**payload)
        else:
            facilityObj = Facility.objects.create(**payload)

    return 'Task completed successfully'


@app.task(name="Servicing_Detail_Synch")
@email_admins_on_failure(task_name='Servicing_Detail_Synch')
def sfDetailSynch():
    """Updates related Facility objects with Salesforce Loan Object Information"""

    # Get Querysets
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
                    try:
                        FacilityRoles.objects.create(**payload)
                    except:
                        payload.pop('facility')
                        write_applog("ERROR", 'Servicing', 'Tasks-sfDetailSynch',
                                     'Could not create role -' + json.dumps(payload))
                        raiseTaskAdminError('Servicing: Could not create Facility Role', loan.sfLoanName)

        # PROPERTIES

        propertyRefTable = sfPropertyLinks.query('Loan__c == "' + str(loan.sfID) + '"', inplace=False)

        # Nested loop required because of property links
        for index, property in propertyRefTable.iterrows():
            propertyID = property['Property__c']

            propertyObjTable = sfProperties.query('Id =="' + str(propertyID) + '"', inplace=False)

            for index2, propertyObj in propertyObjTable.iterrows():

                payload = mapPropertyToFacility(loan, propertyObj)

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
                    try:
                        FacilityPropertyVal.objects.create(**payload)
                    except:
                        write_applog("ERROR", 'Servicing', 'Tasks-sfDetailSynch',
                                     'Could not create property -' + loan.sfLoanName)
                        raiseTaskAdminError('Servicing: Could not create Facility Property', loan.sfLoanName)

        # PURPOSES
        purposesTable = sfPurposes.query('Loan__c == "' + str(loan.sfID) + '"', inplace=False)

        for index, purpose in purposesTable.iterrows():

            payload = mapPurposesToFacility(loan, purpose)

            if qsPurposes.filter(sfPurposeID=purpose['Id']):
                payload.pop('facility')
                qsPurposes.filter(sfPurposeID=purpose['Id']).update(**payload)
            else:
                try:
                    FacilityPurposes.objects.create(**payload)
                except:
                    write_applog("ERROR", 'Servicing', 'Tasks-sfDetailSynch',
                                 'Could not create purpose -' + loan.sfLoanName)
                    raiseTaskAdminError('Servicing: Could not create Facility Purpose', loan.sfLoanName)

        # OTHER ITEMS

        # Populate nextAnnualService date (if required)
        if (not loan.nextAnnualService) and (loan.settlementDate is not None):
            loan.nextAnnualService = loan.settlementDate + timedelta(days=365)
        loan.save()

        # EVENTS (TEMP)
        try:
            qs = FacilityEvents.objects.filter(facility=loan).get()
        except FacilityEvents.DoesNotExist:
            if loan.settlementDate:
                FacilityEvents.objects.create(facility=loan, eventType=1, eventDate=loan.settlementDate,
                                              eventNotes="Facility established. Initial loan drawdown.")
        except FacilityEvents.MultipleObjectsReturned:
            pass


@app.task(name="SF_AMAL_Synch")
@email_admins_on_failure(task_name="SF_AMAL_Synch")
def sfAMALData():
    sfAPI = apiSalesforce()
    statusResult = sfAPI.openAPI(True)

    qsFacilities = Facility.objects.all()

    for loan in qsFacilities:
        sfAPI.updateLoanData(loan.sfID, {
            "Loan_Settlement_Date__c": loan.settlementDate.strftime("%Y-%m-%d") if loan.settlementDate else None,
            "MaxDrawdownDate__c": loan.maxDrawdownDate.strftime("%Y-%m-%d") if loan.maxDrawdownDate else None,
            "Loan_Maturity_Date__c": loan.dischargeDate.strftime("%Y-%m-%d") if loan.dischargeDate else None,
            "Advanced_Amount__c": loan.advancedAmount,
            "Current_Loan_Balance__c": loan.currentBalance
        })

    return "SF Updated Successfully"


@app.task(name="SF_Create_Task")
def sfCreateTask(payload):
    sfAPI = apiSalesforce()
    statusResult = sfAPI.openAPI(True)
    owner_email = payload.pop('owner_email')

    if statusResult['status'] != 'Ok':
        raiseTaskAdminError("Servicing Task not created",
                            "{0} task was not created for {1}".format(payload['Subject'],payload['Description']))
        if owner_email: 
            raiseTaskAdminError(
                "Servicing Task not created",
                "{0} task was not created for {1}".format(
                    payload['Subject'],
                    payload['Description']
                ),
                owner_email
            )

        write_applog("ERROR", 'Servicing', 'sfCreateTask',
                     "Task not created -" + payload['Subject'] + " " + json.dumps(statusResult['responseText']))
        return "Task failed - could not open SF API"
    
    result = sfAPI.createTask(**payload)
    if result['status'] != 'Ok':
        raiseTaskAdminError("Servicing Task not created",
                            "{0} task was not created for {1}".format(payload['Subject'],payload['Description']))
        if owner_email: 
            raiseTaskAdminError(
                "Servicing Task not created",
                "{0} task was not created for {1}".format(
                    payload['Subject'],
                    payload['Description']
                ),
                owner_email
            )
        write_applog("ERROR", 'Servicing', 'sfCreateTask',
                     "Task not created -" + payload['Subject'] + " " + json.dumps(result['responseText']))
        return "Task failed - could not create task"

    return "SF Additional Drawdown Task Created Successfully"


@app.task(name="Annual_Review_Notification")
@email_admins_on_failure(task_name='Annual_Review_Notification')
def sfAnnualReviewNotification():
    write_applog("INFO", 'Servicing', 'sfAnnualReviewNotification',
                 "Starting Annual Review SF notifications")

    futureDate = timezone.now() + timedelta(weeks=6)
    queryset = Facility.objects.filter(nextAnnualService__lte=futureDate,
                                       settlementDate__isnull=False,
                                       status=facilityStatusEnum.ACTIVE.value,
                                       annualServiceNotification=False) \
        .annotate(availableAmount=F('approvedAmount') - F('advancedAmount')) \
        .annotate(planAddition=F('totalPlanAmount') - F('totalLoanAmount')) \
        .order_by('nextAnnualService')

    for obj in queryset:

        #Create SF Task
        write_applog("INFO", 'Servicing', 'sfAnnualReviewNotification',
                     "Creating task for {0}".format(obj.sfLoanName if obj.sfLoanName else ""))

        description = "Please complete an Annual Review for " + obj.sfLoanName
        description += '\r\nWhich is due on {0}'.format(obj.nextAnnualService.strftime("%d-%m-%Y"))

        if obj.availableAmount > 0:
            description += '\r\n\r\nPlease note there are available funds under this facility (extension required?)'

        if obj.planAddition > 0:
            description += '\r\n\r\nPlease note there are plan amounts under this facility (variation required?)'


        payload = {'OwnerId' : obj.owner.profile.salesforceID,
                   'ActivityDate' : obj.nextAnnualService.strftime("%Y-%m-%d"),
                   'Subject' : 'Annual Review',
                   'Description' : description,
                   'Priority': 'Normal',
                   'WhatId' : obj.sfID,
                   'owner_email': obj.owner.email
                   }

        result = sfCreateTask(payload)
        obj.annualServiceNotification = True
        obj.save()

    write_applog("INFO", 'Servicing', 'sfAnnualReviewNotification',
                     "Completed Annual Review SF notifications")

    return "Task completed successfully"

@app.task(name="testbeat")
def test_beat():
    write_applog(
        "INFO",
        'test',
        'testing beat',
        'here'
    )
