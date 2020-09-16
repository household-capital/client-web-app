# Python Imports
import json
import os
import requests

# Application Imports
from apps.lib.site_Logging import write_applog


class apiWordpress():

    api_url_calculator = 'api/calculators/'
    api_url_contact = '/api/leadsys/'


    def __init__(self):
        self.api_path = ""
        self.calculator_token = ""
        self.contact_token = ""


    def openCalculatorAPI(self):

        self.api_path = os.getenv("WORDPRESS_PATH")
        password = os.getenv("WORDPRESS_PASSWORD")

        payload = {"intent": "getToken",
                   "password": password}

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = requests.post(self.api_path+self.api_url_calculator,
                                 headers=headers,
                                 json=payload)

        if response.status_code == 200:
            self.calculator_token = json.loads(response.text)['token']
            return {'status': "Ok"}
        else:
            return {'status': 'Error', 'responseText': 'Wordpress API could not be opened'}


    def getCalculatorQueue(self):

        if self.calculator_token == "":
            return {'status': 'Error', 'responseText': 'Wordpress API not open'}

        payload = {"intent": "getCalculations"}

        headers = dict(Accept="application/json", ContentType="application/json",
                       authorization=self.calculator_token)

        response = requests.post(self.api_path+self.api_url_calculator,
                                 headers=headers,
                                 json=payload)

        if response.status_code == 200:
            result = json.loads(response.text)
            return {'status': 'Ok', 'data': result}
        else:
            return {'status': 'Error', 'responseText': response.text}


    def markCalculatorRetrieved(self, UID):

        if self.calculator_token == "":
            return {'status': 'Error', 'responseText': 'Wordpress API not open'}

        payload = {"intent":"markRetrieved",
                 "uuid":UID}

        headers = dict(Accept="application/json", ContentType="application/json",
                       authorization=self.calculator_token)

        response = requests.post(self.api_path + self.api_url_calculator,
                                 headers=headers,
                                 json=payload)

        result = json.loads(response.text)
        if response.status_code == 200:
            return {'status': 'Ok', 'data': result}
        else:
            return {'status': 'Error', 'responseText': result}

    def openContactAPI(self):

        self.api_path = os.getenv("WORDPRESS_PATH")
        password = os.getenv("WORDPRESS_PASSWORD")

        payload = {"intent": "getToken",
                   "password": password}

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = requests.post(self.api_path+self.api_url_contact,
                                 headers=headers,
                                 json=payload)

        if response.status_code == 200:
            self.contact_token = json.loads(response.text)['token']
            return {'status': "Ok"}
        else:
            return {'status': 'Error', 'responseText': 'Wordpress API could not be opened'}


    def getContactQueue(self):

        if self.contact_token == "":
            return {'status': 'Error', 'responseText': 'Wordpress API not open'}

        payload = {"intent": "getLeads"}

        headers = dict(Accept="application/json", ContentType="application/json",
                       authorization=self.contact_token)

        response = requests.post(self.api_path+self.api_url_contact,
                                 headers=headers,
                                 json=payload)

        if response.status_code == 200:
            result = json.loads(response.text)
            return {'status': 'Ok', 'data': result}
        else:
            return {'status': 'Error', 'responseText': response.text}


    def markContactRetrieved(self, UID):

        if self.contact_token == "":
            return {'status': 'Error', 'responseText': 'Wordpress API not open'}

        payload = {"intent":"markRetrieved",
                 "uuid":UID}

        headers = dict(Accept="application/json", ContentType="application/json",
                       authorization=self.contact_token)

        response = requests.post(self.api_path + self.api_url_contact,
                                 headers=headers,
                                 json=payload)

        result = json.loads(response.text)
        if response.status_code == 200:
            return {'status': 'Ok', 'data': result}
        else:
            return {'status': 'Error', 'responseText': result}