# Python Imports
import base64
import json
import os
import requests

# Application Imports
from apps.lib.site_Logging import write_applog


class apiBurst():

    api_path = 'https://api.transmitsms.com/'
    api_url_balance = 'get-balance.json'
    api_url_send = 'send-sms.json'
    api_key = None
    api_secret = None
    api_auth = None

    def __init__(self):
        self.api_key = os.getenv("BURST_KEY")
        self.api_secret = os.getenv("BURST_SECRET")
        self.api_auth = base64.b64encode((self.api_key+':'+self.api_secret).encode('utf-8')).decode()
        self.headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': 'Basic ' + self.api_auth}

    def getBalance(self):

        response = requests.post(self.api_path + self.api_url_balance, headers=self.headers)

        if response.status_code == 200:
            result = json.loads(response.text)
            return {'status': 'Ok', 'data':result}

        else:
            return {'status': 'Error', 'responseText': 'Burst API call failed'}

    def sendSMS(self, toNumber, message, fromNumber = None):

        target = self.__validate(toNumber)
        if target:

            data = {'message' : message,
                    'to' : target,
                    'from': fromNumber }

            response = requests.post(self.api_path + self.api_url_send, headers=self.headers,
                                      params=data )

            if response.status_code == 200:
                result = json.loads(response.text)
                return {'status': 'Ok', 'data': result}

            else:
                return {'status': 'Error', 'responseText': 'Burst API call failed'}
        else:
            return {'status': 'Error', 'responseText': 'Invalid mobile number'}

    def __validate(self, number):

        result = number.replace("+","").replace(" ","")
        if result[0:3] == "614":
            pass
        elif result[0:2] == "04":
            result = "61" + result[1:]
        else:
            result = None

        if result:
            if len(result) != 11:
                result = None
        return result
