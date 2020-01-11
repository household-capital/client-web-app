#Python Imports
import json
import os
import requests

#Application Imports
from apps.lib.site_Logging import write_applog


class apiMappify():

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
        minFields=['streetAddress','suburb','postcode','state']

        for field in minFields:
            if field not in addressDict or addressDict[field]==None:
                return {"status":"Error","responseText":"Missing Addresss Fields"}

        if '/' in addressDict['streetAddress']:
            self.unit, self.streetAddress = addressDict['streetAddress'].split("/", 1)
            self.fullStreetAddress = addressDict['streetAddress']
        else:
            self.streetAddress = addressDict['streetAddress']
            self.fullStreetAddress = addressDict['streetAddress']

        self.suburb = addressDict['suburb']
        self.postcode = addressDict['postcode']
        self.state = addressDict['state']

        return {"status": "Ok"}

    def checkPostalAddress(self):

        #Use GeoCode to get location first
        payload = {"streetAddress": self.fullStreetAddress,
                   "postcode": self.postcode,
                   "suburb": self.suburb,
                   "state": self.state,
                   "apiKey": self.APIKey}

        response = requests.post(self.mappifyUrlGeo, data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})

        if response.status_code != 200:
            write_applog("ERROR", 'apiMappify', 'checkPostalAddress', 'API Call Failed - '+response.status_code)
            return {'status':"Error","responseText":'API Call Failed - could not check address'}

        response=response.json()

        if response['result']==None:
            return {'status': "Error", "responseText": 'No Address Match'}

        if response['confidence'] < 0.25:
            return {'status': "Error", "responseText": 'Poor Address Match - ' + response['result']['streetAddress']}

        self.location=response['result']['location']


        # Use Autocomplete to get Postal Address
        payload = {"streetAddress": self.fullStreetAddress+" "+self.suburb+" "+str(self.postcode)+" "+self.state ,
                   "sortOrigin": self.location,
                   "formatCase": True,
                   "includeInternalIdentifiers": True,
                   "apiKey": self.APIKey}

        response = requests.post(self.mappifyUrlPost, data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})

        if response.status_code != 200:
            write_applog("ERROR", 'apiMappify', 'checkPostalAddress', 'API Call Failed - '+response.status_code)
            return {'status':"Error","errorText":'API Call Failed - could not check address'}


        response=response.json()

        write_applog("INFO", 'apiMappify', 'checkPostalAddress', 'API Success')

        if len(response['result'])==1 and response['confidence']>0.5:
               return {'status': "Ok", "responseText": 'Address Match - High Confidence',"result":response['result'][0]}
        else:
            return {'status': "Ok", "responseText": 'Address Match - Low Confidence', "result": response['result'][0]}
