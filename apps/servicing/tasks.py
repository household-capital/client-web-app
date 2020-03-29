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
from apps.lib.lixi.lixi_CloudBridge import CloudBridge
from apps.lib.site_Enums import caseStagesEnum
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import taskError, sendTemplateEmail

from apps.case.models import Case
from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, FacilityPurposes, FacilityEvents

from apps.lib.site_Enums import caseStagesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum, \
    pensionTypesEnum, loanTypesEnum, ragTypesEnum, channelTypesEnum, stateTypesEnum, incomeFrequencyEnum, \
    closeReasonEnum, salutationEnum, maritalEnum, appTypesEnum


# CASE TASKS

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
                            transObj.facility = loan
                            transObj.description = transaction['description']
                            transObj.type = transaction['type']
                            transObj.transactionDate = transaction['transactionDate']
                            transObj.effectiveDate = transaction['effectiveDate']
                            transObj.tranRef = transaction['tranRef']
                            transObj.debitAmount = transaction['debitAmount']
                            transObj.creditAmount = transaction['creditAmount']
                            transObj.balance = transaction['balance']

                            transObj.save()

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

            if (loan.totalLoanAmount - loan.approvedAmount) > 1:
                loan.amalReconciliation = False
            else:
                loan.amalReconciliation = True

            loan.save()

    write_applog("INFO", 'Servicing', 'Tasks-fundedData', 'Finishing AMAL Data Extract')

    return 'Task completed successfully'


@app.task(name="Servicing_Synch")
def sfSynch():
    '''Updates Facility with Salesforce Loan Object Information'''
    facilityStatus = {"Inactive": 0, "Active": 1, "Repaid": 2, "Suspended": 3}

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

                payload = {
                    'owner': caseObj.user,
                    'originalCaseUID': caseObj.caseUID,
                    'sfLoanName': caseObj.surname_1 + ", " + caseObj.street + ", " + caseObj.suburb + ", " + caseObj.enumStateType() + ", " + str(
                        caseObj.postcode),
                    'sfLoanID': loanDict['Loan.Name'],
                    'sfID': loanDict['Loan.Id'],
                    # 'sfAccountID': 'unknown',
                    # 'sfReferrerAccount' : 'unknown',
                    'amalID': loanDict['Loan.Mortgage_Number__c'],
                    'sfOriginatorID': caseObj.user.profile.salesforceID,  # Temporary
                    'status': facilityStatus[loanDict['Loan.Status__c']],
                    'totalPurposeAmount': loanDict['Loan.Total_Limits__c'],
                    'totalLoanAmount': loanDict['Loan.Total_Loan_Amount__c'],
                    'totalEstablishmentFee': loanDict['Loan.Total_Establishment_Fee__c'],
                    'establishmentFeeRate': loanDict['Loan.Establishment_Fee_Percent__c'] / 100,
                    # 'totalPlanPurposeAmount': loanObj.totalPlanAmount,
                    # 'totalPlanAmount': loanObj.totalPlanAmount,
                    # 'totalPlanEstablishmentFee': loanObj.planEstablishmentFee,
                    'bankAccountNumber': loanDict['Loan.Account_Number__c'],
                    'bsbNumber': loanDict['Loan.BSB__c'],
                    'meetingDate': caseObj.meetingDate,  # Temporary
                }

                if qsFacility.filter(sfID__exact=loanDict['Loan.Id']):
                    payload.pop('sfID')
                    qsFacility.filter(sfID__exact=loanDict['Loan.Id']).update(**payload)
                else:
                    facilityObj = Facility.objects.create(**payload)

    return 'Task completed successfully'


@app.task(name="Servicing_Detail_Synch")
def sfDetailSynch():
    '''Updates related Facility objects with Salesforce Loan Object Information'''

    roleTypes = {"Principal Borrower": 0,
                 "Secondary Borrower": 1,
                 "Borrower": 2,
                 "Nominated Occupant": 3,
                 "Permitted Cohabitant": 4,
                 "Power of Attorney": 5,
                 "Authorised 3rd Party": 6,
                 "Distribution Partner Contact": 7,
                 "Adviser": 8,
                 "Loan Originator": 9,
                 "Loan Writer": 10,
                 "Valuer": 11,
                 "Executor": 12}

    stateShortCode = {'Victoria': 'VIC', "New South Wales": 'NSW', "Queensland": 'QLD', "Tasmania": 'TAS',
                      "South Australia": 'SA', "Western Australia": 'WA', "Northern Territory": 'NT',
                      "Australian Capital Territory": 'ACT'}

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

                payload = {'facility': loan,
                           'sfContactID': contact['Id'],
                           'role': roleTypes[role['Role__c']],
                           #'isContact': False,  ####
                           #'isInformation:
                           #'isAuthorised
                           'lastName': contact['LastName'],
                           'firstName': contact['FirstName'],
                           'preferredName': None,  ####
                           'birthdate': contact['Birthdate__c'],
                           'mobile': contact['MobilePhone'],
                           'phone': contact['Phone'],
                           'email': contact['Email'],
                           'street': contact['MailingStreet'],
                           'suburb': contact['MailingCity'],
                           'postcode': contact['MailingPostalCode'],
                           'roleNotes': None
                           }

                if contact['Marital_Status__c']:
                    payload['maritalStatus']= maritalEnum[contact['Marital_Status__c'].upper()].value

                if contact['Salutation']:
                    payload['salutation'] = salutationEnum[contact['Salutation'].replace('.', '').upper()].value

                if contact['Gender__c']:
                    payload['gender']= clientSexEnum[contact['Gender__c'].upper()].value

                if contact['MailingStateCode']:
                    payload['state'] = stateTypesEnum[contact["MailingStateCode"]].value

                if qsFacilityRoles.filter(sfContactID__exact=contact['Id']):
                    payload.pop('sfContactID')
                    qsFacilityRoles.filter(sfContactID__exact=contact['Id']).update(**payload)
                else:
                    FacilityRoles.objects.create(**payload)


        # PROPERTIES

        propertyRefTable = sfPropertyLinks.query('Loan__c == "' + str(loan.sfID) + '"', inplace=False)

        for index, property in propertyRefTable.iterrows():
            propertyID = property['Property__c']

            propertyObjTable = sfProperties.query('Id =="' + str(propertyID) + '"', inplace=False)

            for index2, propertyObj in propertyObjTable.iterrows():

                payload = {'facility': loan,
                           'sfPropertyID': propertyObj['Id'],
                           'street': propertyObj['Street_Address__c'],
                           'suburb' : propertyObj['Suburb_City__c'],
                           'postcode': propertyObj['Postcode__c'],
                           'propertyType': propertyObj['Property_Type__c'],
                           'insuranceCompany': propertyObj['Insurer__c'],
                           'insurancePolicy': propertyObj['Policy_Number__c'],
                           'insuranceExpiryDate' :propertyObj['Insurance_Expiry_Date__c'],
                           'insuredAmount': propertyObj['Minimum_Insurance_Value__c']
                           }

                if propertyObj['State__c']:
                    stateCode = stateShortCode[propertyObj['State__c']]
                    payload['state'] = stateTypesEnum[stateCode].value

                if qsFacilityProperty.filter(sfPropertyID__exact=propertyObj['Id']):
                    payload.pop('sfPropertyID')
                    qsFacilityProperty.filter(sfPropertyID__exact=propertyObj['Id']).update(**payload)
                else:
                    FacilityProperty.objects.create(**payload)

                # Pretend separate valuation object in SF
                propertyRef = qsFacilityProperty.filter(sfPropertyID__exact=propertyObj['Id']).get()

                payload = {'property': propertyRef,
                           'valuationAmount': propertyObj['Home_Value_FullVal__c'],
                           'valuationDate': propertyObj['Last_Valuation_Date__c'],
                           'valuationType': 1, ###
                           'valuationCompany': propertyObj['Valuer__c'],
                           'valuerName':  propertyObj['Valuer_Name__c']
                           }

                if qsValuations.filter(property=propertyRef):
                    payload.pop('property')
                    qsValuations.filter(property=propertyRef).update(**payload)
                else:
                    FacilityPropertyVal.objects.create(**payload)


        # PURPOSES
        purposesTable = sfPurposes.query('Loan__c == "' + str(loan.sfID) + '"', inplace=False)

        for index, purpose in purposesTable.iterrows():

            payload = {'facility': loan,
                       'sfPurposeID': purpose['Id'],
                       'category': purpose['Category__c'],
                       'intention': purpose['Intention__c'],
                       'amount': __chkVal(purpose['Amount__c']),
                       'drawdownAmount': __chkVal(purpose['Drawdown_Amount__c']),
                       'drawdownFrequency': purpose['Drawdown_Frequency__c'],
                       'drawdownStartDate': None, ###
                       'drawdownEndDate': None, ###
                       'planAmount': __chkVal(purpose['Plan_Amount__c']),
                       'planPeriod': __chkVal(purpose['Plan_Period__c']),
                       'topUpBuffer': purpose['TopUp_Buffer__c'],
                       'description': purpose['Description__c'],
                       'notes': purpose['Notes__c'],
                       }

            print(type(purpose['Plan_Period__c']))
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


def __chkVal(arg):
    if arg == None:
        return None
    if math.isnan(arg):
        return None
    else:
        return arg