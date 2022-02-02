# Python Imports
import json
from datetime import timedelta
import os

# Django Imports
from django.utils import timezone

# Third-party Imports
from config.celery import app
from django_comments.models import Comment

# Local Application Imports
from apps.case.models import Case
from apps.case.tasks import createSFLeadCase

from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Logging import write_applog
from apps.lib.site_Enums import directTypesEnum
from apps.lib.site_Utilities import raiseTaskAdminError
from apps.lib.site_EmailUtils import sendTemplateEmail
from apps.lib.site_DataMapping import mapEnquiryToLead, mapEnquiryForSF 
from apps.operational.tasks import generic_file_uploader

from .models import Enquiry

from apps.operational.decorators import email_admins_on_failure


@app.task(name='Upload_Enquiry_Files')
def syncEnquiryFiles(enqUID):
    enquiry = Enquiry.objects.get(enqUID=enqUID)
    DOCUMENT_LIST = {
        "Automated Valuation": enquiry.valuationDocument,
        "Loan Summary": enquiry.summaryDocument,
    }
    # Retain file extensions
    DOCUMENT_LIST_MUTATED = {
        "{}{}".format(x, os.path.splitext(y.name)[1]):y 
        for x,y in DOCUMENT_LIST.items()
        if y
    }
    if enquiry.sfEnqID:
        return generic_file_uploader(DOCUMENT_LIST_MUTATED , enquiry.sfEnqID)
    return "Success - No sf Enquiry"


@app.task(name="Hard_delete_enquiries")
@email_admins_on_failure(task_name='Hard_delete_enquiries')
def hard_delete_enquiries():
    write_applog("INFO", 'Enquiry', 'Hard_delete_enquiries', "Starting")
    today = timezone.localtime()
    # hard delete any soft deleted leads from 2 months or prior
    two_months_ago = today - timedelta(days=60)  
    Enquiry.objects.filter(deleted_on__lte=two_months_ago).delete()
    write_applog("INFO", 'Enquiry', 'Hard_delete_enquiries', "Finished")

# TASKS

@app.task(name='Update_SF_Enquiry', bind=True)
def updateSFEnquiryTask(self, enqUID): 
    write_applog("INFO", 'Enquiry', "Task-" + str(self.request.id) + "-updateSFEnquiryTask", "Updating Enquiry for:" + str(enqUID))
    result = updateSFEnquiry(enqUID, taskID=self.request.id)
    if result['status'] == "Ok":
        result = syncNotes(enqUID)
        
    if result['status'] == "Ok":
        write_applog("INFO", 'Enquiry', "Task-" + str(self.request.id) + "-updateSFEnquiryTask", "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Enquiry', "Task-" + str(self.request.id) + "-updateSFEnquiryTask", "Finished - Unsuccessfully")
        return result['responseText']


def updateSFEnquiry(enqUID, sfAPIInstance=None, taskID=None):
    if sfAPIInstance:
        sfAPI = sfAPIInstance
    else:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True, taskID)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', "Task-" + str(taskID) + "-updateSFEnquiry", result['responseText'])
            return {"status": "ERROR", 'responseText': result['responseText']}
    try:
        enquiry = Enquiry.objects.get(enqUID=enqUID)
    except Enquiry.DoesNotExist:
        write_applog("ERROR", 'Enquiry', "Task-" + str(taskID) + "-updateSFEnquiry", 'Enquiry {} does not exist'.format(enqUID))
        return {"status": "ERROR", 'responseText': 'Enquiry {} does not exist'.format(enqUID)}
    if not enquiry.sfEnqID:
        result = createSFEnquiry(enqUID, sfAPI, taskID)
        # etc ..
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', "Task-" + str(taskID) + "-updateSFEnquiry", "No SF ID for: " + str(enqUID) + " - " +  result.get('responseText', ''))
            return {"status": "ERROR", 'responseText': "No SF ID for: " + str(enqUID) + " - " +  result.get('responseText', '')}
        return result

    payload = mapEnquiryForSF(enqUID)
    result = sfAPI.updateEnquiry(enquiry.sfEnqID, payload)
    if result['status'] == "Ok":
        app.send_task('Upload_Enquiry_Files', kwargs={'enqUID': enqUID})
        return {'status': 'Ok'}
    else:
        write_applog("ERROR", 'Enquiry', "Task-" + str(taskID) + "-updateSFEnquiry", json.dumps(result['responseText']))
        return {'status': 'Error', 'responseText': json.dumps(result['responseText'])}


def createSFEnquiry(enqUID, sfAPIInstance=None, taskID=None):
    if sfAPIInstance:
        sfAPI = sfAPIInstance
    else:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True, taskID)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', "Task-" + str(taskID) + "-createSFEnquiry", result['responseText'])
            return {"status": "ERROR", 'responseText': result['responseText']}

    try:
        enquiry = Enquiry.objects.get(enqUID=enqUID)
    except Enquiry.DoesNotExist:
        write_applog("ERROR", 'Enquiry', "Task-" + str(taskID) + "-createSFEnquiry", 'Enquiry {} does not exist'.format(enqUID))
        return {"status": "ERROR", 'responseText': 'Enquiry {} does not exist'.format(enqUID)}
    # get lead ID from case

    if enquiry.email:
        if (os.environ.get('ENV') == 'prod') and ('householdcapital.com' in enquiry.email):
            # Don't create LeadID
            write_applog("INFO", 'Enquiry', "Task-" + str(taskID) + "-createSFEnquiry", "Internal email re:" + str(enquiry.email))
            return {"status": "ERROR", 'responseText': 'Internal email re:' + str(enquiry.email)}

    lead_id = enquiry.case.sfLeadID
    if lead_id is not None:
        payload = mapEnquiryForSF(enqUID, True)
        payload['CreatedDate'] = enquiry.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        payload['Lead__c'] = lead_id
        result = sfAPI.createEnquiry(payload)
        if result['status'] == "Ok":
            enquiry.sfEnqID = result['data']['id']
            write_applog("INFO", 'Enquiry', "Task-" + str(taskID) + "-createSFEnquiry", "Created ID" + str(enquiry.sfEnqID))
            enquiry.save(update_fields=['sfEnqID'])
            app.send_task('Upload_Enquiry_Files', kwargs={'enqUID': enqUID})
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


@app.task(name="sfEnquiryLeadSync", bind=True)
def sfEnquiryLeadSync(self, enqUID):
    try:
        enquiry = Enquiry.objects.get(enqUID=enqUID)
    except Enquiry.DoesNotExist:
        write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', 'Enquiry {} does not exist'.format(enqUID))
        return {"status": "ERROR", 'responseText': 'Enquiry {} does not exist'.format(enqUID)}
    if not enquiry.case.sfLeadID:
        result = createSFLeadCase(str(enquiry.case.caseUID), taskID=self.request.id)
        if result['status'] != 'Ok':
            return {
                "status": "ERROR",
                'responseText': 'Failed to process enquiry: ' + str(enqUID)}
    return updateSFEnquiry(enqUID, taskID=self.request.id)


@app.task(name='SF_Create_Enquiry_Note')
def createNote(note_id):

    note = Comment.objects.get(pk=note_id)
    enquiry = note.content_object

    if not enquiry.sfEnqID:
        return {"status": "Error", "responseText": "SF Enquiry ID missing"}
    parent_sfid = enquiry.sfEnqID

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-createNote', result['responseText'])
        return {"status": "Error"}

    result = sfAPI.createNote(parent_sfid, note)

    return result


@app.task(name='SF_Delete_Enquiry_Note')
def deleteNote(note_id):
    note = Comment.objects.get(pk=note_id)
    if not note.sf_id:
        return {'status': 'Ok'}

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-deleteNote', result['responseText'])
        return {"status": "Error"}

    return sfAPI.deleteNote(note)


@app.task(name='SF_Sync_Enquiry_Notes')
def syncNotes(enqUID):
    enquiry = Enquiry.objects.queryset_byUID(enqUID).get()
    if not enquiry.sfEnqID:
        return {"status": "Error", "responseText": "SF Enquiry ID missing"}

    parent_sfid = enquiry.sfEnqID
    notes = Comment.objects.for_model(enquiry)

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-syncNotes', result['responseText'])
        return {"status": "Error"}

    return sfAPI.syncNotes(parent_sfid, notes)


######################################################################################
######################################################################################
######################################################################################

# FIX ME - MOVE TO LEAD TASKS
def __checkInt(val):
    if val:
        return int(val)
    else:
        return 0
