#Python Imports
import time
import json
import logging
import os

#Django Imports
from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.core import files

#Third-party Imports

#Application Imports
from apps.lib.api_AMAL import apiAMAL
from apps.lib.api_Salesforce import apiSalesforce
from .lixi_EnrichEnum import EnrichEnum
from .lixi_Generator_CAL import LixiXMLGenerator
from apps.lib.site_Globals import ECONOMIC


class CloudBridge():

    LIXI_SETTINGS = {'LIXI_VERSION_CAL': '2.6.17',
                     'LIXI_VERSION':'0.0.3',
                     'SCHEMA_FILENAME_CAL': "/apps/lib/lixi/LixiSchema/LIXI-CAL-2.6.17".replace(".", "_") + '.xsd',
                     'SCHEMA_FILENAME':"/apps/lib/lixi/LixiSchema/LIXI-ACC-0.0.3".replace(".", "_") + '.xsd',
                     'ORIGINATOR_MARGIN': ECONOMIC['lendingMargin'],
                     'ns_map_':{"xsi": 'http://www/w3/org/2001/XMLSchema-instance'},
                     'FILEPATH':(settings.MEDIA_ROOT+'/customerReports/'),
                     'AMAL_DOCUMENTS':["Application Form", "Loan Contract", "Valuation Report"]
                     }

    def __init__(self, opportunityId, isSendFiles, isProdSF, isProdAMAL):

        self.schemaFilename=self.LIXI_SETTINGS['SCHEMA_FILENAME_CAL']
        self.filePath=self.LIXI_SETTINGS['FILEPATH']
        self.AMAL_Documents=self.LIXI_SETTINGS['AMAL_DOCUMENTS']

        self.opportunityId = opportunityId
        self.isSendFiles=isSendFiles

        if isSendFiles==True and isProdAMAL==True:
            self.isProduction = True
        else:
            self.isProduction=False

        self.isProdSF=isProdSF
        self.isProdAMAL=isProdAMAL

        self.outputLog = ""
        self.warningLog=""

        self.outputFile=""

    def openAPIs(self):

        #Open SF API
        self.sfAPI = apiSalesforce()
        result = self.sfAPI.openAPI(self.isProdSF)
        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': "Could not connect to Salesforce"}

        if self.isSendFiles:
            self.sfAPI.setResultsPrefix("Cloud Bridge")
        else:
            self.sfAPI.setResultsPrefix("Cloud Bridge [Test Extract]")

        #Open AMAL API
        self.mlAPI = apiAMAL()
        result=self.mlAPI.openAPI(self.isProdAMAL)
        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': "Could not connect to AMAL"}

        return {'status': "Ok", 'responseText': "Bridge Established"}


    def createLixi(self):

        AMAL_LoanId=""
        identifier=""

        #Generate Lixi File
        try:
            result = self.generateLixiFile()
            if result['status']!="Ok":
                return {'status': "Error", 'responseText': "Unhandled Error", 'log': self.outputLog}
        except:
            return {'status': "Error", 'responseText': "Unhandled Error", 'log':self.outputLog}

        self.outputFile=result['data']

        return {'status':'Ok', "data":{'filename':self.outputFile}, 'log':self.outputLog}


    def submitLixiFiles(self, filename):

        try:
            result = self.sendToAMAL(filename, self.isSendFiles)
        except:
            return {'status': "Error", 'responseText': "Unhandled Error", 'log': self.outputLog}

        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': 'Submit Error', 'log': self.outputLog}

        if self.isSendFiles:
            identifier = result['data']['identifier']
            AMAL_LoanId = result['data']['loanID']

        self.__logging("Application ID: " + identifier)
        self.__logging("Loan ID: " + AMAL_LoanId)

        # Update Salesforce with LoanId
        result = self.saveAMALLoanId(self.opportunityId, AMAL_LoanId, self.isProduction)
        if result['status'] != 'Ok':
            self.warningLog += 'ARN not saved in Salesforce' + "\r\n"

        self.__logging("Cloud Bridge's work is done here")
        return {'status': "Ok", 'responseText': "Cloud Bridge's work is done here", 'log': self.outputLog,
                'warningLog': self.warningLog, "data":{'identifier':identifier,'AMAL_LoanId':AMAL_LoanId}}


    def getSFLoanList(self):
        #Returns a DataFrame of all approved loans from Salesforce
        self.__logging("Extracting approved Loans from Saleforce")

        loanList = self.sfAPI.getApprovedLoans()

        self.__logging(str(len(loanList.index)) + " approved loans returned")
        return loanList


    def checkSFData(self):

        msgString=""
        loanDict = self.sfAPI.getLoanExtract(self.opportunityId)['data']

        # Check loan settlement date
        reqs = ['Loan.Loan_Settlement_Date__c']
        if not self.__chkExist(loanDict,reqs):
            msgString += "Loan settlement date missing. "

        # Check valuation data
        reqs = ['Prop.Home_Value_FullVal__c','Prop.Valuer__c','Prop.Valuer_Name__c']
        if not self.__chkExist(loanDict,reqs):
            msgString += "Valuation data missing. "

        # Check insurance data
        reqs = ['Prop.Insurer__c','Prop.Policy_Number__c','Prop.Minimum_Insurance_Value__c','Prop.Insurance_Expiry_Date__c']
        if not self.__chkExist(loanDict,reqs):
            msgString += "Insurance data missing. "

        # Check borrower roles
        for brwr in range(int(loanDict['Brwr.Number'])):
            if loanDict["Brwr"+str(brwr+1)+".Role"] == None:
                msgString += "Borrower role missing. "

        if msgString == "":
            return {"status":"Ok"}
        else:
            return {"status": "Error", "responseText":msgString }


    def generateLixiFile(self):

        loanDict={}
        filename=filename = self.filePath + str(self.opportunityId) + ".xml"

        self.__logging("Generating Lixi File for "+str(self.opportunityId))

        self.__logging("Step 1 - Extracting Salesforce Data to Loan Dictionary")
        loanDict = self.sfAPI.getLoanExtract(self.opportunityId)['data']


        self.loanId=loanDict['Loan.Loan_Number__c'] #Loan ID used later - hence instance variable

        self.__logging("Step 2 - Enriching and enumerating the Loan Dictionary")
        objEnrich = EnrichEnum(loanDict)
        result=objEnrich.enrich()
        if result['status']!="Ok":
            self.__logging(result['responseText'])
            return {'status': 'Error'}

        loanDict=result['data']

        loanDict["Loan.OriginatorMargin"]=self.LIXI_SETTINGS["ORIGINATOR_MARGIN"]

        self.__logging(" -  This is the final loan dictionary used to generate the LIXI file")
        self.__logging(" -  "+str(loanDict))

        self.__logging("Step 3 - Generating XML File")

        commentStr = str(
            "This file is for short-form loan ID {0}, short-form property ID {1} and with opportunity description {2}").format(
            loanDict['Loan.Name'], loanDict['Prop.Name'], loanDict['Opp.Name'])
        timestamp = time.strftime("%Y%m%d%H%M%S")

        self.__logging(" -  Creating XML Structure")
        lixiFile = LixiXMLGenerator(self.LIXI_SETTINGS, 'Yes', "HHC-" + str(timestamp), "HHC-" + loanDict['Opp.Id'], commentStr, filename)

        self.__logging(" -  Populating Elements")
        result=lixiFile.populateElements(loanDict)
        if result['status']=='Error':
            self.__logging(result['responseText'])
            return {'status':'Error'}

        self.__logging(" -  Creating File")

        result=lixiFile.CreateFile()
        if result['status']=='Error':
            self.__logging(result['responseText'])
            return {'status':'Error'}

        self.__logging("Step 4 - Validating XML File against Schema")
        isValid = lixiFile.ValidateXML(filename, self.schemaFilename)
        if isValid['status']=='Error':
            self.__logging(isValid['responseText'])
            return {'status':'Error'}

        self.__logging("File Generated and Validated")

        return {'status':'Ok','data':filename}

    def sendToAMAL(self, filename, sendFiles):

        identifier=""
        AMAL_LoanId=""
        self.__logging('Step 5 - Checking file with AMAL Schema Validator')
        isValid=self.mlAPI.checkLixiFile(filename)
        if isValid['status']!="Ok":
            self.__logging(isValid['responseText'])
            return {'status': 'Error'}

        if sendFiles:
            self.__logging('Step 6 - Sending Lixi file to AMAL')
            result=self.mlAPI.sendLixiFile(filename)
            if result['status'] == 'Error':
                self.__logging(result['responseText'])
                return {'status': 'Error'}
            return result
        else:
            self.__logging('Step 6 - By-passed - not sent to AMAL')
            return {"status":"Ok"}

    def saveAMALLoanId(self,oppID, AMAL_LoanId, isProduction):

        if not isProduction:
            self.__logging('Step 7 - By-passed - AMAL ID not saved in SF')
            return {"status": "Ok"}
        else:
            self.__logging('Step 7 - Saving AMAL ID in SF Loan Record')

            try:
                result=self.sfAPI.updateLoanID(oppID,AMAL_LoanId)
                if result['status']=="Ok":
                    self.__logging(" -  Saved " + AMAL_LoanId + " to Opportunity " + oppID)
                    return {"status":"Ok"}
                else:
                    self.__logging(" -  Warning: LoanId not updated in Salesforce")
                    self.__logging(result['responseText'])
                    return {"status": "Error"}
            except:
                self.__logging(" -  Warning: LoanId not updated in Salesforce")
                return {"status": "Error"}


    def sendDocumentsToAMAL(self, applicationID):

        docList=self.sfAPI.getDocumentList(self.opportunityId)['data']

        for index, row in docList.iterrows():

            if row["Name"] in self.AMAL_Documents:

                for attempt in range(2):
                    #Try sending three times
                   result = self.__sendDocument(row, applicationID)
                   if result['status'] == "Ok":
                       break

                if result['status'] != "Ok":
                    return result

        return {'status': "Ok"}

    
    def __sendDocument(self, row, applicationID ):
        srcfileIO = self.sfAPI.getDocumentFileStream(row["Id"])

        if srcfileIO['status'] != "Ok":
            return {'status': "Error", 'responseText': 'Did not retrieve ' + row["Name"]}

        try:
            status = self.mlAPI.sendDocuments(srcfileIO['data'], str(row["Name"]) + ".pdf", applicationID)
            if json.loads(status.text)['status'] != 'ok':
                return {'status': "Error", 'responseText': 'Error sending ' + row["Name"] + " to AMAL " + status.text}

        except:

            return {'status': "Error", 'responseText': 'Error sending ' + row["Name"] + " to AMAL"}

        return {'status': "Ok"}


    def __chkExist(self, sourceDict, reqFieldList):
        exists = True
        for item in reqFieldList:
            if sourceDict[item] == None or sourceDict[item] == "":
                exists = False
        return exists

    def __logging(self,string):
        self.outputLog+=string+"\r\n"