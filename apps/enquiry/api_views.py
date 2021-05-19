import datetime, logging
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # <-- Here

from apps.enquiry.util import updateCreatePartnerEnquiry, assign_enquiry_leads
from apps.lib.site_Utilities import cleanPhoneNumber, cleanValuation, calcAge, parse_api_names
from apps.lib.site_Enums import (
    marketingTypesEnum, 
    directTypesEnum, 
    stateTypesEnum, 
    productTypesEnum,
    propensityChoicesReverseDict,
    marketingReferrerDict
)
from apps.enquiry.exceptions import MissingRequiredFields
from apps.enquiry.util import find_auto_campaign

from apps.case.assignment import _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP

from apps.settings.models import GlobalSettings


logger = logging.getLogger('myApps')

REQUIRED_FIELDS = [
    'last',
    'phone',
    'postcode',
    'grading',
    'stream'
]

UNASSIGN_USER_MARKETING_SOURCE = [
    'FACEBOOK'
]

class DataIngestion(APIView):
    permission_classes = (IsAuthenticated,)            
    
    def process_notes(self, json_payload): 
        marketing_source_value = json_payload['stream']
        is_social = marketing_source_value in [
            'LINKEDIN',
            'FACEBOOK'
        ]
        upload_type = 'SOCIAL' if is_social else 'PARTNER'
        enquiryString = "[# Updated from {} Upload #]".format(upload_type)
        enquiryString += "\r\n{}: {}".format(upload_type, marketing_source_value)
        enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
        if json_payload.get('origin_timestamp'):
            enquiryString += "\r\nCreate Date: {}".format(json_payload.get('origin_timestamp'))
        if json_payload.get('dob'):
            enquiryString += "\r\nCustomer Date of birth: {}".format(
                datetime.datetime.strptime(
                    json_payload.get('dob'),
                    '%m/%d/%Y'
                ).strftime('%d/%m/%Y')
            )
        if is_social: 
            if json_payload.get('month_of_birth', ''):
                enquiryString += "\r\nMonth of Birth: {}".format(
                    json_payload.get('month_of_birth', '')
                )
            if json_payload.get('age_status', ''):
                enquiryString += "\r\nYear of Birth: {}".format(
                    json_payload.get('age_status', '')
                )
            if json_payload.get('age_over_60'):
                enquiryString += "\r\nOver 60?: {}".format(
                    json_payload.get('age_over_60')
                )
            if json_payload.get('property_range'):
                enquiryString += "\r\nValuation: {}".format(
                    json_payload.get('property_range')
                )
        return enquiryString

    def process_payload(self, json_payload):
        # basic payload format 
        """
            Lead ingestion basic payload structure 
            {
                "first": "Name",
                "last": "Surname",
                "phone": "0298765432",
                "mobile": "0401234567",
                "email": "user@email.com",
                "unit": "1",
                "street_number": "123",
                "street_name": "Main",
                "street_type": "St",
                "suburb": "Sydney",
                "state": "NSW",
                "postcode": 2000,
                "country": "Australia",
                "dob": "01/01/1970",
                "property_type": "strata",
                "property_value": 1000000,
                "property_owing": 200000,
                "marital_status": "single",
                "notes": "wanting to borrow about $200k in the next couple of months",
                "appointment": "1/02/2021 9:00 AM",
                "specialist": "Chris Moutzikis",
                "referred_by": "Luke Sharam",
                "postcode_type": True,
                "grading": "A",
                "stream" : "YOUR_LIFE_CHOICES",
                "origin" : "web page X",
                "origin_timestamp": "????????????????",
                "origin_id": "ASDASD-1ASDQ23-ZXCZCZ-1231",
            }
        """
        for req_field in REQUIRED_FIELDS: 
            if json_payload.get(req_field) is None: 
                raise MissingRequiredFields('Missing field: \'{}\''.format(req_field))
        
        marketing_source_value = json_payload['stream']
        marketingSource = marketingTypesEnum[marketing_source_value].value
        integration_user = User.objects.get(username='integration_user')

        firstname, lastname, name = parse_api_names(json_payload.get('first'), json_payload.get('last'))
        global_settings = GlobalSettings.load()

        payload = {
            'firstname': firstname,
            'lastname': lastname,
            'phoneNumber': cleanPhoneNumber(json_payload['phone']),
            'postcode': json_payload.get('postcode'),
            'propensityCategory': propensityChoicesReverseDict.get(json_payload['grading']),
            'marketingSource': marketingSource,
            'email': json_payload.get('email'),
            'valuation':  cleanValuation(json_payload.get('property_value')),
            'age_1': calcAge(json_payload.get('dob')),
            'productType': productTypesEnum.LUMP_SUM.value,
            'referrer': directTypesEnum[marketingReferrerDict.get(marketing_source_value, "OTHER")].value,
            'base_specificity': json_payload.get('unit'),
            'street_number': json_payload.get('street_number'),
            'street_name': json_payload.get('street_name'),
            'street_type': json_payload.get('street_type'),
            'submissionOrigin': json_payload.get('origin'),
            #'origin_timestamp': json_payload.get('origin_timestamp'),
            'origin_id': json_payload.get('origin_id'),
            # 'user': integration_user,
            'marketing_campaign': find_auto_campaign(marketingSource),
        }
        auto_assign_config = _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP.get(marketingSource)
        if auto_assign_config and getattr(global_settings, auto_assign_config['settings_assignee_field']).count():
            payload['user'] = integration_user
        if json_payload.get('state'): 
            payload['state'] = stateTypesEnum[json_payload['state']].value

        payload['enquiryNotes'] = self.process_notes(json_payload)
        if json_payload.get('notes'):
            payload['enquiryNotes'] += '\n' + json_payload.get('notes')

        enquiries_to_assign = []
        updateCreatePartnerEnquiry(payload, enquiries_to_assign)
        assign_enquiry_leads(enquiries_to_assign, force=True)

    def post(self, request):
        content = {'status': 'Success'}
        status = 200 
        json_payload = request.data
        try:
            self.process_payload(json_payload)
        except Exception as e:
            logger.exception("Ingestion Error")
            if type(e) is MissingRequiredFields:
                content = {
                    'status': str(e)
                }
                status = 400 
            else: 
                status = 500 
                content = {
                    'status': 'Server error'
                }
        return Response(content, status=status)