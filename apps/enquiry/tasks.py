# Python Imports
import json
from datetime import timedelta
import os

# Django Imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import timezone

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.case.models import Case
from apps.case.tasks import createSFLeadCase

from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Logging import write_applog
from apps.lib.site_Enums import directTypesEnum, marketingTypesEnum
from apps.lib.site_Utilities import sendTemplateEmail, raiseTaskAdminError
from apps.lib.site_DataMapping import mapEnquiryToLead, mapEnquiryForSF 

from .models import Enquiry
from urllib.parse import urljoin


# TASKS
@app.task(name="Create_SF_Lead")
def createSFLeadTask(enqUID):
    # Task to create(or retrieve) a SF Lead
    write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Creating lead for:" + str(enqUID))
    result = createSFLead(enqUID)
    if result['status'] == "Ok":
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Finished - Unsuccessfully")
        return result['responseText']


@app.task(name="Update_SF_Lead")
def updateSFLeadTask(enqUID):
    # deprecated
    write_applog("INFO", 'Enquiry', 'Tasks-updateSFLead', "Updating lead for:" + str(enqUID))
    result = updateSFLead(enqUID)
    if result['status'] == "Ok":
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFLead', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFLead', "Finished - Unsuccessfully")
        return result['responseText']

@app.task(name='Update_SF_Enquiry')
def updateSFEnquiryTask(enqUID): 
    write_applog("INFO", 'Enquiry', 'Tasks-updateSFEnquiryTask', "Updating Enquiry for:" + str(enqUID))
    result = updateSFEnquiry(enqUID)
    if result['status'] == "Ok":
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFEnquiryTask', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFEnquiryTask', "Finished - Unsuccessfully")
        return result['responseText']


@app.task(name="Catchall_SF_Lead")
def catchallSFLeadTask():
    write_applog("INFO", 'Enquiry', 'Tasks-catchallSFLead', "Starting")

    # Open SF API
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Enquiry', 'Tasks-createSFLead', result['responseText'])
        return result['responseText']

    qs = Enquiry.objects.filter(sfLeadID__isnull=True, closeDate__isnull=True).exclude(postcode__isnull=True)
    for enquiry in qs:
        createSFLead(str(enquiry.enqUID), sfAPI)
    write_applog("INFO", 'Enquiry', 'Tasks-catchallSFLead', "Completed")
    return "Finished - Successfully"


@app.task(name="EnquiryFollowUp")
def updateToday():
    write_applog("INFO", 'Enquiry', 'FollowUpEmail', "Starting")

    delta = timedelta(days=21)
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


@app.task(name="SF_Refer_Postcode")
def getReferPostcodeStatus():
    """Retrieve postcode status from SF"""
    write_applog("INFO", 'Enquiry', 'Tasks-getReferPostcodeStatus', "Starting")

    # Open SF API
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Enquiry', 'Tasks-createSFLead', result['responseText'])
        return result['responseText']

    qs = Enquiry.objects.filter(sfLeadID__isnull=False, isReferPostcode=True, referPostcodeStatus__isnull=True)
    for enquiry in qs:
        result = sfAPI.getLead(enquiry.sfLeadID)
        if result['status'] == 'Ok':
            status = result['data']['ReferPostCodeStatus__c']

            if status == 'Approved':
                enquiry.referPostcodeStatus = True
                enquiry.save()
                # update case also if exists
                updateCaseReferStatus(enquiry.sfLeadID, True)

            elif status == 'Rejected':
                enquiry.referPostcodeStatus = False
                enquiry.save()
                # update case also if exists
                updateCaseReferStatus(enquiry.sfLeadID, False)

    write_applog("INFO", 'Enquiry', 'SF_Refer_Postcode', "Completed")
    return "Finished - Successfully"


# UTILITIES

def updateCaseReferStatus(sfLeadID, status):
    """Update referPostcodeStatus on Case"""
    try:
        obj = Case.objects.filter(sfLeadID=sfLeadID).get()
        obj.referPostcodeStatus = status
        obj.save()
    except Case.DoesNotExist:
        pass
    return


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

    if not enqObj.user:
        write_applog("ERROR", 'Enquiry', 'Tasks-FollowUpEmail', "No associated user")
        return {"status": "ERROR", 'responseText': "No associated user"}

    bcc = enqObj.user.email
    subject, from_email, to = "Household Capital: Enquiry Follow-up", enqObj.user.email, enqObj.email

    sentEmail = sendTemplateEmail(template_name, email_context, subject, from_email, to, bcc=bcc)

    if sentEmail:
        enqObj.followUp = timezone.now()
        enqObj.save(update_fields=['followUp'])

        write_applog("INFO", 'Enquiry', 'Tasks-FollowUpEmail', "Follow-up Email Sent: " + enqObj.name)
        return {"status": "Ok", 'responseText': "Follow-up Email Sent"}
    else:
        write_applog("ERROR", 'Enquiry', 'Tasks-FollowUpEmail',
                     "Failed to email follow-up:" + enqUID)
        return {"status": "ERROR", 'responseText': "Failed to email follow-up:" + enqUID}


def createSFLead(enqUID, sfAPIInstance=None):
    # Open SF API
    if sfAPIInstance:
        sfAPI = sfAPIInstance
    else:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', 'Tasks-createSFLead', result['responseText'])
            return {"status": "ERROR", 'responseText': result['responseText']}

    # Get object
    qs = Enquiry.objects.queryset_byUID(enqUID)
    enquiry = qs.get()

    missing_data = []
    # Check for an email or phoneNumber as well as a user
    if not (enquiry.email or enquiry.phoneNumber):
        missing_data.append('No email or phone number')
    if not enquiry.user:
        missing_data.append('No user assigned')
    if not enquiry.postcode:
        missing_data.append('No postcode set')
    if missing_data:
        message = ', '.join(missing_data)
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', message)
        return {"status": "ERROR", "responseText": message}


    # Check for Household email address
    if enquiry.email:
        if (os.environ.get('ENV') == 'prod') and ('householdcapital.com' in enquiry.email):
            # Don't create LeadID
            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Internal email re:" + str(enquiry.email))
            return {"status": "ERROR", 'responseText': 'Internal email re:' + str(enquiry.email)}

    payload = mapEnquiryToLead(str(enquiry.enqUID))
    payload['CreatedDate'] = enquiry.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

    if enquiry.name:
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Attempting:" + str(enquiry.name))
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Attempting: Unknown')

    # Create SF Lead
    result = sfAPI.createLead(payload)

    if result['status'] == "Ok":
        enquiry.sfLeadID = result['data']['id']
        write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', "Created ID" + str(enquiry.sfLeadID))
        enquiry.save(update_fields=['sfLeadID'])
        return {"status": "Ok", "responseText": "Lead Created"}

    else:

        if isinstance(result['responseText'], dict):
            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', result['responseText']['message'])

            # Check for duplicates (as indicated by SF)
            if 'existing' in result['responseText']['message']:
                if enquiry.email:
                    # Search for email in Leads
                    result = sfAPI.qryToDict('LeadByEmail', enquiry.email, 'result')
                    if len(result['data']) != 0:
                        if __checkInt(result['data']['result.PostalCode']) == __checkInt(enquiry.postcode):
                            # match on postcode too
                            enquiry.sfLeadID = result['data']['result.Id']
                            enquiry.save(update_fields=['sfLeadID'])
                            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead',
                                         "Saved ID" + str(enquiry.sfLeadID))
                            return {"status": "Ok"}
                        else:
                            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Postcode mismatch')
                            return {"status": "ERROR", "responseText": "Postcode mismatch"}

                if enquiry.phoneNumber:
                    # Search for phone number in Leads
                    result = sfAPI.qryToDict('LeadByPhone', enquiry.phoneNumber, 'result')
                    if len(result['data']) != 0:
                        if __checkInt(result['data']['result.PostalCode']) == __checkInt(enquiry.postcode):
                            # match on postcode too
                            enquiry.sfLeadID = result['data']['result.Id']
                            enquiry.save(update_fields=['sfLeadID'])
                            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead',
                                         "Saved ID" + str(enquiry.sfLeadID))
                            return {"status": "Ok"}

                        else:
                            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Postcode mismatch')
                            return {"status": "ERROR", "responseText": "Postcode mismatch"}

                write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'No SF ID returned')
                return {"status": "ERROR", "responseText": "No SF ID returned"}

            else:
                write_applog("INFO", 'Case', 'Tasks-createSFLead', result['responseText']['message'])
                return {"status": "ERROR", "responseText": result['responseText']['message']}

        else:
            write_applog("INFO", 'Enquiry', 'Tasks-createSFLead', 'Unknown SF error')
            return {"status": "ERROR", "responseText": "Unknown SF error"}

def updateSFEnquiry(enqUID, sfAPIInstance=None):
    if sfAPIInstance: 
        sfAPI = sfAPIInstance
    else: 
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', result['responseText'])
            return {"status": "ERROR", 'responseText': result['responseText']}
    try: 
        enquiry = Enquiry.objects.get(enqUID=enqUID)
    except Enquiry.DoesNotExist: 
        write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', 'Enquiry {} does not exist'.format(enqUID))
        return {"status": "ERROR", 'responseText': 'Enquiry {} does not exist'.format(enqUID)}
    if not enquiry.sfEnqID: 
        result = createSFEnquiry(enqUID, sfAPI)
        # etc .. 
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', "No SF ID for: " + str(enqUID) + " - " +  result.get('responseText', ''))
            return {"status": "ERROR", 'responseText': "No SF ID for: " + str(enqUID) + " - " +  result.get('responseText', '')}
        return result

    payload = mapEnquiryForSF(enqUID)
    result = sfAPI.updateEnquiry(enquiry.sfEnqID, payload)
    if result['status'] == "Ok":
        return {'status': 'Ok'}
    else: 
        write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', json.dumps(result['responseText']))
        return {'status': 'Error', 'responseText': json.dumps(result['responseText'])}

def createSFEnquiry(enqUID, sfAPIInstance=None): 
    if sfAPIInstance: 
        sfAPI = sfAPIInstance
    else: 
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', 'Tasks-createSFEnquiry', result['responseText'])
            return {"status": "ERROR", 'responseText': result['responseText']}

    try: 
        enquiry = Enquiry.objects.get(enqUID=enqUID)
    except Enquiry.DoesNotExist: 
        write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', 'Enquiry {} does not exist'.format(enqUID))
        return {"status": "ERROR", 'responseText': 'Enquiry {} does not exist'.format(enqUID)}
    # get lead ID from case 

    missing_data = []
    # Check for an email or phoneNumber as well as a user
    if not (enquiry.email or enquiry.phoneNumber):
        missing_data.append('No email or phone number')
    if not enquiry.postcode:
        missing_data.append('No postcode set')
    if missing_data:
        message = ', '.join(missing_data)
        write_applog("INFO", 'Enquiry', 'Tasks-createSFEnquiry', message)
        return {"status": "ERROR", "responseText": message}

    if enquiry.email:
        if (os.environ.get('ENV') == 'prod') and ('householdcapital.com' in enquiry.email):
            # Don't create LeadID
            write_applog("INFO", 'Enquiry', 'Tasks-createSFEnquiry', "Internal email re:" + str(enquiry.email))
            return {"status": "ERROR", 'responseText': 'Internal email re:' + str(enquiry.email)}

    lead_id = enquiry.case.sfLeadID
    if lead_id is not None:
        payload = mapEnquiryForSF(enqUID)
        payload['CreatedDate'] = enquiry.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        payload['Lead__c'] = lead_id
        result = sfAPI.createEnquiry(payload)
        if result['status'] == "Ok":
            enquiry.sfEnqID = result['data']['id']
            write_applog("INFO", 'Enquiry', 'Tasks-createSFEnquiry', "Created ID" + str(enquiry.sfEnqID))
            enquiry.save(update_fields=['sfEnqID'])
            return {"status": "Ok", "responseText": "Enquiry Created"}
        else:
            return {
                'status': 'ERROR',
                'responseText': 'Enquiry Creation Failed: {}'.format(result['responseText'])
            }
    else: 
        # attempt syncing case ID. 
        return {
            'status': 'ERROR',
            'responseText': 'No sfLead attached to parent object.'
        }

@app.task(name="sfEnquiryLeadSync")
def sfEnquiryLeadSync(enqUID): 
    try: 
        enquiry = Enquiry.objects.get(enqUID=enqUID)
    except Enquiry.DoesNotExist: 
        write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', 'Enquiry {} does not exist'.format(enqUID))
        return {"status": "ERROR", 'responseText': 'Enquiry {} does not exist'.format(enqUID)}
    if not enquiry.case.sfLeadID:
        result = createSFLeadCase(str(enquiry.case.caseUID))
        if result['status'] != 'Ok':
            return {
                "status": "ERROR", 
                'responseText': 'Failed to process enquiry: ' + str(enqUID)}
    return updateSFEnquiry(enqUID)


def updateSFLead(enqUID, sfAPIInstance=None):
    # Open SF API
    if sfAPIInstance:
        sfAPI = sfAPIInstance
    else:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', 'Tasks-createSFLead', result['responseText'])
            return {"status": "ERROR", 'responseText': result['responseText']}

    # Get object
    qs = Enquiry.objects.queryset_byUID(enqUID)
    enquiry = qs.get()

    if not enquiry.sfLeadID:
        result = createSFLead(enqUID)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', 'Tasks-updateSFLead', "No SF ID for: " + str(enqUID))
            return {"status": "ERROR", 'responseText': "No SF ID for: " + str(enqUID)}
        else:
            # Update object
            qs = Enquiry.objects.queryset_byUID(enqUID)
            enquiry = qs.get()

    # Update SF Lead
    payload = mapEnquiryToLead(str(enquiry.enqUID))
    result = sfAPI.updateLead(str(enquiry.sfLeadID), payload)

    if result['status'] == "Ok":
        return {'status': 'Ok'}
    else:
        write_applog("ERROR", 'Enquiry', 'Tasks-updateSFLead', json.dumps(result['responseText']))
        # Check for closed object and raise error
        if enquiry.closeDate:
            raiseTaskAdminError("Lead synch error - close enquiry",
                                "Lead Synch - " + enquiry.name + "-" + json.dumps(result['responseText']))

        return {'status': 'Error', 'responseText': json.dumps(result['responseText'])}


def __checkInt(val):
    if val:
        return int(val)
    else:
        return 0


