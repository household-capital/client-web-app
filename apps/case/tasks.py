# Python Imports
import json
import base64

# Django Imports
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.api_AMAL import apiAMAL
from apps.lib.api_Docsaway import apiDocsAway
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.lixi.lixi_CloudBridge import CloudBridge
from apps.lib.site_Enums import caseStagesEnum, channelTypesEnum
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError, sendTemplateEmail
from apps.lib.site_DataMapping import mapCaseToOpportunity
from apps.lib.site_Globals import ECONOMIC
from apps.lib.hhc_LoanValidator import LoanValidator


from .models import Case, LossData, Loan, ModelSetting
from apps.application.models import ApplicationDocuments
from urllib.parse import urljoin

# CASE TASKS

@app.task(name="Create_SF_Case_Lead")
def createSFLeadCaseTask(caseUID):
    '''Task wrapper to create(or retrieve) a SF Lead'''
    write_applog("Info", 'Case', 'Tasks-createSFLead', "Creating lead for:" + str(caseUID))
    result = createSFLeadCase(caseUID)
    if result['status'] == "Ok":
        write_applog("INFO", 'Case', 'Tasks-createSFLead', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Case', 'Tasks-createSFLead', "Finished - Unsuccessfully")
        return "Finished - Unsuccessfully"


@app.task(name="Update_SF_Case_Lead")
def updateSFLeadTask(caseUID):
    # Task wrapper to update a SF Lead
    write_applog("INFO", 'Case', 'Tasks-updateSFLead', "Updating lead for:" + str(caseUID))
    result = updateSFLead(caseUID)
    if result['status'] == "Ok":
        write_applog("INFO", 'Case', 'Tasks-updateSFLead', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Case', 'Tasks-updateSFLead', "Finished - Unsuccessfully")
        return "Finished - Unsuccessfully"


@app.task(name="Catchall_SF_Case_Lead")
def catchallSFLeadTask():
    '''Task wrapper to to create lead for all cases without sfLeadID '''
    write_applog("INFO", 'Case', 'Tasks-catchallSFLead', "Starting")

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-createSFLead', result['responseText'])
        return "Error - could not open Salesforce"

    qs = Case.objects.filter(sfLeadID__isnull=True, lossdata__closeDate__isnull=True)
    for case in qs:
        createSFLeadCase(str(case.caseUID), sfAPI)
    write_applog("INFO", 'Case', 'Tasks-catchallSFLead', "Completed")
    return "Finished - Unsuccessfully"


@app.task(name='SF_Lead_Convert')
def sfLeadConvert(caseUID):
    '''Task wrapper to to create lead for all cases without sfLeadID '''

    # Get object
    qs = Case.objects.queryset_byUID(caseUID)
    case = qs.get()
    description = case.caseDescription

    write_applog("INFO", 'Case', 'Tasks-SF_Lead_Convert', "Starting")

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-SF_Lead_Convert', result['responseText'])
        raiseTaskAdminError('Tasks-SF_Lead_Convert', "Error - could not open Salesforce :" + result['responseText'])
        return "Error - could not open Salesforce"

    result = convertSFLead(caseUID, sfAPI)

    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-SF_Lead_Convert', result['responseText'])
        raiseTaskAdminError('Tasks-SF_Lead_Convert',
                            "Error - could not convert lead :" + description + "-" + result['responseText'])
        return "Error - " + description + "-" + result['responseText']
    else:
        write_applog("INFO", 'Case', 'Tasks-SF_Lead_Convert', description + "-" + "Lead Converted")
        sfOppSynch(caseUID)
        sfDocSynch(caseUID)
        return "Lead converted and synchd!"


@app.task(name='SF_Opp_Synch')
def sfOppSynch(caseUID):
    '''Task wrapper to to create lead for all cases without sfLeadID '''

    # Get object
    qs = Case.objects.queryset_byUID(caseUID)
    case = qs.get()
    description = case.caseDescription

    write_applog("INFO", 'Case', 'Tasks-SF_Opp_Synch', "Starting")

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-SF_Opp_Synch', result['responseText'])
        raiseTaskAdminError('Tasks-SF_Opp_Synch', "Error - could not open Salesforce :" + result['responseText'])
        return "Error - could not open Salesforce"

    result = updateSFOpp(caseUID, sfAPI)

    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-SF_Opp_Synch', description + "-" + result['responseText'])
        raiseTaskAdminError('Tasks-SF_Opp_Synch',
                            "Error - could not synch Opp :" + description + "-" + result['responseText'])
        return "Error - " + result['responseText']
    else:
        write_applog("INFO", 'Case', 'Tasks-SF_Opp_Synch', description + "-" + "Opp Synched!")
        return "Success - Opp Synched!"


@app.task(name='SF_Doc_Synch')
def sfDocSynch(caseUID):
    '''Task wrapper to synch case documents '''

    # Get object
    qs = Case.objects.queryset_byUID(caseUID)
    case = qs.get()
    description = case.caseDescription

    write_applog("INFO", 'Case', 'Tasks-SF_Doc_Synch', "Starting")

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-SF_Doc_Synch', result['responseText'])
        raiseTaskAdminError('Tasks-SF_Doc_Synch', "Error - could not open Salesforce :" + result['responseText'])
        return "Error - could not open Salesforce"

    result = updateSFDocs(caseUID, sfAPI)

    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-SF_Doc_Synch', description + "-" + result['responseText'])
        raiseTaskAdminError('Tasks-SF_Doc_Synch',
                            "Error - could not synch Opp :" + description + "-" + result['responseText'])
        return "Error - " + result['responseText']
    else:
        write_applog("INFO", 'Case', 'Tasks-SF_Doc_Synch', description + "-" + "Docs Synched!")
        return "Success - Docs Synched!"


@app.task(name='AMAL_Send_Docs')
def amalDocs(caseUID):
    '''Task to send documents to AMAL using submission identifier '''
    # Get object
    qs = Case.objects.queryset_byUID(caseUID)
    caseObj = qs.get()

    CB = CloudBridge(caseObj.sfOpportunityID, False, True, True)

    result = CB.openAPIs()
    if result['status'] == "Error":
        return "Error - " + caseObj.caseDescription + "-" + result['responseText']

    if not caseObj.amalIdentifier:
        return "Error - " + caseObj.caseDescription + "- no AMAL application ID"

    result = CB.sendDocumentsToAMAL(caseObj.amalIdentifier)
    if result['status'] == "Error":
        return "Error - " + caseObj.caseDescription + "- " + result['responseText']
    else:
        return "Success - Documents sent to AMAL"


@app.task(name='SF_Stage_Synch')
def stageSynch():
    '''Reverse synch SF -> clientApp'''

    stageMapping = {
        "Meeting Held": caseStagesEnum.MEETING_HELD.value,
        "Application Sent": caseStagesEnum.APPLICATION.value,
        "Approval": caseStagesEnum.APPLICATION.value,
        "Assess": caseStagesEnum.APPLICATION.value,
        "Build Case": caseStagesEnum.APPLICATION.value,
        "Certification": caseStagesEnum.DOCUMENTATION.value,
        "Documentation": caseStagesEnum.DOCUMENTATION.value,
        "Settlement": caseStagesEnum.DOCUMENTATION.value,
        "Settlement Booked": caseStagesEnum.DOCUMENTATION.value,
        "Pre-Settlement": caseStagesEnum.DOCUMENTATION.value,
        "Post-Settlement Review": caseStagesEnum.FUNDED.value,
        "Loan Approved": caseStagesEnum.FUNDED.value,
        "Parked": caseStagesEnum.CLOSED.value,
        "Loan Application Withdrawn": caseStagesEnum.CLOSED.value,
        "Loan Declined": caseStagesEnum.CLOSED.value,
    }

    # Get stage list from SF
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    output = sfAPI.getStageList()

    if output['status'] == "Ok":
        dataFrame = output['data']

        # Loop through SF list and update stage of CaseObjects
        for index, row in dataFrame.iterrows():
            try:
                obj = Case.objects.filter(sfOpportunityID=row['Id']).get()
            except Case.DoesNotExist:
                obj = None

            if obj:
                if obj.caseStage != caseStagesEnum.FUNDED.value and row['StageName'] in stageMapping:
                    obj.caseStage = stageMapping[row['StageName']]
                    obj.save(update_fields=['caseStage'])
    write_applog("INFO", 'stageSynch', 'task', "SF Stages Synched")

    return "Success - SF Stages Synched"


@app.task(name='SF_Integrity_Check')
def integrityCheck():
    '''Compare Amounts between Salesforce and ClientApp'''

    # Get stage list from SF
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    output = sfAPI.getAmountCheckList()

    if output['status'] == "Ok":
        dataFrame = output['data']

        # Loop through SF list and update stage of CaseObjects
        for index, row in dataFrame.iterrows():
            try:
                obj = Case.objects.filter(sfOpportunityID=row['Id']).get()
                loanObj = Loan.objects.filter(case__sfOpportunityID=row['Id']).get()
                modelObj = ModelSetting.objects.filter(case__sfOpportunityID=row['Id']).get()
            except obj.DoesNotExist:
                obj = None

            if obj:
                errorFlag = False

                if abs(loanObj.totalLoanAmount - row['Total_Household_Loan_Amount__c']) > 1:
                    errorFlag = True

                if abs(loanObj.totalPlanAmount - row['Total_Plan_Amount__c']) > 1:
                    errorFlag = True

                if modelObj.establishmentFeeRate:
                    if abs(modelObj.establishmentFeeRate - row['Establishment_Fee_Percent__c'] / 100) > 0.0001:
                        errorFlag = True

                if errorFlag == True:
                    write_applog("INFO", 'integrityCheck', 'task', "Difference on " + obj.caseDescription)
                    email_template = 'case/email/clientAppEmails/email.html'
                    email_context = {"obj": obj,
                                     "loanObj": loanObj,
                                     'establishmentFeeRate': modelObj.establishmentFeeRate * 100,
                                     'Total_Household_Loan_Amount__c': row['Total_Household_Loan_Amount__c'],
                                     'Total_Plan_Amount__c': row['Total_Plan_Amount__c'],
                                     'Establishment_Fee_Percent__c': row['Establishment_Fee_Percent__c']
                                     }
                    email_context['absolute_url'] = urljoin(settings.SITE_URL, settings.STATIC_URL) 

                    subject, from_email, to = "Salesforce - ClientApp Integrity Check", \
                                                  'noreply@householdcapital.app', \
                                                  [obj.owner.email]

                    emailSent = sendTemplateEmail(email_template, email_context, subject, from_email, to)

    return "Success - Integrity Check Complete"


@app.task(name='SF_Limit_Check')
def limitCheck():
    '''Check limits on SF Opportunities'''

    # Get stage list from SF
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    output = sfAPI.getAmountCheckList()

    if output['status'] == "Ok":
        dataFrame = output['data']

        # Loop through SF list and update stage of CaseObjects
        for index, row in dataFrame.iterrows():

            srcDict = sfAPI.getOpportunityExtract(row['Id'])
            srcDict.update(ECONOMIC)

            loanObj = LoanValidator(srcDict)
            loanStatus = loanObj.getStatus()['data']
            print(loanStatus)

    return "Success - Limit Check Complete"


@app.task(name='SF_Create_Variation')
def sfCreateVariation(newCaseUID, orgCaseUID):
    end_point = 'CreateLoanVariation/v1/'
    end_point_method = 'POST'

    orgSfOpportunityID = Case.objects.queryset_byUID(orgCaseUID).get().sfOpportunityID

    payload = {"opportunityId": orgSfOpportunityID}

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)

    result = sfAPI.apexCall(end_point, end_point_method, data=payload)

    if result['status'] != 'Ok':
        write_applog("ERROR", 'Case', 'task-sfCreateVariation',
                     'Could not create variation - ' + json.dumps(result['responseText']))
        return "Variation could not be created"

    else:
        newCaseObj = Case.objects.queryset_byUID(newCaseUID).get()

        # Save response data
        newCaseObj.sfOpportunityID = result['responseText']['opportunityid']
        newCaseObj.sfLoanID = result['responseText']['loanNumber']
        newCaseObj.save()

        write_applog("INFO", 'Case', 'task-sfCreateVariation',
                     'New variation created - ' + str(result['responseText']['loanNumber']))

        return "Variation successfully created!"


@app.task(name='Email_Loan_Summary')
def emailLoanSummary(caseUID, template_name):

    email_context = {}
    caseObj = Case.objects.queryset_byUID(caseUID).get()

    email_context['obj'] = caseObj
    email_context['absolute_url'] = urljoin(settings.SITE_URL, settings.STATIC_URL)
    email_context['absolute_media_url'] = settings.MEDIA_URL

    attachFilename = "HouseholdLoanSummary.pdf"
    bcc = caseObj.owner.email

    subject, from_email, to = "Household Loan Summary Report", caseObj.owner.email, caseObj.email
    text_content = "Text Message"

    attachments = [(attachFilename, caseObj.summaryDocument.name)]

    result = sendTemplateEmail(template_name, email_context, subject, from_email, to,
                               cc=None, bcc=bcc, attachments=attachments)

    if result:
        caseObj.summarySentDate = timezone.now()
        caseObj.save(update_fields=['summarySentDate'])
        write_applog("INFO", 'Case-Task', 'emailLoanSummary',
                     "Loan summary emailed:" + caseUID)
        return "Task Completed Successfully"

    else:
        write_applog("ERROR", 'Case-Task', 'emailLoanSummary',
                     "Failed to email Loan Summary Report:" + caseUID)
        raiseTaskAdminError("Email Loan Summary Failed", "Failed to email Loan Summary Report " + caseObj.caseDescription)
        return "Task Failed)"


@app.task(name='Mail_Loan_Summary')
def mailLoanSummary(caseUID):

    caseObj = Case.objects.queryset_byUID(caseUID).get()

    docs = apiDocsAway()

    result = docs.sendPdfByMail(caseObj.summaryDocument.name,
                                caseObj.enumSalutation()[0] + " " + caseObj.firstname_1 + " " + caseObj.surname_1,
                                caseObj.street,
                                caseObj.suburb,
                                caseObj.state,
                                caseObj.postcode
                                )

    if result['status'] != "Ok":
        write_applog("ERROR", 'Case-Tasks', 'mailLoanSummary',
                     "Failed to mail Loan Summary Report:" + caseUID + " - " + result['responseText'])
        raiseTaskAdminError("Failed to mail Loan Summary Report",
                            "Failed to mail Loan Summary Report:" + caseObj.surname_1 + " - " + result['responseText'] )
    else:
        resultDict = json.loads(result['data'])

        # Check for other send errors
        if resultDict["APIErrorNumber"] != 0 or resultDict["transaction"]["approved"] != 'y':
            write_applog("ERROR", 'Case-Tasks', 'mailLoanSummary',
                         "Failed to mail Loan Summary Report:" + caseObj.surname_1 + " | "+ caseUID)
            raiseTaskAdminError("Failed to mail Loan Summary Report",
                                "Failed to mail Loan Summary Report:" + caseObj.surname_1)
        else:
            # Record the send reference
            caseObj.summarySentRef = resultDict["transaction"]["reference"]
            caseObj.save(update_fields=['summarySentRef'])

            write_applog("INFO", 'Case-Tasks', 'mailLoanSummary',
                         "Mailed Loan Summary Report:" + caseUID + " - " + result['data'])


# UTILITIES

SF_LEAD_CASE_MAPPING = {'phoneNumber': 'Phone',
                        'email': 'Email',
                        'age_1': 'Age_of_1st_Applicant__c',
                        'age_2': 'Age_of_2nd_Applicant__c',
                        'dwellingType': 'Dwelling_Type__c',
                        'valuation': 'Estimated_Home_Value__c',
                        'postcode': 'PostalCode',
                        'caseNotes': 'External_Notes__c',
                        'firstname_1': 'Firstname',
                        'surname_1': 'Lastname',
                        'isZoomMeeting': 'isZoom__c'
                        }


def createSFLeadCase(caseUID, sfAPIInstance=None):
    '''Creates a SF Lead from a case using the SF Rest API.
    If a duplicate exists - the function retrieves the SF Lead ID using a SOQL query on email or phone'''

    # Get object
    qs = Case.objects.queryset_byUID(caseUID)
    case = qs.get()
    if case.sfLeadID:
        return {"status": "Error", "responseText": "SF Lead ID already exists"}

    # Open SF API
    if sfAPIInstance:
        sfAPI = sfAPIInstance
    else:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Case', 'Tasks-createSFLead', result['responseText'])
            return {"status": "Error"}

    # Check for an email or phoneNumber as well as a user
    if (case.email or case.phoneNumber) and case.owner:
        # Check for Household email address
        if case.email:
            if 'householdcapital.com' in case.email:
                # Don't create LeadID
                write_applog("INFO", 'Case', 'Tasks-createSFLead', "Internal email re:" + str(case.email))
                return {"status": "Error", "responseText": "HouseholdCapital email address"}

        payload = __buildLeadCasePayload(case)
        payload['CreatedDate'] = case.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

        if case.surname_1:
            write_applog("INFO", 'Case', 'Tasks-createSFLead', case.surname_1)
        else:
            write_applog("INFO", 'Case', 'Tasks-createSFLead', 'unknown')

        # Create SF Lead
        result = sfAPI.createLead(payload)

        write_applog("INFO", 'Case', 'Tasks-createSFLead', result['status'])

        if result['status'] == "Ok":
            case.sfLeadID = result['data']['id']
            write_applog("INFO", 'Case', 'Tasks-createSFLead', "Created ID" + str(case.sfLeadID))
            case.save(update_fields=['sfLeadID'])
            return {"status": "Ok"}

        else:

            if isinstance(result['responseText'], dict):
                write_applog("INFO", 'Case', 'Tasks-createSFLead', result['responseText']['message'])

                # Check for duplicates (as indicated by SF) and attempt to retrieve ID using SOQL
                if 'existing' in result['responseText']['message']:
                    if case.email:
                        # Search for email in Leads
                        result = sfAPI.qryToDict('LeadByEmail', case.email, 'result')
                        if len(result['data']) == 0:
                            write_applog("INFO", 'Case', 'Tasks-createSFLead', 'No SF ID returned')
                            return {"status": "Error", "responseText": "No SF ID returned"}
                        else:
                            if int(result['data']['result.PostalCode']) == int(case.postcode):
                                # match on postcode too
                                case.sfLeadID = result['data']['result.Id']
                                case.save(update_fields=['sfLeadID'])
                                write_applog("INFO", 'Case', 'Tasks-createSFLead',
                                             "Saved ID" + str(case.sfLeadID))
                                return {"status": "Ok"}
                            else:
                                write_applog("INFO", 'Case', 'Tasks-createSFLead', 'Postcode mismatch')
                                return {"status": "Error", "responseText": "Postcode mismatch"}

                    elif case.phoneNumber:
                        # Search for phone number in Leads
                        result = sfAPI.qryToDict('LeadByPhone', case.phoneNumber, 'result')
                        if len(result['data']) == 0:
                            write_applog("INFO", 'Case', 'Tasks-createSFLead', 'No SF ID returned')
                            return {"status": "Error", "responseText": "No SF ID returned"}
                        else:
                            if __checkInt(result['data']['result.PostalCode']) == __checkInt(case.postcode):
                                # match on postcode too
                                case.sfLeadID = result['data']['result.Id']
                                case.save(update_fields=['sfLeadID'])
                                write_applog("INFO", 'Case', 'Tasks-createSFLead',
                                             "Saved ID" + str(case.sfLeadID))
                                return {"status": "Ok"}

                            else:
                                write_applog("INFO", 'Case', 'Tasks-createSFLead', 'Postcode mismatch')
                                return {"status": "Error", "responseText": "Postcode mismatch"}
                else:
                    write_applog("INFO", 'Case', 'Tasks-createSFLead', result['responseText']['message'])
                    return {"status": "Error", "responseText": result['responseText']['message']}

            else:
                write_applog("INFO", 'Case', 'Tasks-createSFLead', 'Unknown SF error')
                return {"status": "Error", "responseText": "Unknown SF error"}

    else:
        write_applog("INFO", 'Case', 'Tasks-createSFLead', 'No email or phone number')
        return {"status": "Error", "responseText": "No email or phone number"}


def updateSFLead(caseUID):
    '''Updates a SF Lead from a case using the SF Rest API.'''

    # Open SF API
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-updateSFLead', result['responseText'])
        return {"status": "Error"}

    # Get object
    qs = Case.objects.queryset_byUID(caseUID)
    caseObj = qs.get()

    if not caseObj.sfLeadID:
        result = createSFLeadCase(caseUID)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Case', 'Tasks-updateSFLead', "No SF ID for: " + str(caseUID))
            return {"status": "Error"}
        else:
            # Update object
            qs = Case.objects.queryset_byUID(caseUID)
            caseObj = qs.get()

    # Update SF Lead
    payload = __buildLeadCasePayload(caseObj)
    result = sfAPI.updateLead(str(caseObj.sfLeadID), payload)

    if result['status'] == "Ok":
        return {'status': 'Ok'}
    else:
        write_applog("ERROR", 'Case', 'Tasks-updateSFLead', result['status'])
        return {'status': 'Error'}


def __buildLeadCasePayload(case):
    '''Build SF REST API payload using Case field mapping'''

    payload = {}
    caseDict = case.__dict__

    for app_field, sf_field in SF_LEAD_CASE_MAPPING.items():
        payload[sf_field] = caseDict[app_field]

    # Ensure name fields populated

    if not payload['Lastname']:
        payload['Lastname'] = "Unknown"

    payload['External_ID__c'] = str(caseDict['caseUID'])
    payload['OwnerID'] = case.owner.profile.salesforceID
    payload['Loan_Type__c'] = case.enumLoanType()
    payload['Dwelling_Type__c'] = case.enumDwellingType()
    payload['Date_Case_Created__c'] = case.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Map / create other fields
    if case.lossdata.followUpDate:
        payload['Scheduled_Followup_Date_External__c'] = case.lossdata.followUpDate.strftime("%Y-%m-%d")
    payload['Scheduled_Followup_Notes__c'] = case.lossdata.followUpNotes

    if case.lossdata.closeDate:
        payload['Park_Lead__c'] = True
    else:
        payload['Park_Lead__c'] = False

    payload['Reason_for_Parking_Lead__c'] = case.lossdata.enumCloseReason()

    if case.lossdata.doNotMarket:
        payload['DoNotMarket__c'] = True

    payload['Sales_Channel__c'] = case.enumChannelType()

    return payload


def __checkInt(val):
    if val:
        return int(val)
    else:
        return 0


def convertSFLead(caseUID, sfAPI):
    '''convert lead using APEX end-point'''

    end_point = 'leadconvert/v1/'
    end_point_method = 'POST'

    caseObj = Case.objects.queryset_byUID(caseUID).get()

    if not caseObj.sfLeadID:

        write_applog("ERROR", 'Case', 'convertSFLead', 'Case has no SF LeadID')
        return {'status': 'Error', 'responseText': 'Case has no SF LeadID'}

    # Convert Lead [Post Meeting]
    if not caseObj.sfOpportunityID:

        payload = {"leadId": caseObj.sfLeadID,
                   "ownerId": caseObj.owner.profile.salesforceID}

        result = sfAPI.apexCall(end_point, end_point_method, data=payload)

        if result['status'] != 'Ok':
            write_applog("ERROR", 'Case', 'convertSFLead', 'Lead conversion error - ' + result['responseText'])
            return {'status': 'Error', 'responseText': result['responseText']}

        # Save response data
        caseObj.sfOpportunityID = result['responseText']['opportunityId']
        caseObj.sfLoanID = result['responseText']['loanNumber']
        caseObj.save(update_fields=['sfOpportunityID', 'sfLoanID'])

    return {'status': 'Ok', 'responseText': caseObj.sfOpportunityID}


def updateSFOpp(caseUID, sfAPI):
    end_point = 'caseopptysync/v1/'
    end_point_method = 'POST'

    caseObj = Case.objects.queryset_byUID(caseUID).get()
    lossObj = LossData.objects.queryset_byUID(caseUID).get()

    # Update Opportunity [Application]

    payload = mapCaseToOpportunity(caseObj, lossObj)

    # Call endpoint
    result = sfAPI.apexCall(end_point, end_point_method, data=payload)
    if result['status'] != 'Ok':
        write_applog("ERROR", 'Case', 'updateSFOpp', "Opportunity Synch -" + json.dumps(result['responseText']))
        return {'status': 'Error', 'responseText': caseObj.caseDescription + " - " + json.dumps(result['responseText'])}

    return {'status': 'Ok', "responseText": "Salesforce Synch!"}


def updateSFDocs(caseUID, sfAPI):
    doc_end_point = 'docuploader/v1/'
    doc_end_point_method = 'POST'

    caseObj = Case.objects.queryset_byUID(caseUID).get()

    DOCUMENT_LIST = {"Automated Valuation": caseObj.valuationDocument,
                     "Responsible Lending Summary": caseObj.responsibleDocument,
                     "Enquiry Document": caseObj.enquiryDocument,
                     "Loan Summary": caseObj.summaryDocument,
                     "Application Received": caseObj.applicationDocument,
                     }

    for docName, docObj in DOCUMENT_LIST.items():
        if docObj:
            try:
                with default_storage.open(docObj.name, "rb") as f:
                    body = base64.b64encode(f.read()).decode('ascii')

                data = {
                    'opptyId': caseObj.sfOpportunityID,
                    'documentTitle': docName,
                    'base64BinaryStream': body,
                    'extension': 'pdf'}

                result = sfAPI.apexCall(doc_end_point, doc_end_point_method, data=data)

                if result['status'] != 'Ok':
                    write_applog("ERROR", 'Case', 'updateSFdocs',
                                 "Document Synch - " + docName + "-" + json.dumps(result['responseText']))
                    raiseTaskAdminError("Document synch error",
                                        "Document Synch - " + docName + "-" + json.dumps(result['responseText']))

            except FileNotFoundError:
                write_applog("ERROR", 'Case', 'updateSFdocs',
                             "Document Synch - " + docName + "- file does not exist")


    # Check for online Application Documents
    if caseObj.appUID:
        qs = ApplicationDocuments.objects.filter(application__appUID=caseObj.appUID)
        for doc in qs:
            with default_storage.open(doc.document.name, "rb") as f:
                body = base64.b64encode(f.read()).decode('ascii')

            docType, ext = doc.mimeType.split("/",1)

            data = {
                'opptyId': caseObj.sfOpportunityID,
                'documentTitle': doc.enumDocumentType,
                'base64BinaryStream': body,
                'extension': ext}

            result = sfAPI.apexCall(doc_end_point, doc_end_point_method, data=data)
            if result['status'] != 'Ok':
                write_applog("ERROR", 'Case', 'updateSFdocs',
                             "Document Synch - " + doc.enumDocumentType + "-" + json.dumps(result['responseText']))
                raiseTaskAdminError("Document synch error", "Document Synch - " + doc.enumDocumentType + "-" + json.dumps(result['responseText']))

    return {'status': 'Ok', "responseText": "Salesforce Doc Synch!"}


