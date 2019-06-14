#Python Imports
import logging
import os
import io

#Application Imports
from apps.lib.site_Logging import write_applog

#Third-party Imports
from pandas import DataFrame
from simple_salesforce import Salesforce, SalesforceMalformedRequest

class apiSalesforce():

    qryDefinitions = {'OpportunityRef':
                          "Select ConvertedOpportunityId from Lead where Id=\'{0}\'",
                      'LoanRef':
                          "Select Loan_Number__c from Opportunity where Id=\'{0}\'",
                      'Opportunities':
                          "Select Id,Name,StageName,CloseDate from Opportunity where RecordType.Name=\'Household\' and StageName=\'Loan Approved\' and isDeleted=False",
                      'Opportunity':
                          "Select Id,Name,StageName,CloseDate, OwnerId, Establishment_Fee_Percent__c from Opportunity where Id=\'{0}\'",
                      'Properties':
                          "Select Id, Name, Street_Address__c,Suburb_City__c,State__c,Postcode__c,Country__c, Last_Valuation_Date__c, Home_Value_FullVal__c, Valuer__c, Valuer_Name__c, Insurer__c, Policy_Number__c, Minimum_Insurance_Value__c, Insurance_Expiry_Date__c  from Properties__c where Opportunity__c=\'{0}\' and isDeleted=False",
                      'Loan':
                          "Select Loan_Number__c,Name, Loan_Type__c, Interest_Type__c,Establishment_Fee__c, Interest_Rate__c, Settlement_Date__c, Protected_Equity_Percent__c, Distribution_Partner_Contact__c, Total_Household_Loan_Amount__c from Opportunity where Id=\'{0}\' and isDeleted=False",
                      'Purposes':
                          "Select Name, Category__c, Description__c, Intention__c, Amount__c from Purpose__c where Opportunity__c=\'{0}\' and isDeleted=False",
                      'Purpose':
                          "Select Name, Category__c, Description__c, Intention__c, Amount__c from Purpose__c where Name=\'{0}\' and isDeleted=False",
                      'OppRoles':
                          "Select OpportunityId, ContactId, Role from OpportunityContactRole where OpportunityId=\'{0}\' and isDeleted=False",
                      'Contacts':
                          "Select Id,FirstName, LastName, Phone,MobilePhone, Email, Birthdate__c, Age__c, Gender__c, Permanent_Resident__c, Salutation, Marital_Status__c, Country_of_Citizenship__c from Contact where Id=\'{0}\' and isDeleted=False",
                      'Documents':
                          "Select Id, Name, Status__c from Document__C where Opportunity__c=\'{0}\'",
                      'DocumentLink':
                          "Select contentDocumentId from ContentDocumentLink where LinkedEntityID=\'{0}\'",
                      'ContentVersion':
                          "Select VersionData from ContentVersion where ContentDocumentID=\'{0}\'",
                      'DistContact':
                          "Select FirstName, LastName, AccountId from Contact where Id=\'{0}\' and isDeleted=False",
                      'DistCompany':
                          "Select Name from Account where Id=\'{0}\' and isDeleted=False",
                      'User':
                          "Select Id, Username, Firstname, Lastname from User where Id=\'{0}\'"
                      }

    def openAPI(self,production):

        if production == True:
            ENV_STR = '_PROD'
        else:
            ENV_STR = '_DEV'

        try:
            # Open API connection to SF and retrive session token (handled by simple-salesforce)
            if production == True:
                self.sf = Salesforce(username=os.getenv("SALESFORCE_USERNAME" + ENV_STR),
                                     password=os.getenv("SALESFORCE_PASSWORD" + ENV_STR),
                                     security_token=os.getenv("SALESFORCE_TOKEN" + ENV_STR))
            else:
                self.sf = Salesforce(username=os.getenv("SALESFORCE_USERNAME" + ENV_STR),
                                     password=os.getenv("SALESFORCE_PASSWORD" + ENV_STR),
                                     security_token=os.getenv("SALESFORCE_TOKEN" + ENV_STR),
                                     domain="test")

            write_applog("INFO", 'apiSalesforce', 'openAPI', "Salesforce API Opened")
            return {'status':"Ok"}

        except Exception as e:
            errorStr = 'API Error: Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e))
            write_applog("ERROR", 'apiSalesforce', 'openAPI', errorStr)

            return {'status':"Error", 'responseText':errorStr}

    def qryToDict(self,qryName,qryParameter,prefix,targetDict):

        #Utility function to build output dictionary from query results
        results = self.execSOQLQuery(qryName, qryParameter) # Get dataframe with qry results
        for i, row in results.iterrows(): #Iterate over table using inbuilt generators
            for j, column in row.iteritems():
                targetDict[prefix + "." + j] = column #Store results in dictionary with prefix added to field name


    def execSOQLQuery(self,qryName,qryVariable=None):

        #Executes SOQL query using definitions dictionary and returns results in a Pandas DataFrame
        if qryVariable:
            soqlQryStr=self.qryDefinitions[qryName].format(qryVariable)
        else:
            soqlQryStr = self.qryDefinitions[qryName]

        soqlQuery=  soqlQryStr.encode('unicode_escape') # Need to escape the "" in the SQL statement

        try:
            qryResult=self.sf.query(soqlQuery)
        except Exception as e:
            errorStr = 'Query Error: Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e))
            write_applog("ERROR", 'apiSalesforce', 'execSOQLQuery', errorStr)
            return

        isDone=qryResult['done']
        resultsTable=DataFrame(qryResult['records']) #Import results into a pandas DataFrame for easier manipulation

        # API returns results in batches (for large results, need to keep calling until done
        while isDone!= True:
            qryResult=self.sf.query_more(qryResult['nextRecordsurl'],True)
            resultsTable = resultsTable.append(DataFrame(qryResult['records']))
            isDone=qryResult['done']

        if len(resultsTable.index)!=0:  #is not empty
            #qryResults are returned will full type attributes, drop these for easier manipulation
            resultsTable=resultsTable.drop('attributes',axis=1)

        return resultsTable


    def createLead(self,leadDict):

        try:
            result=self.sf.Lead.create(leadDict)
            return dict(result)

        except SalesforceMalformedRequest as err:
            responseDict=err.content[0]
            responseDict['success']=False
            return responseDict
        except:
            return {'success':False,'message':'Unknown' }

    def getLoanExtract(self,OpportunityID):

        #returns full extract dictionary for specific opportunityID
        logging.info("         Making multiple SOQL calls to produce dictionary")
        loanDict={}
        self.qryToDict('Opportunity', OpportunityID, 'Opp', loanDict)
        self.qryToDict('Properties', OpportunityID, 'Prop', loanDict)
        self.qryToDict('Loan', OpportunityID, 'Loan', loanDict)

        self.qryToDict('User',loanDict['Opp.OwnerId'],'User',loanDict)

        if loanDict['Loan.Distribution_Partner_Contact__c']!=None:
            self.qryToDict('DistContact', loanDict['Loan.Distribution_Partner_Contact__c'], 'Dist', loanDict)
            self.qryToDict('DistCompany', loanDict['Dist.AccountId'], 'Dist', loanDict)

        # Nested loop - multiple purposes
        results = self.execSOQLQuery('Purposes', OpportunityID)
        loanDict['Purp.NoPurposes'] = len(results.index)
        for  index, row in results.iterrows():
            self.qryToDict('Purpose', row['Name'], "Purp" + str(index+1), loanDict)

        #Nested loop - multiple borrowers

        results = self.execSOQLQuery('OppRoles', OpportunityID)

        borrowerCount=0
        poaCount=0
        for  index, row in results.iterrows():
            if "Borrower" in row['Role']:
                borrowerCount+=1
                loanDict["Brwr" + str(borrowerCount)+".Role"]=row['Role']
                self.qryToDict('Contacts', row['ContactId'], "Brwr" + str(borrowerCount), loanDict)
            if "Attorney" in row['Role']:
                poaCount +=1
                loanDict["POA" + str(poaCount) + ".Role"] = row['Role']
                self.qryToDict('Contacts', row['ContactId'], "POA" + str(poaCount), loanDict)

        loanDict['Brwr.Number'] = borrowerCount
        loanDict['POA.Number'] = poaCount

        #Work around - SF DB changes
        loanDict['Loan.Application_Amount__c']=loanDict["Loan.Total_Household_Loan_Amount__c"]

        return loanDict


    def getApprovedLoans(self):
        #returns a list of Approved Loans
        appLoans=self.execSOQLQuery('Opportunities',None)
        return appLoans

    def getDocumentList(self,OpportunityID):
        # returns a list of documents that have been loaded against an OpportunityID
        appLoans = self.execSOQLQuery('Documents', OpportunityID)
        return appLoans

    def getDocumentFileStream(self, documentID):
        # Multi-call approach as SF has restrictions on calling the link table

        contentID=self.__getContentDocumentID(documentID)

        fileUrl=self.__getFileUrl(contentID)

        # Work-around as simple_salesforce Restful call attempts to JSON decode response
        # This approach uses simple_salesforce utilities to make a direct call and return response

        baseUrl = self.sf.base_url
        fullUrl=baseUrl + fileUrl[-54:]
        response = self.sf._call_salesforce(method="GET", url=fullUrl)
        inMemoryFile = io.BytesIO(response.content)

        return inMemoryFile

    def updateLoanID(self, loanId, AMAL_loanId):

        if len(loanId)<5 or len(AMAL_loanId)<5:
            raise Exception
        else:
            self.sf.Loan__c.update(loanId,{"Loan_ID__c": AMAL_loanId})

    def setResultsPrefix(self, prefix):
        self.resultsPrefix=prefix

    def createResultsTask(self,opportunityID,success,log):

        if success:
            status='Completed'
            subject= self.resultsPrefix+' Success'
        else:
            status='Open'
            subject = self.resultsPrefix+ ' * Failure *'

        payload={'WhatId':opportunityID,
                 'Subject':subject,
                 'Status':status,
                 'OwnerId':'0052P000000JbVjQAK',
                 'Description':log}
        result=self.sf.Task.create(payload)
        return result


    def __getContentDocumentID(self,LinkID):
        #returns link ID to Content Version table
        docLink=self.execSOQLQuery('DocumentLink', LinkID)
        return str(docLink.iloc[0]["ContentDocumentId"])

    def __getFileUrl(self,ContentDocumentID):
        #returns URL
        Url=self.execSOQLQuery('ContentVersion', ContentDocumentID)
        return str(Url.iloc[0]["VersionData"])