#Python Imports
import logging
import io
import os

#Third-party Imports
from pandas import DataFrame
from simple_salesforce import Salesforce, SalesforceMalformedRequest

class apiSalesforce():

    qryDefinitions = {'OpportunityRef':
                          "Select ConvertedOpportunityId from Lead where Id=\'{0}\'",
                      'LoanRef':
                          "Select Name from Loan__c where Opportunity__c=\'{0}\'",
                      'Opportunities':
                          "Select Id,Name,StageName,CloseDate from Opportunity where RecordType.Name=\'Household\' and StageName=\'Loan Approved\' and isDeleted=False",
                      'Opportunity':
                          "Select Id,Name,StageName,CloseDate, OwnerId, Establishment_Fee_Percent__c from Opportunity where Id=\'{0}\'",
                      'Properties':
                          "Select Id, Name, Street_Address__c,Suburb_City__c,State__c,Postcode__c,Country__c, Property_Type__c, Last_Valuation_Date__c, Home_Value_FullVal__c, Home_Value_AVM__c, Valuer__c, Insurer__c, Policy_Number__c, Minimum_Insurance_Value__c  from Properties__c where Opportunity__c=\'{0}\' and isDeleted=False",
                      'Loan':
                          "Select Id,Name, Loan_Type__c, Interest_Type__c, NCCP__c,Application_Amount__c, Establishment_Fee__c, Interest_Rate__c, Settlement_Date__c, Protected_Equity_Percent__c, Distribution_Partner_Contact__c FROM Loan__c where Opportunity__c=\'{0}\' and isDeleted=False",
                      'Purposes':
                          "Select Name, Category__c, Description__c, Intention__c, Amount__c from Purpose__c where Opportunity__c=\'{0}\' and isDeleted=False",
                      'Purpose':
                          "Select Name, Category__c, Description__c, Intention__c, Amount__c from Purpose__c where Name=\'{0}\' and isDeleted=False",
                      'LoanRoles':
                          "Select Customer_Contact__c, Role__c from Loan_Contact_Role__c where Loan__c=\'{0}\' and isDeleted=False",
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

    def openAPI(self,password):
        logging.info("Opening Salesforce API")
        try:
            # Open API connection to SF and retrive session token (handled by simple-salesforce)
            self.sf = Salesforce(username=os.getenv("SALESFORCE_USERNAME"), password=password,
                                 security_token=os.getenv("SALESFORCE_TOKEN"))
            logging.info("API successfully opened")
            return True

        except Exception as e:
            errorStr = 'Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e))
            logging.critical(errorStr)
            return False

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
            errorStr = 'Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e))
            logging.critical(errorStr)
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
        results = self.execSOQLQuery('LoanRoles', loanDict['Loan.Id'])

        borrowerCount=0
        poaCount=0
        for  index, row in results.iterrows():
            if "Borrower" in row['Role__c']:
                borrowerCount+=1
                loanDict["Brwr" + str(borrowerCount)+".Role"]=row['Role__c']
                self.qryToDict('Contacts', row['Customer_Contact__c'], "Brwr" + str(borrowerCount), loanDict)
            if "Attorney" in row['Role__c']:
                poaCount +=1
                loanDict["POA" + str(poaCount) + ".Role"] = row['Role__c']
                self.qryToDict('Contacts', row['Customer_Contact__c'], "POA" + str(poaCount), loanDict)

        loanDict['Brwr.Number'] = borrowerCount
        loanDict['POA.Number'] = poaCount

        return loanDict

