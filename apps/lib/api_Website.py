# Python Imports
import json
import os
import requests

# Application Imports
from apps.lib.site_Logging import write_applog


class apiWebsite():
    api_url_token = 'token/get'
    api_url_calc_queue = 'calculator/getQueue'
    api_url_calc_retrived = 'calculator/markRetrieved/'
    api_url_cont_queue = 'contact/getQueue'
    api_url_cont_retrived = 'contact/markRetrieved/'

    def __init__(self):
        self.api_path = ""
        self.access_token = ""
        self.refresh_token = ""

    def openAPI(self):

        self.api_path = os.getenv("WEBSITE_PATH")
        username = os.getenv("WEBSITE_USERNAME")
        password = os.getenv("WEBSITE_PASSWORD")

        jsondata = {'username': username,
                    'password': password}

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = requests.post(self.api_path + self.api_url_token, headers=headers, json=jsondata)

        if response.status_code == 200:
            result = json.loads(response.text)
            self.access_token = result['access']
            self.refresh_token = result['refresh']
            return {'status': 'Ok'}

        else:
            return {'status': 'Error', 'responseText': 'Website API could not be opened'}

    def getCalculatorQueue(self):

        headers = dict(Accept="application/json", ContentType="application/xml; charset=UTF-8",
                       Authorization="Bearer " + self.access_token)

        response = requests.get(self.api_path + self.api_url_calc_queue, headers=headers)

        result = json.loads(response.text)
        if response.status_code == 200:

            return {'status': 'Ok', 'data': result}

        else:
            return {'status': 'Error', 'responseText': result['detail']}

    def markCalculatorRetrieved(self, UID):
        headers = dict(Accept="application/json", ContentType="application/xml; charset=UTF-8",
                       Authorization="Bearer " + self.access_token)
        response = requests.patch(self.api_path + self.api_url_calc_retrived + UID, headers=headers)

        result = json.loads(response.text)
        if response.status_code == 200:

            return {'status': 'Ok', 'data': result}

        else:
            return {'status': 'Error', 'responseText': result}

    def getContactQueue(self):

        headers = dict(Accept="application/json", ContentType="application/xml; charset=UTF-8",
                       Authorization="Bearer " + self.access_token)

        response = requests.get(self.api_path + self.api_url_cont_queue, headers=headers)

        result = json.loads(response.text)
        if response.status_code == 200:

            return {'status': 'Ok', 'data': result}

        else:
            return {'status': 'Error', 'responseText': result['detail']}

    def markContactRetrieved(self, UID):
        headers = dict(Accept="application/json", ContentType="application/xml; charset=UTF-8",
                       Authorization="Bearer " + self.access_token)
        response = requests.patch(self.api_path + self.api_url_cont_retrived + UID, headers=headers)

        result = json.loads(response.text)
        if response.status_code == 200:

            return {'status': 'Ok', 'data': result}

        else:
            return {'status': 'Error', 'responseText': result}
