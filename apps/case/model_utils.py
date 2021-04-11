from config.celery import app
from django.db.models import Q

from apps.case.models import Case
from apps.lib.site_Enums import (
    directTypesEnum, 
    channelTypesEnum,
    caseStagesEnum
)
from apps.lib.site_Enums import PRE_MEETING_STAGES

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
        ).order_by('-updated').first()
    return None 


def _build_case_data_update(enquiry, case=None):
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
        'sfLeadID',
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
    else:
        surname = enquiry.lastname

    # Create dictionary of Case fields from Enquiry fields
    caseDict = {}
    caseDict['caseStage'] = caseStagesEnum.UNQUALIFIED_CREATED.value
    if not (case and (case.caseDescription is not None) and (not case.caseDescription.startswith('Unknown'))):
        caseDict['caseDescription'] = surname + " - " + str(enquiry.postcode)

    if not (case and (case.salesChannel is not None)):
        if enquiry.referrer in salesChannelMap:
            caseDict['salesChannel'] = salesChannelMap[enquiry.referrer]
        else:
            caseDict['salesChannel'] = channelTypesEnum.DIRECT_ACQUISITION.value

    for field in copyFields:
        if not (case and (getattr(case, field) is not None)):
            caseDict[field] = getattr(enquiry, field)

    for enq_field, case_field in map_fields.items():
        if not (case and (getattr(case, case_field) is not None)):
            caseDict[case_field] = getattr(enquiry, enq_field, None)

    return caseDict


def create_case_from_enquiry(enquiry, attach_to_case=True):
    print('create_case_from_enquiry')
    caseDict = _build_case_data_update(enquiry)

    case_obj = Case.objects.create(
        owner=enquiry.user,
        **caseDict
    )

    if attach_to_case: 
        case_obj.enquiries.add(enquiry)
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
