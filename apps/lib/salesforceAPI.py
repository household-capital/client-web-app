#Python Imports
import logging
import io
import os

#Third-party Imports
from pandas import DataFrame
from simple_salesforce import Salesforce, SalesforceMalformedRequest

class apiSalesforce():

    qryDefinitions={'OpportunityRef':
                        "Select ConvertedOpportunityId from Lead where Id=\'{0}\'",

                    'LoanRef':
                        "Select Name from Loan__c where Opportunity__c=\'{0}\'"

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

    def createResultsTask(self,objectID,subject,status,description,owenerID):

        payload={'WhatId':objectID,
                 'Subject':subject,
                 'Status':status,
                 'OwnerId':'0052P000000JbVjQAK',
                 'Description':description}
        result=self.sf.Task.create(payload)
        return result

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

