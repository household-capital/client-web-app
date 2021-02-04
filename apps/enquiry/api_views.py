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
        # ylc
        name = "{} {}".format(
            json_payload['first'],
            json_payload['last']
        )
        postcode = json_payload['postcode']
        email = json_payload['email']
        phonenumber = cleanPhoneNumber(json_payload['mobile'])
        valuation = cleanValuation(json_payload['property_value'])
        age_1 = calcAge(json_payload['dob'])
        marketingSource = marketingTypesEnum.YOUR_LIFE_CHOICES.value
        referrer = directTypesEnum.PARTNER.value
        productType = productTypesEnum.LUMP_SUM.value
        state = stateTypesEnum[json_payload['state']].value
        propensityCategory = propensityChoicesReverseDict.get(
            json_payload['grading']
        )

        marketing_source_value = 'YOUR_LIFE_CHOICES' 
        marketing_source_string = 'Your Life Choices'

        enquiryString = "[# Updated from Partner Upload #]"
        enquiryString += "\r\nPartner: {}".format(marketing_source_string)
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
        json_payload = request.data
        self.process_payload(json_payload)
        return Response(content)