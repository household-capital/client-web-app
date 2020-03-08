# Python Imports
import os
import json
import requests
import base64


class apiDocsAway():

    apiAccountUrl = "https://www.docsaway.com/app/api/rest/account.json"
    apiSendMailUrl = "https://www.docsaway.com/app/api/rest/mail.json"

    username = os.getenv('DOCS_USERNAME')
    key = os.getenv('DOCS_KEY')

    def getAccountDetails(self):

        headers = {
            'content-type': "application/json"}

        payload = {
            "APIConnection":{
                "email": self.username,
                "key": self.key
            },
            "balance": True,
            "volume": True,
            "reference": True,
            "company": True,
            "name": True,
            "APIReport": True
            }

        response = requests.post(self.apiAccountUrl, headers=headers, data=json.dumps(payload))

        return response

    def sendPdfByMail(self, src_filepath, name, street, city, state, postcode):

        headers = {
            'content-type': "application/json"}

        file = open(src_filepath,'rb')
        fileContents = file.read()
        fileEncode = base64.b64encode(fileContents)
        fileStr = str(fileEncode, "utf-8")

        payload = {
            "APIConnection":{
                "email": self.username,
                "key": self.key
            },
            "APIMode": "TEST",
            "APIReport": False,
            "Recipient":
                {
                    "name": name,
                    "company": False,
                    "address1": street,
                    "city": city,
                    "state": state,
                    "zip": postcode,
                    "country": "AU"
                },
            "PrintingStation":
                {
                    "id": "AU2",
                    "courierID": 'AU2_1',
                    "ink": "CL",
                    "paper": "80"
                },
            "PDFFile": fileStr }

        response = requests.post(self.apiSendMailUrl, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            return {'status':'Ok', 'data': response.text}
        else:
            return {'status': 'Error', 'responseText': response.text}

