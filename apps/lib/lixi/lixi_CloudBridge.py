#Python Imports
import time
import json
import logging
import os

#Django Imports
from django.conf import settings

#Third-party Imports

#Application Imports
from apps.lib.api_AMAL import apiAMAL
from apps.lib.api_Salesforce import apiSalesforce
from .lixi_EnrichEnum import EnrichEnum
from .lixi_Generator import LixiXMLGenerator
from apps.lib.site_Globals import ECONOMIC



class CloudBridge():

    LIXI_SETTINGS = {'LIXI_VERSION': '2.6.17',
                     'SCHEMA_FILENAME': "/apps/lib/lixi/LixiSchema/LIXI-CAL-2.6.17".replace(".", "_") + '.xsd',
                     'ORIGINATOR_MARGIN': ECONOMIC['lendingMargin'],
                     'ns_map_':{"xsi": 'http://www/w3/org/2001/XMLSchema-instance'},
                     'FILEPATH':(settings.MEDIA_ROOT+'/CustomerReports/'),
                     'AMAL_DOCUMENTS':["Application Form", "Loan Contract", "Valuation Report"]
                     }

    def __init__(self, opportunityId, isSendFiles, isProdSF, isProdAMAL):

        self.schemaFilename=self.LIXI_SETTINGS['SCHEMA_FILENAME']
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
            return {'status': "Error", 'responseText': "Could not connect to Salesforce"}

        return {'status': "Ok", 'responseText': "Bridge Established"}


    def extractAndSend(self):

        filename=""
        AMAL_LoanId=""
        identifier=""

        #Generate Lixi File
        try:
            result = self.generateLixiFile()
            if result['status']!="Ok":
                return {'status': "Error", 'responseText': "Unhandled Error", 'log': self.outputLog}
        except:
            return {'status': "Error", 'responseText': "Unhandled Error", 'log':self.outputLog}

        filename=result['data']

        # Submit Lixi File
        try:
            result = self.sendToAMAL(filename, self.isSendFiles)
        except:
            return {'status': "Error", 'responseText': "Unhandled Error", 'log': self.outputLog}

        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': 'Submit Error', 'log': self.outputLog}

        if self.isSendFiles:
            identifier = result['data']['identifier']
            AMAL_LoanId = result['data']['loanID']

        # Update Salesforce with LoanId
        result = self.saveAMALLoanId(self.loanId, AMAL_LoanId, self.isProduction)
        if result['status'] != 'Ok':
            self.warningLog += 'ARN not saved in Salesforce' + "\r\n"

        # Send supporting Documents
        try:
            result=self.sendDocumentsToAMAL(identifier, self.isSendFiles)
            if result['status'] != 'Ok':
                self.warningLog += 'Suporting docs not sent to AMAL' + "\r\n"

        except:
            self.warningLog+='Suporting docs not sent to AMAL'

        print(self.outputLog)
        self.__logging("Cloud Bridge's work is done here")
        return {'status': "Ok", 'responseText': "Cloud Bridge's work is done here", 'log': self.outputLog,'warningLog':self.warningLog}


    def getSFLoanList(self):
        #Returns a DataFrame of all approved loans from Salesforce
        self.__logging("Extracting approved Loans from Saleforce")

        loanList = self.sfAPI.getApprovedLoans()

        self.__logging(str(len(loanList.index)) + " approved loans returned")
        return loanList

    def generateLixiFile(self):

        loanDict={}
        filename=""

        self.__logging("Generating Lixi File for "+str(self.opportunityId))

        self.__logging("Step 1 - Extracting Salesforce Data to Loan Dictionary")
        loanDict = self.sfAPI.getLoanExtract(self.opportunityId)

        self.loanId=loanDict['Loan.Loan_Number__c'] #Loan ID used later - hence instance variable

        filename = self.filePath+str(self.opportunityId)+".xml"

        self.__logging("Step 2 - Enriching and enumerating the Loan Dictionary")
        objEnrich = EnrichEnum(loanDict,filename.replace("xml","txt"))
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

    def saveAMALLoanId(self,loanId, AMAL_LoanId, isProduction):

        if not isProduction:
            self.__logging('Step 7 - By-passed - AMAL ID not saved in SF')
            return {"status": "Ok"}
        else:
            self.__logging('Step 7 - Saving AMAL ID in SF Loan Record')

            try:
                self.sfAPI.updateLoanID(loanId,AMAL_LoanId)
                self.__logging(" -  Saved " + AMAL_LoanId + " to Loan " + loanId)
                return {"status":"Ok"}

            except:
                self.__logging(" -  Warning: LoanId not updated in Salesforce")
                return {"status": "Error"}


    def sendDocumentsToAMAL(self, applicationID,sendFiles):

        if sendFiles:
            self.__logging('Step 8 - Retrieving documents from Salesforce and Sending to AMAL')
        else:
            self.__logging('Step 8 - Retrieving documents from Salesforce - Not Sent to AMAL')

        docList=self.sfAPI.getDocumentList(self.opportunityId)

        for index, row in docList.iterrows():

            print(row["Name"])
            if row["Name"] in self.AMAL_Documents:

                self.__logging('         Retrieving '+row["Name"])
                srcfileIO=self.sfAPI.getDocumentFileStream(row["Id"])

                if sendFiles:
                    self.__logging('         Sending '+row["Name"])
                    status=self.mlAPI.sendDocuments(srcfileIO, str(row["Name"])+".pdf", applicationID)

                    if json.loads(status.text)['status']!='ok':
                        self.__logging('         Error sending ' + row["Name"]+ "to AMAL")
                        self.__logging(status.text)
                        return {'status':"Error"}
        return {'status': "Ok"}

    def __nuke(self):
        response=self.mlAPI.nuke()
        print(response)
        
    def __logging(self,string):
        self.outputLog+=string+"\r\n"