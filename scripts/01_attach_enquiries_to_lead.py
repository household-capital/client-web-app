from apps.enquiry.models import Enquiry
from apps.case.models import Case
from apps.lib.site_Enums import caseStagesEnum, enquiryStagesEnum, closeReasonEnum, closeReasonEnumUpdated, PRE_MEETING_STAGES
from apps.lib.hhc_LoanValidator import LoanValidator

# enqs = Enquiry.objects.order_by('updated').iterator()
# WHICH Enquiries should create LEADS for dups (?)
# ASk sue 
# current approach 
# Target all enquries which Distribution marks as "MAIN" first 
# Other dups will attach ^ 

# get all enquiries which are in pre-meeting. 

"""
    Assumptions
    1. Migrations have been run but no tamperment with creating "Leads" 
    2. Duplicates have been managed (i.e Deleted) and only the latest are used to create Leads
       enquiries without cases
    3. 
"""

######################################## 
# Enquiries which havent become cases 
########################################

# only Run against Enquiries with no case_ids
# enq_to_case_dict = dict(Case.objects.filter(enqUID__isnull=False).values_list('enqUID', 'pk'))
# member ship tests faster in sets
# un_actioned_enqs = Enquiry.objects.filter(case_id__isnull=True).order_by('-timestamp').iterator()

###
ENQS_WITH_ADDRESS_GT_60 = [
    '7bdb1eb1-d981-40c4-a023-11d712d18efe'
]

ENQS_TO_IGNORE_CONSIDER = ENQS_WITH_ADDRESS_GT_60


def handle_all_enqs(): 
    enq_to_case_dict = dict(Case.objects.filter(enqUID__isnull=False).values_list('enqUID', 'pk'))
    # member ship tests faster in sets
    un_actioned_enqs = Enquiry.objects.filter(case_id__isnull=True).exclude(enqUID__in=ENQS_TO_IGNORE_CONSIDER).order_by('-timestamp').iterator()
    for enq in un_actioned_enqs:
        print('processing enqUID - {}'.format(str(enq.enqUID))) 
        if enq.case_id:
            print('Skipping enqUID - {}'.format(str(enq.enqUID)))
            continue
        if enq_to_case_dict.get(enq.enqUID) is not None:
            # case exists 
            enq.case_id = enq_to_case_dict.get(enq.enqUID)
        enq.save(should_sync=False) # save will create or fetch the associated case Obj
        # this will attach but will not propagate values of fields onto leads 

def update_lead_stage():
    enquiries = list(Enquiry.objects.order_by('-timestamp').exclude(enqUID__in=ENQS_TO_IGNORE_CONSIDER))
    for chunked_enqs in chunks(enquiries, 500):
        to_update = []
        for enq in chunked_enqs:
            case_obj = update_lead_stages_from_enquiry(enq)
            if case_obj is not None: 
                to_update.append(case_obj)
        Case.objects.bulk_update(to_update, ['caseStage'])



def update_lead_stages_from_enquiry(enquiry):
    print('Updating Stage for enqUID = {}'.format(enquiry.enqUID))
    case_obj = enquiry.case
    if case_obj is None: 
        print('No lead Object here.. EnqUID {}'.format(enq.enqUID))
        raise Exception('No lead Object here.. EnqUID {}'.format(enq.enqUID))
    # app
    # Old Case Model used EnqUID to show relationsip between 
    enqs_attached = case_obj.enquiries.count()

    if enqs_attached > 0: 
        latest_enq = case_obj.enquiries.latest('timestamp')
        if latest_enq.timestamp > enquiry.timestamp:
            print("Attaching older enquiry to lead. Should not affect stage")
            return 

    if not case_obj.caseStage in [
        caseStagesEnum[_stage].value
        for _stage in PRE_MEETING_STAGES
    ]:
        # What about closed (?)
        print('no need to update - Loan past interview stage')
        return
    enq_dict = vars(enquiry)
    enq_dict.pop('_state')
    loanObj = LoanValidator(enq_dict)
    chkOpp = loanObj.validateLoan()
    if chkOpp['status'] != 'Ok': 
        print('Case uid {} set to Marketing Qualified'.format(case_obj.caseUID))
        case_obj.caseStage = caseStagesEnum.MARKETING_QUALIFIED.value
        return case_obj

    stage_mapping = {
        enquiryStagesEnum.GENERAL_INFORMATION.value: caseStagesEnum.SQ_GENERAL_INFO.value,
        enquiryStagesEnum.BROCHURE_SENT.value: caseStagesEnum.SQ_BROCHURE_SENT.value,
        enquiryStagesEnum.SUMMARY_SENT.value: caseStagesEnum.SQ_CUSTOMER_SUMMARY_SENT.value,
        enquiryStagesEnum.DISCOVERY_MEETING.value: caseStagesEnum.SQ_BROCHURE_SENT.value,
        enquiryStagesEnum.FUTURE_CALL.value: caseStagesEnum.SQ_FUTURE_CALL.value,
        enquiryStagesEnum.LOAN_INTERVIEW.value: caseStagesEnum.SQ_GENERAL_INFO.value, 
        enquiryStagesEnum.LIVE_TRANSFER.value: caseStagesEnum.SQ_GENERAL_INFO.value,
        enquiryStagesEnum.DUPLICATE.value: caseStagesEnum.SQ_GENERAL_INFO.value, 
        enquiryStagesEnum.MORE_TIME_TO_THINK.value: caseStagesEnum.MARKETING_QUALIFIED.value,
    }
    lead_stage = stage_mapping.get(enquiry.enquiryStage)
    if lead_stage is not None: 
        case_obj.caseStage = lead_stage
        return case_obj
    """ 
        Unhandled for enquiries in stages  Loan Interview, or
        Live transfer, or
        Duplicate 
        Check with @sue   
    """

    
    old_to_new_close_map = {
        closeReasonEnum.MINIMUM_LOAN_AMOUNT.value: closeReasonEnumUpdated.BELOW_MIN_LOAN_AMOUNT.value, 
        closeReasonEnum.MORTGAGE.value: closeReasonEnumUpdated.REFI_TOO_LARGE.value,
        closeReasonEnum.SHORT_TERM.value: closeReasonEnumUpdated.UNSUITABLE_PURPOSE.value,
        closeReasonEnum.TENANTS.value: closeReasonEnumUpdated.UNSUITABLE_TITLE_OWNERSHIP.value,
        closeReasonEnum.UNSUITABLE_PROPERTY.value: closeReasonEnumUpdated.UNSUITABLE_PROPERTY.value, 
        closeReasonEnum.UNSUITABLE_PURPOSE.value: closeReasonEnumUpdated.UNSUITABLE_PURPOSE.value, 
        closeReasonEnum.ALTERNATIVE_SOLUTION.value: closeReasonEnumUpdated.NOT_PROCEEDING.value,
        closeReasonEnum.COMPETITOR.value: closeReasonEnumUpdated.NOT_PROCEEDING.value,
        closeReasonEnum.NO_CLIENT_ACTION.value: closeReasonEnumUpdated.NOT_PROCEEDING.value,
        closeReasonEnum.ANTI_REVERSE_MORTGAGE.value: closeReasonEnumUpdated.DOESNT_LIKE_REV_MORTGAGES.value,
        closeReasonEnum.CALL_ONLY.value: closeReasonEnumUpdated.FEE_INTEREST_TOO_HIGH.value
    }

    if enquiry.closeDate and enquiry.closeReason is not None: 
        case_obj.caseStage = old_to_new_close_map.get(enquiry.closeReason, closeReasonEnumUpdated.OTHER.value)
        return case_obj

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def handle_do_not_market():
    all_leads_pre_meet = list(Case.objects.exclude(sfOpportunityID__isnull=False).order_by('timestamp'))
    PARTITION_SIZE = 300
    for lead_chunk in chunks(all_leads_pre_meet, PARTITION_SIZE):
        objects_to_update = [] 
        for lead in lead_chunk:
            lead.doNotMarket = any(lead.enquiries.values_list('doNotMarket', flat=True)) or lead.lossdata.doNotMarket
            objects_to_update.append(lead)
        Case.objects.bulk_update(objects_to_update, ['doNotMarket'])
    # faster/efficient
    

def handle_edge_fields():
    handle_do_not_market()
    pass

def run_script(): 
    handle_all_enqs()
    update_lead_stage()
    print('yay - All done')

#######
def sync_to_sf(): 
    all_leads_pre_meet = Case.objects.exclude(sfOpportunityID__isnull=False).order_by('timestamp')
    for i in all_leads_pre_meet:
        i.save(should_sync=True)
