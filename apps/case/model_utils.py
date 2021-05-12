from config.celery import app
from django.db.models import Q

from apps.case.models import Case
from apps.lib.site_Enums import (
    directTypesEnum, 
    channelTypesEnum,
    caseStagesEnum
)
from django_comments.models import Comment
from apps.case.note_utils import add_case_note
from apps.lib.site_Enums import PRE_MEETING_STAGES
from apps.lib.site_Enums import appTypesEnum

# UTILS TO SUPPORT NEW DATA MODEL 


def get_existing_case(phoneNumber, email):
    query = Q() 
    if email and phoneNumber:
        query = (Q(email_1__iexact=email) | Q(phoneNumber_1=phoneNumber))
    elif email:
        query = Q(email_1__iexact=email)
    elif phoneNumber:
        query = Q(phoneNumber_1=phoneNumber)
    if query:
        query = query & Q(deleted_on__isnull=True)
        return Case.objects.filter(
            query
        ).exclude(appType=appTypesEnum.VARIATION.value).order_by('-updated').first()
    return None 


def _build_case_data_update(enquiry, case=None):
    is_create = case is None 
    copyFields = [
        'loanType',
        'age_1',
        'age_2',
        'dwellingType',
        'valuation',

        'postcode',
        'suburb',
        'state',

        'base_specificity',
        'street_number',
        'street_name',
        'street_type',
        'gnaf_id',

        'mortgageDebt',
        #'sfLeadID',
        'productType',
        'isReferPostcode',
        'referPostcodeStatus',
        'valuationDocument',
        'enqUID',
        'propensityCategory',
        'referrer',
        'marketing_campaign',
    ]
    # enq to case
    map_fields = {
        'streetAddress': 'street',
        'timestamp': 'enquiryCreateDate',
        'marketingSource': 'channelDetail',
        'firstname': 'firstname_1',
        'lastname': 'surname_1',
        'email': 'email_1',
        'phoneNumber': 'phoneNumber_1',
    }

    salesChannelMap = {
        directTypesEnum.PARTNER.value: channelTypesEnum.PARTNER.value,
        directTypesEnum.ADVISER.value: channelTypesEnum.ADVISER.value,
        directTypesEnum.BROKER.value: channelTypesEnum.BROKER.value
    }

    if not enquiry.lastname:
        surname = 'Unknown'
        if not is_create and case.surname_1 not in [None, 'Unknown']:
            surname = case.surname_1
    else:
        surname = enquiry.lastname

    # Create dictionary of Case fields from Enquiry fields
    caseDict = {}
    caseDict['caseStage'] = caseStagesEnum.UNQUALIFIED_CREATED.value

    caseDict['caseDescription'] = surname + " - " + str(enquiry.postcode)

    if enquiry.referrer in salesChannelMap:
        caseDict['salesChannel'] = salesChannelMap[enquiry.referrer]
    else:
        caseDict['salesChannel'] = channelTypesEnum.DIRECT_ACQUISITION.value

    for field in copyFields:
        field_val = getattr(enquiry, field)
        if field_val is not None and field_val != '':
            caseDict[field] = field_val

    for enq_field, case_field in map_fields.items():
        field_val = getattr(enquiry, enq_field)
        if field_val is not None and field_val != '':
            caseDict[case_field] = field_val

    return caseDict

def move_notes_to_lead(enquiry, case):
    notes = Comment.objects.for_model(enquiry)
    for note in notes:
        add_case_note(case, note.comment, enquiry.user)



def create_case_from_enquiry(enquiry, attach_to_case=True):
    print('create_case_from_enquiry')
    caseDict = _build_case_data_update(enquiry)

    case_obj = Case.objects.create(
        owner=enquiry.user,
        **caseDict
    )

    if attach_to_case: 
        case_obj.enquiries.add(enquiry)
        move_notes_to_lead(enquiry, case_obj)
    app.send_task('sfEnquiryLeadSync', kwargs={'enqUID': str(enquiry.enqUID)})
    # TBC for exisitng documents

    return case_obj


def update_case_from_enquiry(enquiry, case):
    if caseStagesEnum(case.caseStage).name not in PRE_MEETING_STAGES:
        return

    caseDict = _build_case_data_update(enquiry, case)
    print('caseDict = %s' % caseDict)
    for key, value in caseDict.items():
        setattr(case, key, value)
    case.save()
    move_notes_to_lead(enquiry, case)
