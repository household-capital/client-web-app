#Python Imports
import json
import os
import requests

#Application Imports
from apps.lib.site_Logging import write_applog


class apiAMAL():

    api_url_session = '/api/session'
    api_url_lixi = '/api/lixiapplications'
    api_url_balance = '/api/accounts/{0}/balances/{1}'
    api_url_lvr = '/api/loans/{0}/lvr'
    api_url_schema = '/api/lixivalidateschema'
    api_url_documents='/api/lixiapplications/{0}/documents'
    api_url_nuke='/api/loanapplicationmaintenance/cleanup'

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self):

        self.api_path = ""
        self.token = ""

    def openAPI(self, production):

        if production == True:
            ENV_STR = '_PROD'
        else:
            ENV_STR = '_DEV'

        self.api_path = os.getenv("AMAL_PATH" + ENV_STR)

        jsondata = {'UserNumber': os.getenv("AMAL_USERNUMBER" + ENV_STR),
                    'Password': os.getenv("AMAL_PASSWORD" + ENV_STR)}
        response = requests.post(self.api_path + self.api_url_session, headers=self.headers, json=jsondata)

        status = json.loads(response.text)['status']

        if status != "ok":
            write_applog("ERROR", 'apiAMAL', 'openAPI', 'Could not open API'+ENV_STR)
            return {"status":"Error",'responseText':"API could not be opened"}
        else:
            write_applog("INFO", 'apiAMAL', 'openAPI', 'Opened AMAL API'+ENV_STR)
            self.token = json.loads(response.text)['data'][0]['token']
            return {"status":"Ok",'responseText':"API opened"}

    def sendLixiFile(self,filename):

        headers=dict(Accept="application/json",ContentType="application/xml; charset=UTF-8",AccessToken=self.token)
        files = {'document': open(filename,'rb')}

        response = requests.post(self.api_path+self.api_url_lixi, files=files,headers=headers)

        status=json.loads(response.text)['status']
        error= json.loads(response.text)['error']

        if status!="ok":
            write_applog("ERROR", 'apiAMAL', 'sendLixiFile', 'LIXI submission failed - '+error)
            return {'status':'Error','responseText':error}
        else:
            data = json.loads(response.text)['data'][0]
            identifier = data['identifier']
            loanID=data['loanID']
            validationMessages=data['validationMessages']
            write_applog("INFO", 'apiAMAL', 'sendLixiFile', 'LIXI submission successful' + identifier )
            return {'status': 'Ok', 'data':{'loanID':loanID,'identifier':identifier,'validationMessages':validationMessages}}

    def checkLixiFile(self,filename):

        headers=dict(Accept="application/json",ContentType="application/xml; charset=UTF-8",AccessToken=self.token,
                     fileTypeDescription="Test")
        files = {'document': open(filename,'rb')}
        data={"descriptiveName":"TestDescriptive"}

        response = requests.post(self.api_path+self.api_url_schema, files=files,headers=headers, data=data)

        status=json.loads(response.text)['status']
        error= json.loads(response.text)['error']

        if status!="ok":
            write_applog("ERROR", 'apiAMAL', 'checkLixiFile', 'LIXI validation error - ' + error)
            return {'status': 'Error', 'responseText': 'LIXI validation error - ' + error}
        else:
            write_applog("INFO", 'apiAMAL', 'checkLixiFile', 'LIXI validation passed')

        return {'status':"Ok"}

    def sendDocuments(self, objFileIo, filename, identifier):

        #Sends documents associated with the loan - using the identifier returned by the lixi submission
        fileDescription=filename[:len(filename)-4]

        headers=dict(Accept='application/json',ContentType="multipart/form-data", AccessToken=self.token, FileDescription=fileDescription)
        files={'file':(filename,objFileIo,"application/pdf")}
        specific_url=self.api_path+self.api_url_documents.format(identifier)

        response = requests.post(specific_url, files=files, headers=headers)

        return response

    def nuke(self):
        headers = dict(Accept="application/json", ContentType="application/xml; charset=UTF-8", AccessToken=self.token)
        response = requests.get(self.api_path+self.api_url_nuke, headers=headers)
        return

    def getFundedData(self,ARN):

        headers = dict(Accept="application/json", AccessToken=self.token)

        #Get Valuation
        response = requests.get(self.api_path + self.api_url_lvr.format(ARN), headers=headers)

        response=json.loads(response.content)

        if response['status']=='ok':
            totalValuation=response['data'][0]['totalValuation']
        else:
            write_applog("ERROR", 'apiAMAL', 'getFundedData', 'Could not retrieve valuation - '+ARN)
            return {'status':"Error",'responseText':'Could not retrieve valuation - '+ARN}

        #Get Advanced / Principal
        response_advanced = requests.get(self.api_path + self.api_url_balance.format(ARN,'advanced'), headers=headers)
        response_principal = requests.get(self.api_path + self.api_url_balance.format(ARN,'principal'), headers=headers)

        response_advanced = json.loads(response_advanced.content)
        response_principal = json.loads(response_principal.content)

        if response_advanced['status'] == 'ok' and response_principal['status'] == 'ok':
            advanced = response_advanced['data'][0]['balance']
            principal= response_principal['data'][0]['balance']
        else:
            write_applog("ERROR", 'apiAMAL', 'getFundedData', 'Could not retrieve balances - ' + ARN)
            return {'status': "Error", 'responseText': 'Could not retrieve balances - ' + ARN}

        write_applog("INFO", 'apiAMAL', 'getFundedData', 'Funded data retrieved - ' + ARN)
        return {'status':"Ok",'responseText':'','data':{'totalValuation':totalValuation,'advanced':advanced,'principal':principal}}
