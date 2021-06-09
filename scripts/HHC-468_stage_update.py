from apps.lib.site_Enums import directTypesEnum
from apps.case.models import * 
from apps.lib.api_Salesforce import apiSalesforce

import json

is_mq = lambda case: (
    case.referrer in [
        directTypesEnum.WEB_ENQUIRY.value,
        directTypesEnum.SOCIAL.value,
        directTypesEnum.WEB_CALCULATOR.value,
        directTypesEnum.PARTNER.value
    ]
) or (
    (
        case.firstname_1 or 
        case.surname_1 or 
        case.firstname_2 or 
        case.surname_2
    ) and 
    (case.phoneNumber_1 or case.email_1) and 
    case.postcode and 
    case.age_1
) # HHC-468

expected_stage = caseStagesEnum.UNQUALIFIED_CREATED.value

leads = Case.objects.filter(caseStage=expected_stage)

the_ones = [
    x for x in leads if is_mq(x)
]
the_ones_id = [
    x.pk for x in the_ones
]
sf_bulk_update = [
    {
        'Id': x.sfLeadID,
        'Status__c': "Marketing Qualified",
        'Status': "Marketing Qualified"
    }
    for x in the_ones
    if x.sfLeadID
]


with open('sf_bulk_update.txt', 'w') as f: 
    f.write(
        json.dumps(sf_bulk_update)
    )

Case.objects.filter(pk__in=the_ones_id).update(
    caseStage=caseStagesEnum.MARKETING_QUALIFIED.value
)

sfAPI = apiSalesforce() 
sfAPI.openAPI(True)
sfAPI.sf.bulk.Lead.update(
    sf_bulk_update
)

