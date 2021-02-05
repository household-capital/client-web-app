import datetime 

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # <-- Here

from apps.enquiry.util import updateCreateEnquiry
from apps.lib.site_Utilities import cleanPhoneNumber, cleanValuation, calcAge
from apps.lib.site_Enums import (
    marketingTypesEnum, 
    directTypesEnum, 
    stateTypesEnum, 
    productTypesEnum,
    propensityChoicesReverseDict
)

class DataIngestion(APIView):
    permission_classes = (IsAuthenticated,)            
    
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
                "stream" : "YOUR_LIFE_CHOICES"
            }
        """
        name = "{} {}".format(
            json_payload.get('first', ''),
            json_payload.get('last', '')
        )
        postcode = json_payload['postcode']
        email = json_payload['email']
        phonenumber = cleanPhoneNumber(json_payload['mobile'])
        valuation = cleanValuation(json_payload['property_value'])
        age_1 = calcAge(json_payload['dob'])
        marketing_source_value = json_payload['stream']
        marketingSource = marketingTypesEnum[marketing_source_value].value
        referrer = directTypesEnum.PARTNER.value
        productType = productTypesEnum.LUMP_SUM.value
        state = stateTypesEnum[json_payload['state']].value
        propensityCategory = propensityChoicesReverseDict.get(
            json_payload['grading']
        )
        enquiryString = "[# Updated from Partner Upload #]"
        enquiryString += "\r\nPartner: {}".format(marketing_source_value)
        enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
        if json_payload.get('notes'): 
            enquiryString += json_payload.get('notes')
        payload = {
            "name": name,
            "postcode": postcode,
            "email": email,
            "phoneNumber": phonenumber,
            "valuation": valuation,
            "age_1": age_1,
            "marketingSource": marketingSource,
            "referrer": referrer,
            "productType": productType,
            "state": state ,
            "propensityCategory": propensityCategory
        }
        updateCreateEnquiry(
            email,
            phonenumber,
            payload,
            enquiryString,
            marketingSource,
            [],
            False,
        )

    def post(self, request):
        content = {'status': 'Success'}
        status = 200 
        json_payload = request.data
        try:
            self.process_payload(json_payload)
        except KeyError as e: 
            missing_key = str(e)
            content = {
                'status': 'Payload missing mandatory key {}'.format(missing_key)
            }
            status = 400 
        return Response(content, status=status)