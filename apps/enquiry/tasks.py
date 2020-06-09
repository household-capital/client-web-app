#Python Imports
from datetime import timedelta

# Django Imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import timezone

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Logging import write_applog
from .models import Enquiry
from apps.lib.site_Enums import directTypesEnum
from apps.lib.site_Utilities import sendTemplateEmail



# TASKS
@app.task(name="Create_SF_Lead")
def createSFLeadTask(enqUID):
    # Task to create(or retrieve) a SF Lead
    write_applog("Info", 'Enquiry', 'Tasks-createSFLead', "Creating lead for:" + str(enqUID))
    result = createSFLead(enqUID)
    if result['status'] == "Ok":
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Finished - Unsuccessfully")
        return result['responseText']


@app.task(name="Update_SF_Lead")
def updateSFLeadTask(enqUID):
    # Task to create(or retrieve) a SF Lead
    write_applog("Info", 'Enquiry', 'Tasks-updateSFLead', "Updating lead for:" + str(enqUID))
    result = updateSFLead(enqUID)
    if result['status'] == "Ok":
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFLead', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFLead', "Finished - Unsuccessfully")
        return result['responseText']


@app.task(name="Catchall_SF_Lead")
def catchallSFLeadTask():
    write_applog("INFO", 'Enquiry', 'Tasks-catchallSFLead', "Starting")

    # Open SF API
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("Error", 'Enquiry', 'Tasks-createSFLead', result['responseText'])
        return result['responseText']

    qs = Enquiry.objects.filter(sfLeadID__isnull=True, closeDate__isnull=True).exclude(postcode__isnull=True)
    for enquiry in qs:
        createSFLead(str(enquiry.enqUID),sfAPI)
    write_applog("INFO", 'Enquiry', 'Tasks-catchallSFLead', "Completed")
    return "Finished - Successfully"


@app.task(name="EnquiryFollowUp")
def updateToday():
    write_applog("INFO", 'Enquiry', 'FollowUpEmail', "Starting")

    delta = timedelta(days=7)
    windowDate = timezone.now() - delta

    qs = Enquiry.objects.filter(followUp__isnull=True,
                                email__isnull=False,
                                enquiryNotes__isnull=True,
                                referrer=directTypesEnum.WEB_CALCULATOR.value,
                                timestamp__lte=windowDate,
                                user__isnull=False,
                                actioned=0,
                                status=1,
                                closeDate__isnull=True).exclude(isCalendly=True)[:75]
    # should not be more then 75 in a day - ensure no time out

    for enquiry in qs:
        result = FollowUpEmail(str(enquiry.enqUID))
        if result['status'] == "Ok":
            write_applog("INFO", 'Enquiry', 'FollowUpEmail', "Sent -" + enquiry.name)
            updateSFLead(str(enquiry.enqUID))
        else:
            write_applog("ERROR", 'Enquiry', 'FollowUpEmail', "Failed -" + enquiry.name)

    write_applog("INFO", 'Enquiry', 'FollowUpEmail', "Finished")
    return "Finished - Successfully"


# UTILITIES

# Follow Up Email
def FollowUpEmail(enqUID):
    template_name = 'enquiry/email/email_followup.html'

    enqObj = Enquiry.objects.queryset_byUID(enqUID).get()

    # Build context
    email_context = {}

    #  Strip name
    if enqObj.name:
        if " " in enqObj.name:
            customerFirstName, surname = enqObj.name.split(" ", 1)
        else:
            customerFirstName = enqObj.name
        if len(customerFirstName) < 2:
            customerFirstName = None

    email_context['customerFirstName'] = customerFirstName

    email_context['obj'] = enqObj
    email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
    email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

    if not enqObj.user:
        write_applog("Error", 'Enquiry', 'Tasks-FollowUpEmail', "No associated user")
        return {"status": "Error", 'responseText': "No associated user"}

    bcc = enqObj.user.email
    subject, from_email, to = "Household Capital: Enquiry Follow-up", enqObj.user.email, enqObj.email

    sentEmail = sendTemplateEmail(template_name, email_context, subject, from_email, to, bcc=bcc )

    if sentEmail:
        enqObj.followUp = timezone.now()
        enqObj.save(update_fields=['followUp'])

        write_applog("Info", 'Enquiry', 'Tasks-FollowUpEmail', "Follow-up Email Sent: "+enqObj.name)
        return {"status": "Ok", 'responseText': "Follow-up Email Sent"}
    else:
        write_applog("ERROR", 'Enquiry', 'Tasks-FollowUpEmail',
                     "Failed to email follow-up:" + enqUID)
        return {"status": "ERROR", 'responseText': "Failed to email follow-up:" + enqUID}


SF_LEAD_MAPPING = {'phoneNumber': 'Phone',
                   'email': 'Email',
                   'age_1': 'Age_of_1st_Applicant__c',
                   'age_2': 'Age_of_2nd_Applicant__c',
                   'dwellingType': 'Dwelling_Type__c',
                   'valuation': 'Estimated_Home_Value__c',
                   'postcode': 'PostalCode',
                   'isTopUp': 'IsTopUp__c',
                   'isRefi': 'IsRefi__c',
                   'isLive': 'IsLive__c',
                   'isGive': 'IsGive__c',
                   'isCare': 'IsCare__c',
                   'calcTopUp': 'CalcTopUp__c',
                   'calcRefi': 'CalcRefi__c',
                   'calcLive': 'CalcLive__c',
                   'calcGive': 'CalcGive__c',
                   'calcCare': 'CalcCare__c',
                   'calcTotal': 'CalcTotal__c',
                   'enquiryNotes': 'External_Notes__c',
                   'payIntAmount': 'payIntAmount__c',
                   'payIntPeriod': 'payIntPeriod__c',
                   'status': 'HCC_Loan_Eligible__c',
                   'maxLoanAmount': 'Maximum_Loan__c',
                   'maxLVR': 'Maximum_LVR__c',
                   'errorText': 'Ineligibility_Reason__c',
                   'referrerID': 'Referrer_ID__c',
                   'doNotMarket':'DoNotMarket__c'
                   }


BooleanList = ['isTopUp', 'isRefi', 'isLive', 'isGive', 'isCare','doNotMarket']


def createSFLead(enqUID, sfAPIInstance=None):

    # Open SF API
    if sfAPIInstance:
        sfAPI=sfAPIInstance
    else:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("Error", 'Enquiry', 'Tasks-createSFLead', result['responseText'])
            return {"status": "Error", 'responseText':result['responseText']}

    # Get object
    qs = Enquiry.objects.queryset_byUID(enqUID)
    enquiry = qs.get()

    # Check for an email or phoneNumber as well as a user
    if (enquiry.email or enquiry.phoneNumber) and enquiry.user and enquiry.postcode:

        # Check for Household email address
        if enquiry.email:
            if 'householdcapital.com' in enquiry.email:
                # Don't create LeadID
                write_applog("Info", 'Enquiry', 'Tasks-createSFLead', "Internal email re:" + str(enquiry.email))
                return {"status": "Error", 'responseText':'Internal email re:' + str(enquiry.email)}

        payload = __buildLeadPayload(enquiry)

        if enquiry.name:
            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead',"Attempting:"+str(enquiry.name))
        else:
            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Attempting: Unknown')

        # Create SF Lead
        result = sfAPI.createLead(payload)

        if result['status'] == "Ok":
            enquiry.sfLeadID = result['data']['id']
            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Created ID" + str(enquiry.sfLeadID))
            enquiry.save(update_fields=['sfLeadID'])
            return {"status": "Ok", "responseText":"Lead Created"}

        else:

            if isinstance(result['responseText'], dict):
                write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', result['responseText']['message'])

                # Check for duplicates (as indicated by SF)
                if 'existing' in result['responseText']['message']:
                    if enquiry.email:
                        # Search for email in Leads
                        result = sfAPI.qryToDict('LeadByEmail', enquiry.email, 'result')
                        if len(result['data']) == 0:
                            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'No SF ID returned')
                            return {"status": "Error","responseText":"No SF ID returned"}
                        else:
                            if int(result['data']['result.PostalCode']) == int(enquiry.postcode):
                                # match on postcode too
                                enquiry.sfLeadID = result['data']['result.Id']
                                enquiry.save(update_fields=['sfLeadID'])
                                write_applog("INFO", 'Enquiry', 'Tasks-createSFLead',
                                             "Saved ID" + str(enquiry.sfLeadID))
                                return {"status": "Ok"}
                            else:
                                write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Postcode mismatch')
                                return {"status": "Error","responseText":"Postcode mismatch" }

                    elif enquiry.phoneNumber:
                        # Search for phone number in Leads
                        result = sfAPI.qryToDict('LeadByPhone', enquiry.phoneNumber, 'result')
                        if len(result['data']) == 0:
                            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'No SF ID returned')
                            return {"status": "Error","responseText":"No SF ID returned"}
                        else:
                            if __checkInt(result['data']['result.PostalCode']) == __checkInt(enquiry.postcode):
                                # match on postcode too
                                enquiry.sfLeadID = result['data']['result.Id']
                                enquiry.save(update_fields=['sfLeadID'])
                                write_applog("INFO", 'Enquiry', 'Tasks-createSFLead',
                                             "Saved ID" + str(enquiry.sfLeadID))
                                return {"status": "Ok"}

                            else:
                                write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Postcode mismatch')
                                return {"status": "Error","responseText":"Postcode mismatch" }
                else:
                    write_applog("INFO", 'Case', 'Tasks-createSFLead', result['responseText']['message'])
                    return {"status": "Error", "responseText": result['responseText']['message']}

            else:
                write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Unknown SF error')
                return {"status": "Error", "responseText":"Unknown SF error"}
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'No email or phone number')
        return {"status": "Error", "responseText":"No email or phone number"}


def updateSFLead(enqUID, sfAPIInstance=None):

    # Open SF API
    if sfAPIInstance:
        sfAPI = sfAPIInstance
    else:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("Error", 'Enquiry', 'Tasks-createSFLead', result['responseText'])
            return {"status": "Error", 'responseText': result['responseText']}

    # Get object
    qs = Enquiry.objects.queryset_byUID(enqUID)
    enquiry = qs.get()

    if not enquiry.sfLeadID:
        result = createSFLead(enqUID)
        if result['status'] != "Ok":
            write_applog("Error", 'Enquiry', 'Tasks-updateSFLead', "No SF ID for: " + str(enqUID))
            return {"status": "Error", 'responseText':"No SF ID for: " + str(enqUID)}
        else:
            # Update object
            qs = Enquiry.objects.queryset_byUID(enqUID)
            enquiry = qs.get()

    # Update SF Lead
    payload = __buildLeadPayload(enquiry)
    result = sfAPI.updateLead(str(enquiry.sfLeadID), payload)

    if result['status'] == "Ok":
        return {'status': 'Ok'}
    else:
        write_applog("Error", 'Enquiry', 'Tasks-updateSFLead', result['status'])
        return {'status': 'Error', 'responseText':result['status']}


def __buildLeadPayload(enquiry):
    # Build SF REST API payload
    payload = {}
    enquiryDict = enquiry.__dict__

    for app_field, sf_field in SF_LEAD_MAPPING.items():
        payload[sf_field] = enquiryDict[app_field]
        # Ensure Boolean fields are not null
        if app_field in BooleanList and not enquiryDict[app_field]:
            payload[sf_field] = False

    payload['CreatedDate'] = enquiry.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Ensure name fields populated
    if not enquiryDict['name']:
        payload['Lastname'] = 'Unknown'
    elif " " in enquiryDict['name']:
        payload['Firstname'], payload['Lastname'] = enquiryDict['name'].split(" ", 1)
    else:
        payload['Lastname'] = enquiryDict['name']

    payload['External_ID__c'] = str(enquiryDict['enqUID'])
    payload['OwnerID'] = enquiry.user.profile.salesforceID
    payload['Loan_Type__c'] = enquiry.enumLoanType()
    payload['Dwelling_Type__c'] = enquiry.enumDwellingType()
    payload['LeadSource'] = enquiry.enumReferrerType()

    # Map / create other fields
    if enquiry.referralUser:
        payload['Referral_UserID__c'] = enquiry.referralUser.last_name
    if enquiry.followUp:
        payload['Last_External_Followup_Date__c'] = enquiry.followUp.strftime("%Y-%m-%d")

    if enquiry.followUpDate:
        payload['Scheduled_Followup_Date_External__c'] = enquiry.followUpDate.strftime("%Y-%m-%d")
    payload['Scheduled_Followup_Notes__c'] = enquiry.followUpNotes

    if enquiry.closeDate:
        payload['Park_Lead__c'] = True
    else:
        payload['Park_Lead__c'] = False

    payload['Reason_for_Parking_Lead__c'] = enquiry.enumCloseReason()

    return payload

def __checkInt(val):
    if val:
        return int(val)
    else:
        return 0