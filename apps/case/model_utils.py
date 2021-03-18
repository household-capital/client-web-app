from config.celery import app
from django.db.models import Q

from apps.case.models import Case
from apps.lib.site_Enums import (
    directTypesEnum, 
    channelTypesEnum,
    caseStagesEnum
)

# UTILS TO SUPPORT NEW DATA MODEL 


def get_existing_case(phoneNumber, email):
    query = Q() 
    if email and phoneNumber:
        query = (Q(email__iexact=email) | Q(phoneNumber=phoneNumber))
    elif email:
        query = Q(email__iexact=email)
    elif phoneNumber:
        query = Q(phoneNumber=phoneNumber)
    if query:
        return Case.objects.filter(
            query
        ).order_by('-updated').first()
    return None 


def create_case_from_enquiry(enquiry, attach_to_case=True): 
    copyFields = [
        'firstname',
        'lastname',
        'loanType', 
        'age_1', 
        'age_2', 
        'dwellingType', 
        'valuation', 
        'postcode', 
        'suburb', 
        'state', 
        'email',
        'phoneNumber', 
        'mortgageDebt',
        'sfLeadID', 
        'productType', 
        'isReferPostcode', 
        'referPostcodeStatus', 
        'valuationDocument',
        'enqUID',
        'propensityCategory',
        'referrer'
    ]
    # enq to case
    map_fields = {
        'streetAddress': 'street',
        'enquiryDocument': 'summaryDocument',
        'enquiryNotes': 'caseNotes',
        'timestamp': 'enquiryCreateDate',
        'marketingSource': 'channelDetail'
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
    caseDict['caseDescription'] = surname + " - " + str(enquiry.postcode)
    if enquiry.referrer in salesChannelMap:
        caseDict['salesChannel'] = salesChannelMap[enquiry.referrer]
    else:
        caseDict['salesChannel'] = channelTypesEnum.DIRECT_ACQUISITION.value
    for field in copyFields: 
        caseDict[field] = getattr(enquiry, field)
    for enq_field, case_field in map_fields.items():
        caseDict[case_field] = getattr(enquiry, enq_field, None)
    case_obj = Case.objects.create(
        owner=enquiry.user,
        **caseDict
    )
    if attach_to_case: 
        case_obj.enquiries.add(enquiry)
    app.send_task('sfEnquiryLeadSync', kwargs={'enqUID': str(enquiry.enqUID)})
    # TBC for exisitng documents
    return case_obj
