
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.lixi.lixi_CloudBridge import CloudBridge
from apps.lib.site_Enums import caseStagesEnum, channelTypesEnum, directTypesEnum
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError
from apps.lib.site_DataMapping import mapCaseToOpportunity, sfStateEnum
from apps.lib.site_Globals import ECONOMIC
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.operational.tasks import generic_file_uploader

from apps.case.tasks import __buildLeadCasePayload
from apps.case.models import Case
from apps.enquiry.models import Enquiry
from apps.lib.site_DataMapping import mapEnquiryToLead, mapEnquiryForSF 
from django_comments.models import Comment

import os 
import json

from apps.lib.site_Utilities import raiseTaskAdminError

def generic_file_uploader(doc_list, record_id, sfAPI=None): 
    """
        doc_list = {
            "Doc Title" : FileField
        }
    """
    from datetime import timedelta
    from django.utils import timezone as djtimezone
    from django.core.files.storage import default_storage
    if sfAPI is None: 
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'operational', 'Tasks-Generic File-upload', result['responseText'])
            return "Error - could not open Salesforce"
    for file_name, file_obj in doc_list.items():
        write_applog("INFO", 'operational', 'Tasks-Generic File-upload', 'Attempting to sync {} on {}'.format(file_name, record_id))
        try:
            with default_storage.open(file_obj.name, "rb") as f:
                body = f.read()
            result = sfAPI.genericUploader(record_id, body, file_name)
            if result['status'] != 'Ok':
                write_applog("ERROR", 'operational', 'Tasks-Generic File-upload', result['responseText'])
                return "Error - Failed to upload docs"
        except FileNotFoundError:
            write_applog("ERROR", 'operational', 'Tasks-Generic File-upload', "Document Synch - " + file_name + "- file does not exist")
    return "Success"



def syncEnquiryFiles(enqUID, sfAPI):
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
        return generic_file_uploader(DOCUMENT_LIST_MUTATED , enquiry.sfEnqID, sfAPI)
    return "Success - No sf Enquiry"


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

    if enquiry.email:
        if (os.environ.get('ENV') == 'prod') and ('householdcapital.com' in enquiry.email):
            # Don't create LeadID
            write_applog("INFO", 'Enquiry', 'Tasks-createSFEnquiry', "Internal email re:" + str(enquiry.email))
            return {"status": "ERROR", 'responseText': 'Internal email re:' + str(enquiry.email)}

    lead_id = enquiry.case.sfLeadID
    if lead_id is not None:
        payload = mapEnquiryForSF(enqUID, True)
        payload['CreatedDate'] = enquiry.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        payload['Lead__c'] = lead_id
        result = sfAPI.createEnquiry(payload)
        if result['status'] == "Ok":
            enquiry.sfEnqID = result['data']['id']
            write_applog("INFO", 'Enquiry', 'Tasks-createSFEnquiry', "Created ID" + str(enquiry.sfEnqID))
            enquiry.save(update_fields=['sfEnqID'])
            syncEnquiryFiles(enqUID, sfAPI)
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
        syncEnquiryFiles(enqUID, sfAPI)
        return {'status': 'Ok'}
    else:
        write_applog("ERROR", 'Enquiry', 'Tasks-updateSFEnquiry', json.dumps(result['responseText']))
        return {'status': 'Error', 'responseText': json.dumps(result['responseText'])}

def syncNotesENQ(enqUID, sfAPI=None):
    enquiry = Enquiry.objects.queryset_byUID(enqUID).get()
    if not enquiry.sfEnqID:
        return {"status": "Error", "responseText": "SF Enquiry ID missing"}

    parent_sfid = enquiry.sfEnqID
    notes = Comment.objects.for_model(enquiry)
    if sfAPI is None:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Case', 'Tasks-syncNotes', result['responseText'])
            return {"status": "Error"}

    return sfAPI.syncNotes(parent_sfid, notes)

def updateSFEnquiryTask(enqUID, sfAPI=None): 
    write_applog("INFO", 'Enquiry', 'Tasks-updateSFEnquiryTask', "Updating Enquiry for:" + str(enqUID))
    result = updateSFEnquiry(enqUID, sfAPI)
    if result['status'] == "Ok":
        result = syncNotesENQ(enqUID, sfAPI)
        
    if result['status'] == "Ok":
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFEnquiryTask', "Finished - Successfully")
        return "Finished - Successfully"
    else:
        write_applog("INFO", 'Enquiry', 'Tasks-updateSFEnquiryTask', "Finished - Unsuccessfully")
        return result['responseText']

def update_all_unsycned_enquiries(case, sfAPI): 
    for enq in case.enquiries.filter(deleted_on__isnull=True).all():
        updateSFEnquiryTask(str(enq.enqUID) , sfAPI)


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
    if (case.email or case.phoneNumber):
        # Check for Household email address
        if case.email:
            if (os.environ.get('ENV') == 'prod') and ('householdcapital.com' in case.email):
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
            update_all_unsycned_enquiries(case, sfAPI)
            return {"status": "Ok"}

        else:

            if isinstance(result['responseText'], dict):
                write_applog("INFO", 'Case', 'Tasks-createSFLead', "caseUID: {} \t{}".format(str(case.caseUID), result['responseText']['message']))

                # Check for duplicates (as indicated by SF) and attempt to retrieve ID using SOQL
                if 'existing' in result['responseText']['message']:
                    if case.email:
                        # Search for email in Leads
                        result = sfAPI.qryToDict('LeadByEmail', case.email, 'result')
                        if len(result['data']) != 0:
                            if int(result['data']['result.PostalCode']) == int(case.postcode):
                                # match on postcode too
                                case.sfLeadID = result['data']['result.Id']
                                case.save(update_fields=['sfLeadID'])
                                write_applog("INFO", 'Case', 'Tasks-createSFLead',
                                             "Saved ID" + str(case.sfLeadID))
                                update_all_unsycned_enquiries(case, sfAPI)
                                return {"status": "Ok"}
                            else:
                                write_applog("INFO", 'Case', 'Tasks-createSFLead', 'Postcode mismatch')
                                return {"status": "Error", "responseText": "Postcode mismatch"}

                    if case.phoneNumber:
                        # Search for phone number in Leads
                        result = sfAPI.qryToDict('LeadByPhone', case.phoneNumber, 'result')
                        if len(result['data']) != 0:
                            if __checkInt(result['data']['result.PostalCode']) == __checkInt(case.postcode):
                                # match on postcode too
                                case.sfLeadID = result['data']['result.Id']
                                case.save(update_fields=['sfLeadID'])
                                write_applog("INFO", 'Case', 'Tasks-createSFLead',
                                             "Saved ID" + str(case.sfLeadID))
                                update_all_unsycned_enquiries(case, sfAPI)
                                return {"status": "Ok"}

                            else:
                                write_applog("INFO", 'Case', 'Tasks-createSFLead', 'Postcode mismatch')
                                return {"status": "Error", "responseText": "Postcode mismatch"}

                    write_applog("INFO", 'Case', 'Tasks-createSFLead', 'No SF ID returned')
                    return {"status": "Error", "responseText": "No SF ID returned"}

                else:
                    write_applog("INFO", 'Case', 'Tasks-createSFLead', result['responseText']['message'])
                    return {"status": "Error", "responseText": result['responseText']['message']}

            else:
                write_applog("INFO", 'Case', 'Tasks-createSFLead', 'Unknown SF error')
                return {"status": "Error", "responseText": "Unknown SF error"}

    else:
        write_applog("INFO", 'Case', 'Tasks-createSFLead', 'No email or phone number')
        return {"status": "Error", "responseText": "No email or phone number"}

def __checkInt(val):
    if val:
        return int(val)
    else:
        return 0


def syncLeadFiles(caseUID, sfAPI):
    write_applog("INFO", 'Case', 'Tasks-syncLeadFiles', "Updating lead files for:" + str(caseUID))
    case = Case.objects.get(caseUID=caseUID)
    DOCUMENT_LIST = {
        "Automated Valuation": case.valuationDocument,
        "Responsible Lending Summary": case.responsibleDocument,
        "Loan Summary": case.summaryDocument,
        "Application Received": case.applicationDocument,
        "Property Image": case.propertyImage
    }
    # Retain file extensions
    DOCUMENT_LIST_MUTATED = {
        "{}{}".format(x, os.path.splitext(y.name)[1]):y 
        for x,y in DOCUMENT_LIST.items()
        if y
    }
    if case.sfLeadID:
        return generic_file_uploader(DOCUMENT_LIST_MUTATED , case.sfLeadID, sfAPI)
    return "Success - No sf Lead"


def syncNotesCASE(caseUID, sfAPI=None):
    write_applog("INFO", 'Case', 'syncNotes', "Syncing notes for caseUID " + caseUID)

    case = Case.objects.queryset_byUID(caseUID).get()
    if not case.sfLeadID:
        return {"status": "Error", "responseText": "SF Lead ID missing"}

    parent_sfid = case.sfLeadID
    notes = Comment.objects.for_model(case)
    if sfAPI is None:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Case', 'Tasks-syncNotes', result['responseText'])
            return {"status": "Error"}

    result = sfAPI.syncNotes(parent_sfid, notes)

    if result['status'] != 'Ok':
        write_applog("ERROR", 'Case', 'deleteNote', "Sync notes -" + json.dumps(result['responseText']))
        return {'status': 'Error', 'responseText': json.dumps(result['responseText'])}

    return {'status': 'Ok', "responseText": "Salesforce Sync Notes!"}



def sync_lead(caseObj, sfAPI=None): 
    caseUID = str(caseObj.caseUID)
    if caseObj.sfOpportunityID is not None: 
        return 
    if sfAPI is None:
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Case', 'Tasks-updateSFLead', result['responseText'])
            return {"status": "Error"}

    if not caseObj.sfLeadID:
        all_enqs = caseObj.enquiries.order_by('-timestamp')
        found = False
        for enq in all_enqs: 
            if not found and enq.sfLeadID: 
                caseObj.sfLeadID = enq.sfLeadID
                found = True
        if found: 
            caseObj.save(should_sync=False)
        if not found:
            result = createSFLeadCase(caseUID, sfAPI)
            if result['status'] != "Ok":
                write_applog("ERROR", 'Case', 'Tasks-updateSFLead', "No SF ID for: " + str(caseUID))
                return {"status": "Error"}

    caseObj.refresh_from_db()
    payload = __buildLeadCasePayload(caseObj)
    result = sfAPI.updateLead(str(caseObj.sfLeadID), payload)
    update_all_unsycned_enquiries(caseObj, sfAPI)
        
    syncNotesCASE(caseUID, sfAPI)
    syncLeadFiles(caseUID, sfAPI)


def run_sync(): 
    import datetime
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'Case', 'Tasks-updateSFLead', result['responseText'])
        return {"status": "Error"}
    print('opening SF')
    leads_to_consider = Case.objects.filter(
       pk__in=Enquiry.objects.filter(
        #    timestamp__lte=(
        #        datetime.datetime.now() - datetime.timedelta(days=46)
        #    ),
        #    timestamp__gte=(
        #        datetime.datetime.now() - datetime.timedelta(days=10)
        #    ),
           ).values_list('case_id', flat=True)
       ,sfOpportunityID__isnull=True,
       ).exclude(touched_in_sf_sync=True)
    failing_leads = []
    for lead in leads_to_consider: 
        try: 
            print('processing caseUId {}'.format(str(lead.caseUID)))
            sync_lead(lead, sfAPI)
            lead.touched_in_sf_sync = True
            lead.save(should_sync=False)
        except: 
            failing_leads.append(str(lead.caseUID))
    
    if failing_leads: 
        failed_leads = "\n".join(failing_leads)
        raiseTaskAdminError(
            "Failed Lead Syncs",
            "Failed Lead UIDS: \n{}".format(failed_leads)
        )
