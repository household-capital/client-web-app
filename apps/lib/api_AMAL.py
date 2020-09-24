#Python Imports
import json
import os
import requests

from django.core.files.storage import default_storage

#Application Imports
from apps.lib.site_Logging import write_applog

class apiAMAL():
    """AMAL RestAPI wrapper"""

    api_url_session = '/api/session'
    api_url_lixi = '/api/lixiapplications'
    api_url_balance = '/api/accounts/{0}/balances/{1}'
    api_url_dates = '/api/loans/{0}/dates'
    api_url_lvr = '/api/loans/{0}/lvr'
    api_url_bpay = '/api/loans/{0}/bpay'
    api_url_transactions = '/api/loans/{0}/transactions'
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

        jsondata = {'UserNumber': os.getenv("AMAL_USERNUMBER" + ENV_STR+"_CAL"),
                    'Password': os.getenv("AMAL_PASSWORD" + ENV_STR)}
        response = requests.post(self.api_path + self.api_url_session, headers=self.headers, json=jsondata)

        try:
            status = json.loads(response.text)['status']
        except:
            return {"status": "Error", 'responseText': "API could not be opened"}

        if status != "ok":
            write_applog("ERROR", 'apiAMAL', 'openAPI', 'Could not open API'+ENV_STR)
            return {"status":"Error",'responseText':"API could not be opened"}
        else:
            write_applog("INFO", 'apiAMAL', 'openAPI', 'Opened AMAL API'+ENV_STR)
            self.token = json.loads(response.text)['data'][0]['token']
            return {"status":"Ok",'responseText':"API opened"}

    def sendLixiFile(self,filename):

        headers=dict(Accept="application/json",ContentType="application/xml; charset=UTF-8",AccessToken=self.token)
        files = {'document': default_storage.open(filename,'rb')}

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
        files = {'document': default_storage.open(filename,'rb')}
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
            totalValuation = 1

        #Get Advanced / Principal
        advanced = self.__getBalanceValue(ARN, 'advanced', headers)
        principal = self.__getBalanceValue(ARN, 'principal', headers)
        approved = self.__getBalanceValue(ARN, 'approved', headers)

        #Calc LVR
        if principal and totalValuation:
            currentLVR = principal / totalValuation
        else:
            currentLVR = 0

        #Get Dates
        response = requests.get(self.api_path + self.api_url_dates.format(ARN), headers=headers)
        response = json.loads(response.content)

        if response['status'] == 'ok':
            settlement = response['data'][0]['settlement']
            discharge = response['data'][0]['discharge']
        else:
            settlement = None
            discharge = None

        #Get BPay
        response = requests.get(self.api_path + self.api_url_bpay.format(ARN), headers=headers)
        response = json.loads(response.content)

        if response['status'] == 'ok':
            bPayCode = response['data'][0]['billerCode']
            bPayRef = response['data'][0]['referenceNumber']
        else:
            bPayCode = None
            bPayRef = None

        write_applog("INFO", 'apiAMAL', 'getFundedData', 'Funded data retrieved - ' + ARN)
        return {'status':"Ok",'responseText':'','data':{'totalValuation':totalValuation,'advancedAmount':advanced,
                                                        'currentBalance':principal, 'approvedAmount':approved,
                                                        'currentLVR':currentLVR,
                                                        'settlementDate':settlement, 'dischargeDate':discharge,
                                                        'bPayBillerCode':bPayCode,'bPayReference':bPayRef}}

    def __getBalanceValue(self, ARN, balanceName, headers):
        response = requests.get(self.api_path + self.api_url_balance.format(ARN,balanceName), headers=headers)
        try:
            response_dict = json.loads(response.content)
            if response_dict['status'] == 'ok':
                return response_dict['data'][0]['balance']
        except:
            pass

        return 0

    def getTransactionData(self,ARN):

        headers = dict(Accept="application/json", AccessToken=self.token)

        #Get Valuation
        response = requests.get(self.api_path + self.api_url_transactions.format(ARN), headers=headers)
        if response.status_code!=200:
            return {'status': "Error", 'responseText': response.status_code}

        response=json.loads(response.content)

        if response['status']=='ok':
            return {'status': "Ok", 'data': response['data']}
        else:
            return {'status': "Error", 'responseText': ""}
