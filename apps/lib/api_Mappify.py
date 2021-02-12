#Python Imports
import json
import os
import requests

#Application Imports
from apps.lib.site_Logging import write_applog


class apiMappify():
    """Mappify address lookup/validation API wrapper"""

    mappifyUrlGeo= 'https://mappify.io/api/rpc/address/geocode/'
    mappifyUrlPost= 'https://mappify.io/api/rpc/address/autocomplete/'

    def __init__(self):
        self.unit=""
        self.streetAddress=""
        self.fullStreetAddress=""
        self.suburb=""
        self.postcode=""
        self.state=""
        self.location={}

        self.APIKey=os.getenv('MAPPIFY_KEY')

    def setAddress(self,addressDict):
        minFields=['streetAddress', 'suburb', 'postcode', 'state']

        for field in minFields:
            if field not in addressDict or addressDict[field]==None:
                return {"status":"Error","responseText":"Missing Addresss Fields"}

        street_address = "{} {} {}".format(
            addressDict.get('streetnumber', ''),
            addressDict.get('streetname', ''),
            addressDict.get('streettype', ''),
        ).strip()

        concatenated_address = "{} {}".format(
            addressDict.get('unit', ''),
            street_address
        ).strip()

        self.streetAddress = concatenated_address
        self.fullStreetAddress = concatenated_address

        if addressDict.get('unit', '') != '': 
            self.unit = addressDict.get('unit', '')
            self.streetAddress = street_address

        self.suburb = addressDict['suburb']
        self.postcode = addressDict['postcode']
        self.state = addressDict['state']
        
        self.streetnumber = addressDict.get('streetnumber', '')
        self.streetname = addressDict.get('streetname', '')
        self.streettype = addressDict.get('streettype', '')

        return {"status": "Ok"}

    def checkPostalAddress(self):

        #Strip apartment if present
        stripAddress = self.streetAddress
        #Use GeoCode to get location first
        payload = {"streetAddress": stripAddress,
                   "postcode": self.postcode,
                   "suburb": self.suburb,
                   "state": self.state,
                   "apiKey": self.APIKey}

        response = requests.post(self.mappifyUrlGeo, data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})
                                 
        if response.status_code != 200:
            write_applog("ERROR", 'apiMappify', 'checkPostalAddress', 'API Call Failed - '+ str(response.status_code))
            return {'status':"Error","responseText":'API Call Failed - could not check address'}

        response=response.json()

        if response['result']==None:
            return {'status': "Error", "responseText": 'No Address Match'}

        if response['confidence'] < 0.25:
            return {'status': "Error", "responseText": 'Poor Address Match - ' + response['result']['streetAddress']}

        self.location=response['result']['location']

        
        # Use Autocomplete to get Postal Address
        payload = {"streetAddress": "{} {} {} {}".format(self.fullStreetAddress, self.suburb, self.postcode, self.state),
                   "sortOrigin": self.location,
                   "formatCase": True,
                   "includeInternalIdentifiers": True,
                   "apiKey": self.APIKey}

        response = requests.post(self.mappifyUrlPost, data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})

        if response.status_code != 200:
            write_applog("ERROR", 'apiMappify', 'checkPostalAddress', 'API Call Failed - '+response.status_code)
            return {'status':"Error","responseText":'API Call Failed - could not check address'}


        response=response.json()

        write_applog("INFO", 'apiMappify', 'checkPostalAddress', 'API Success')
        results = response['result']
        confidence = response['confidence']
        normalise = lambda _s: str(_s).lower()
        base_validator = lambda _dict, dictkey, objkey: normalise(_dict[dictkey]) == normalise(getattr(self, objkey, ''))
        dict_validator_map = {
            'flatNumber': 'unit',
            'streetName': 'streetname',
            'streetType': 'streettype' 
        }
        error_text = ""
        for result in results: 
            result_valid = True
            error_text = error_text + "\nAttempting Validation: {}".format(result['streetAddress'])
            for x,y in dict_validator_map.items():  
                if base_validator(result, x, y) == False: 
                    error_text = error_text + "\n" + "- Validator_value={} != In-App={} [{} in app]".format(
                        result[x],
                        getattr(self, y, ''),
                        y
                    )
                result_valid =  result_valid and  base_validator(result, x, y)
            if result_valid: 
                return {
                    'status': 'Ok',
                    'responseText': 'Address Match - {} Confidence'.format('High' if confidence > 0.5 else 'Low'),
                    'result': result
                }
        error_text += "\nNo valid address found. Please edit unit or streetnumber or streetname or streettype"
        return {'status':"Error", "responseText": error_text}

    def autoComplete(self, streetAddress):

        # Use Autocomplete to get Postal Address
        payload = {
            "streetAddress": streetAddress,
            "formatCase": True,
            "includeInternalIdentifiers": True,
            "apiKey": self.APIKey}

        response = requests.post(self.mappifyUrlPost, data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})

        response = response.json()
        return response['result']