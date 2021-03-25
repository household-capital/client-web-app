#Python Imports
import logging
import os
import io
import json
import base64
from datetime import datetime

from collections import OrderedDict

#Application Imports
from apps.lib.site_Logging import write_applog

#Third-party Imports
from pandas import DataFrame
from simple_salesforce import Salesforce, SalesforceMalformedRequest, SalesforceGeneralError

class apiSalesforce():
    """Simple-Salesforce Wrapper"""


    qryDefinitions = {'OpportunityRef':
                          "Select ConvertedOpportunityId from Lead where Id=\'{0}\'",
                      'LoanRef':
                          "Select Loan_Number__c from Opportunity where Id=\'{0}\'",
                      'Opportunities':
                          "Select Id,Name,StageName,CloseDate from Opportunity where RecordType.Name != \'Distribution\' and StageName=\'Loan Approved\' and isDeleted=False",
                      'Opportunity':
                          "Select Id,Name,StageName,CloseDate, OwnerId, Establishment_Fee_Percent__c from Opportunity where Id=\'{0}\'",
                      'OpportunityPropertyLink':
                          "Select Property__c from OpportunityPropertyLink__c where Opportunity__c=\'{0}\'",
                      'Properties':
                          "Select Id, Name, Street_Address__c, Street_Name__c, Street_Number__c, Street_Type__c, Unit__c, Gnaf_id__c, Suburb_City__c,State__c,Postcode__c,Country__c, Property_Type__c, Last_Valuation_Date__c, Home_Value_AVM__c, Home_Value_FullVal__c, Valuer__c, Valuer_Name__c, Insurer__c, Policy_Number__c, Minimum_Insurance_Value__c, Insurance_Expiry_Date__c  from Properties__c where Id=\'{0}\' and isDeleted=False",
                      'OpportunityDetails':
                          "Select Loan_Number__c,Name, Interest_Type__c,Establishment_Fee__c, Planned_Establishment_Fee__c, Interest_Rate__c, Loan_Settlement_Date__c, Protected_Equity_Percent__c, Distribution_Partner_Contact__c, Total_Household_Loan_Amount__c, Total_Plan_Amount__c from Opportunity where Id=\'{0}\' and isDeleted=False",
                      'Purposes':
                          "Select Name, Category__c, Description__c, Intention__c, Amount__c from Purpose__c where Opportunity__c=\'{0}\' and isDeleted=False",
                      'Purpose':
                          "Select Name, Category__c, Description__c, Intention__c, Amount__c from Purpose__c where Name=\'{0}\' and isDeleted=False",
                      'OppRoles':
                          "Select OpportunityId, ContactId, Role from OpportunityContactRole where OpportunityId=\'{0}\' and isDeleted=False",
                      'Contacts':
                          "Select Id,FirstName, MiddleName, LastName, Phone,MobilePhone, Email, Birthdate__c, Age__c, Gender__c, Permanent_Resident__c, Salutation, Marital_Status__c, Country_of_Citizenship__c from Contact where Id=\'{0}\' and isDeleted=False",
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
                          "Select Id, Username, Firstname, Lastname from User where Id=\'{0}\'",
                      'LeadByEmail':
                          "Select Id, PostalCode from Lead where Email=\'{0}\'",
                      'LeadByPhone':
                          "Select Id, PostalCode from Lead where Phone=\'{0}\'",
                      'StageList':
                          "Select Id, Name, StageName from Opportunity where RecordType.Name != \'Distribution\'",
                      'AmountCheckList':
                           "Select Id, Total_Household_Loan_Amount__c, Total_Plan_Amount__c, Establishment_Fee_Percent__c from Opportunity where Lead_Record_Type__c = 'Household' and StageName in ('Meeting Held', 'Application Sent', 'Build Case', 'Assess')",

                      'LoanObjectList':
                           "Select Id, Status__c, Name, LoanNumber__c, Total_Loan_Amount__c, Total_Limits__c, Total_Establishment_Fee__c, Establishment_Fee_Percent__c, Total_Plan_Purpose_Amount__c, TotalPlanAmount__c, TotalPlanEstablishmentFee__c, Mortgage_Number__c, Account_Number__c, BSB__c from Loan__c where Status__c != \'Inactive\'",

                      'LoanLinkList':
                            "select Loan__c, Opportunity__c from LoanOpportunityLink__c order by CreatedDate",

                      'LoanLink':
                          "Select Loan__c from LoanOpportunityLink__c where Opportunity__c=\'{0}\'",

                      'LoanObjectDetails':
                           "Select LoanNumber__c from Loan__c where Id =\'{0}\'",

                      'LoanObjectRoles':
                            "Select Id, Name, Loan__c, Contact__c, Role__c from LoanContactRole__c",

                      'LoanObjectContacts':
                            "Select Id, Salutation, FirstName, MiddleName, PreferredName__c, LastName, Birthdate__c, Gender__c, Marital_Status__c, MailingStreet, MailingCity, MailingPostalCode, MailingStateCode, Phone, MobilePhone, Email from Contact" ,

                      'LoanObjectProperties':
                            "Select Id, Street_Address__c, Suburb_City__c, State__c, Postcode__c, Property_Type__c, Insurer__c, Policy_Number__c, Insurance_Expiry_Date__c, Minimum_Insurance_Value__c, Home_Value_FullVal__c, Valuer__c, Valuer_Name__c, Last_Valuation_Date__c from Properties__c",

                      'LoanObjectPropertyLink':
                            "Select Id, Name, Loan__c, Property__c from LoanPropertyLink__c",

                      'LoanObjectPurposes':
                            "select Id, Category__c, Amount__c, Description__c, Drawdown_Amount__c, Drawdown_Frequency__c, Intention__c, Loan__c, Name, Notes__c, Plan_Amount__c, Plan_Period__c, TopUp_Buffer__c, Contract_Drawdowns__c, Plan_Drawdowns__c, Active__c from Loan_Limit__c",

                      'Notes':
                          "Select ContentDocumentId from ContentNote where LinkedEntityId=\'{0}\'",

                      }


    def openAPI(self,production):

        if production == True:
            ENV_STR = '_PROD'
        else:
            ENV_STR = '_UAT'

        try:
            # Open API connection to SF and retrive session token (handled by simple-salesforce)
            if production == True:
                extra_kwargs = {}
                if os.environ.get('ENV') != 'prod': 
                    extra_kwargs['domain'] = "test"
                self.sf = Salesforce(username=os.getenv("SALESFORCE_USERNAME" + ENV_STR),
                                     password=os.getenv("SALESFORCE_PASSWORD" + ENV_STR),
                                     security_token=os.getenv("SALESFORCE_TOKEN" + ENV_STR),
                                     version='48.0', **extra_kwargs)
            else:

                self.sf = Salesforce(username=os.getenv("SALESFORCE_USERNAME" + ENV_STR),
                                     password=os.getenv("SALESFORCE_PASSWORD" + ENV_STR),
                                     security_token=os.getenv("SALESFORCE_TOKEN" + ENV_STR),
                                     domain="test",
                                     version='48.0')

            write_applog("INFO", 'apiSalesforce', 'openAPI', "Salesforce API Opened")
            return {'status':"Ok"}

        except Exception as e:
            errorStr = 'API Error: Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e))
            write_applog("ERROR", 'apiSalesforce', 'openAPI', errorStr)

            return {'status':"Error", 'responseText':errorStr}


    # Core Query Utilities

    def qryToDict(self,qryName,qryParameter,prefix):

        responseDict={}
        #Utility function to build output dictionary from query results
        results = self.execSOQLQuery(qryName, qryParameter) # Get dataframe with qry results

        if results['status']!="Error":
            for i, row in results['data'].iterrows(): #Iterate over table using inbuilt generators
                for j, column in row.iteritems():
                    responseDict[prefix + "." + j] = column #Store results in dictionary with prefix added to field name
            return {'status':'Ok','data':responseDict}
        else:
            return {'status': 'Ok', 'data': None}


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
            return {'status':'Error', 'responseText':errorStr}

        isDone=qryResult['done']
        resultsTable=DataFrame(qryResult['records']) #Import results into a pandas DataFrame for easier manipulation

        # API returns results in batches (for large results, need to keep calling until done
        while isDone!= True:
            qryResult=self.sf.query_more(qryResult['nextRecordsUrl'],True)
            resultsTable = resultsTable.append(DataFrame(qryResult['records']))
            isDone=qryResult['done']

        if len(resultsTable.index)!=0:  #is not empty
            #qryResults are returned will full type attributes, drop these for easier manipulation
            resultsTable=resultsTable.drop('attributes',axis=1)

        return {'status':'Ok', 'data':resultsTable, 'rows':len(resultsTable.index)}


    def apexCall(self, callUrl, method="GET", data=None):

        apexUrl = self.sf.apex_url
        fullUrl = apexUrl + callUrl
        if data:
            data = json.dumps(data)

        try:
            response = self.sf._call_salesforce(method=method, url=fullUrl, data=data )
        except SalesforceGeneralError as err:
            return {'status':'Error', 'responseText':err.content}

        if response.status_code != 200:
            return {'status': 'Error', "responseText": json.loads(response.content)}
        else:
            return {'status': 'Ok', "responseText": json.loads(response.content)}


    # SF Create / Update / Workflow

    def createEnquiry(self, enqDict):
        try:
            result=self.sf.Enquiry__c.create(enqDict)
            return {'status':'Ok','data':result}
        except SalesforceMalformedRequest as err:
            return {'status':'Error', 'responseText':err.content[0]}
        except:
            return {'status':'Error','responseText':'Unknown' }

    def updateEnquiry(self, enqID, enqDict):
        try:
            result=self.sf.Enquiry__c.update(enqID, enqDict)
            return {'status':'Ok','data':result}

        except SalesforceMalformedRequest as err:
            return {'status':'Error', 'responseText':err.content[0]}
        except:
            return {'status':'Error','responseText':'Unknown' }

    def createLead(self,leadDict):

        try:
            result=self.sf.Lead.create(leadDict)
            return {'status':'Ok','data':result}

        except SalesforceMalformedRequest as err:
            return {'status':'Error', 'responseText':err.content[0]}
        except:
            return {'status':'Error','responseText':'Unknown' }


    def updateLead(self,leadID,leadDict):
        try:
            result=self.sf.Lead.update(leadID,leadDict)
            return {'status':'Ok','data':result}

        except SalesforceMalformedRequest as err:
            return {'status':'Error', 'responseText':err.content[0]}
        except:
            return {'status':'Error','responseText':'Unknown' }

    def updateOpportunity(self,opportunityID,oppDict):
        try:
            result=self.sf.Opportunity.update(opportunityID,oppDict)
            return {'status':'Ok','data':result}

        except SalesforceMalformedRequest as err:
            return {'status':'Error', 'responseText':err.content[0]}
        except:
            return {'status':'Error','responseText':'Unknown' }

    def getLead(self, leadID):
        try:
            result = self.sf.Lead.get(leadID)
            return {'status': 'Ok', 'data': result}

        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}

        except:
            return {'status': 'Error', 'responseText': 'Unknown'}

    def updateLoanID(self, oppID, AMAL_loanId):
        '''Update LoanID on Opportunity and Loan Object'''
        if len(oppID)<5 or len(AMAL_loanId)<5:
            return {'status':'Error' , "responseText":"ID not valid"}
        else:
            #Update Opportunity
            self.sf.Opportunity.update(oppID,{"Loan_ID__c": AMAL_loanId})

            #Update Loan Object
            loanObj = self.qryToDict('LoanLink', oppID, "Loan")['data']

            if loanObj:
                loanID = loanObj['Loan.Loan__c']
                self.sf.Loan__c.update(loanID, {"Status__c": "Active",
                                                "Mortgage_Number__c": AMAL_loanId,
                                                "Date_Lixi_Sent__c": datetime.now().strftime("%Y-%m-%d")})
        return {'status':'Ok' }


    def updateOpportunity(self, oppID, oppDict):
        try:
            result = self.sf.Opportunity.update(oppID, oppDict)
            return {'status': 'Ok', 'data': result}

        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}
        except:
            return {'status': 'Error', 'responseText': 'Unknown'}


    def updateLoan(self, loanID, loanDict):
        try:
            result = self.sf.Loan__c.update(loanID, loanDict)
            return {'status': 'Ok', 'data': result}

        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}
        except:
            return {'status': 'Error', 'responseText': 'Unknown'}

    def createTask(self, OwnerId, ActivityDate, Subject, Priority = 'Normal', Status='Open', Description=None, WhatId=None, WhoId=None):

        payload={
            'OwnerId': OwnerId,
            'ActivityDate': ActivityDate,
            'Subject': Subject,
            'Priority': Priority,
            'Status': Status,
            'Description': Description,
            'WhatId': WhatId,
            'WhoId': WhoId,
        }

        try:
            result = self.sf.Task.create(payload)
            return {'status': 'Ok', 'data': result}

        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}
        except SalesforceGeneralError as err:
            return {'status': 'Error', 'responseText': err.content[0]}

    def createNote(self, parent_sfid, note):
        content = '<p>' + note.comment.replace('\n','</p><p>') + '</p>'
        content = base64.b64encode(content.encode('ascii')).decode('ascii')

        payload = {
            'Content': content,
            'Title': 'Note from ' + note.user_name,
        }
        if note.user and note.user.profile.salesforceID:
            payload['OwnerId'] = note.user.profile.salesforceID

        try:
            result = self.sf.ContentNote.create(payload)
        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}
        except:
            return {'status': 'Error','responseText': 'Unknown'}

        payload = {
            'ContentDocumentId': result['id'],
            'LinkedEntityId': parent_sfid,
        }
        try:
            result2 = self.sf.ContentDocumentLink.create(payload)
        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}
        except:
            return {'status': 'Error','responseText': 'Unknown'}

        note.sf_id = result['id']
        note.save()

        return {'status': 'Ok', 'data': result}

    def deleteNote(self, note):
        try:
            result = self.sf.ContentNote.delete(note.sf_id)
            return {'status': 'Ok', 'data': result}
        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}
        except:
            return {'status': 'Error', 'responseText': 'Unknown'}

    def syncNotes(self, parent_sfid, notes):
        try:
            soql = "Select ContentDocumentId from ContentDocumentLink where LinkedEntityId=\'{0}\'".format(parent_sfid)
            soql = soql.encode('unicode_escape') # Need to escape the "" in the SQL statement

            raw_list = self.sf.query_all(soql)

            sf_note_sfids = [record['ContentDocumentId'] for record in raw_list['records']]
            ca_note_sfids = [note.sf_id for note in notes]

            write_applog("INFO", 'apiSalesforce', 'syncNotes', "sf_note_sfids = " + json.dumps(sf_note_sfids))
            write_applog("INFO", 'apiSalesforce', 'syncNotes', "ca_note_sfids = " + json.dumps(ca_note_sfids))

            for note in notes:
                write_applog("INFO", 'apiSalesforce', 'syncNotes', "processing note %d" % note.id)
                if note.is_removed:
                    write_applog("INFO", 'apiSalesforce', 'syncNotes', "note marked for removal")
                    if not note.sf_id:
                        write_applog("INFO", 'apiSalesforce', 'syncNotes', "No SFID - skipping")
                        pass
                    elif note.sf_id in sf_note_sfids:
                        write_applog("INFO", 'apiSalesforce', 'syncNotes', "In SF - Deleting...")
                        self.deleteNote(note)
                    else:
                        write_applog("INFO", 'apiSalesforce', 'syncNotes', "Not in SF - skipping")
                        pass
                else:
                    write_applog("INFO", 'apiSalesforce', 'syncNotes', "note marked for keeping")
                    if not note.sf_id:
                        write_applog("INFO", 'apiSalesforce', 'syncNotes', "No SFID - adding")
                        self.createNote(parent_sfid, note)
                    elif note.sf_id in sf_note_sfids:
                        write_applog("INFO", 'apiSalesforce', 'syncNotes', "In SF - skipping")
                        pass
                    else:
                        # need to be restored
                        write_applog("INFO", 'apiSalesforce', 'syncNotes', "Not in SF - restoring")
                        self.createNote(parent_sfid, note)

                # FIX ME - this isn't working yet, it isn't hitting an error, but no delete applying in SF.
                # possibly just an issue with the Type of the sf_id? some issue with string types?
                #for sfid in sf_note_sfids:
                #    if sfid not in ca_note_sfids:
                #        print('deleting')
                #        self.sf.ContentNote.delete(sfid)
            return {'status': 'Ok'}
        except SalesforceMalformedRequest as err:
            return {'status': 'Error', 'responseText': err.content[0]}
        except:
            write_applog("ERROR", 'apiSalesforce', 'syncNotes', "", is_exception=True)
            return {'status': 'Error', 'responseText': 'Unknown'}






    # SF Opportunity Extract

    def getOpportunityExtract(self,OpportunityID):

        #returns full extract dictionary for specific opportunityID
        logging.info("         Making multiple SOQL calls to produce dictionary")
        loanDict={}

        loanDict.update(self.qryToDict('Opportunity', OpportunityID, 'Opp')['data'])

        print(self.qryToDict('OpportunityPropertyLink', OpportunityID,'Prop'))
        propertyID = self.qryToDict('OpportunityPropertyLink', OpportunityID,'Prop')['data']['Prop.Property__c']

        loanDict.update(self.qryToDict('Properties', propertyID, 'Prop')['data'])

        loanDict.update(self.qryToDict('OpportunityDetails', OpportunityID, 'Loan')['data'])

        loanDict.update(self.qryToDict('User',loanDict['Opp.OwnerId'],'User')['data'])


        if 'Loan.Distribution_Partner_Contact__c' in loanDict:
            if loanDict['Loan.Distribution_Partner_Contact__c']!=None:
                loanDict.update(self.qryToDict('DistContact', loanDict['Loan.Distribution_Partner_Contact__c'], 'Dist')['data'])
                loanDict.update(self.qryToDict('DistCompany', loanDict['Dist.AccountId'], 'Dist')['data'])

        # Nested loop - multiple purposes
        results = self.execSOQLQuery('Purposes', OpportunityID)
        loanDict['Purp.NoPurposes'] = results['rows']
        for  index, row in results['data'].iterrows():
            loanDict.update(self.qryToDict('Purpose', row['Name'], "Purp" + str(index+1) )['data'])

        #Nested loop - multiple borrowers

        results = self.execSOQLQuery('OppRoles', OpportunityID)

        borrowerCount=0
        poaCount=0
        for  index, row in results['data'].iterrows():
            if row['Role'] is None:
                return {'status': "Error", 'responseText' : "No Role set" }

            if "Borrower" in row['Role']:
                borrowerCount+=1
                loanDict["Brwr" + str(borrowerCount)+".Role"]=row['Role']
                loanDict.update(self.qryToDict('Contacts', row['ContactId'], "Brwr" + str(borrowerCount)) ['data'])
            if "Attorney" in row['Role']:
                poaCount +=1
                loanDict["POA" + str(poaCount) + ".Role"] = row['Role']
                loanDict.update(self.qryToDict('Contacts', row['ContactId'], "POA" + str(poaCount))['data'])

        loanDict['Brwr.Number'] = borrowerCount
        loanDict['POA.Number'] = poaCount


        #Get LoanObjectID (Using Opportunity Link Table)
        loanObj = self.qryToDict('LoanLink', OpportunityID, "Loan")['data']
        if loanObj:
            loanDict['LoanObject.SFID'] = loanObj['Loan.Loan__c']
            loanObj = self.qryToDict('LoanObjectDetails',loanDict['LoanObject.SFID'], "Loan")['data']
            loanDict['LoanObject.LoanNumber'] = loanObj['Loan.LoanNumber__c']

        return {'status':"Ok", "data":loanDict}


    def getApprovedLoans(self):
        #returns a list of Approved Loans
        appLoans=self.execSOQLQuery('Opportunities',None)
        return appLoans

    def getDocumentList(self,OpportunityID):
        # returns a list of documents that have been loaded against an OpportunityID
        appLoans = self.execSOQLQuery('Documents', OpportunityID)
        return appLoans

    def getStageList(self):
        #returns a list of stages by sfLoanID
        stageList = self.execSOQLQuery('StageList', None)
        return stageList

    def getAmountCheckList(self):
        #returns a list of stages by sfLoanID
        amountList = self.execSOQLQuery('AmountCheckList', None)
        return amountList


    # Loan Object Extract

    def getLoanObjList(self):
        # returns a list of LoanObjs (excluding inactive)
        list = self.execSOQLQuery('LoanObjectList', None)
        return list

    def getLoanLinkList(self):
       #returns list of LoanObjData
       list = self.execSOQLQuery('LoanLinkList', None)
       return list

    def getLoanObjRoles(self):
        # returns a list of Loan Object Roles
        list = self.execSOQLQuery('LoanObjectRoles', None)
        return list

    def getLoanObjContacts(self):
        # returns a list of Loan Obect Contacts
        list = self.execSOQLQuery('LoanObjectContacts', None)
        return list

    def getLoanObjProperties(self):
        # returns a list of Loan Object Properties
        list = self.execSOQLQuery('LoanObjectProperties', None)
        return list

    def getLoanObjPropertyLinks(self):
        # returns a list of Loan Object Property Links
        list = self.execSOQLQuery('LoanObjectPropertyLink', None)
        return list

    def getLoanObjPurposes(self):
        # returns a list of Loan Object Purposes
        list = self.execSOQLQuery('LoanObjectPurposes', None)
        return list


    # Document Extract

    def getDocumentFileStream(self, documentID):
        # Multi-call approach as SF has restrictions on calling the link table

        contentID=self.__getContentDocumentID(documentID)

        if not contentID:
            return {'status':'Error', 'responseText':"Couldn't find content ID"}

        fileUrl=self.__getFileUrl(contentID)

        # Work-around as simple_salesforce Restful call attempts to JSON decode response
        # This approach uses simple_salesforce utilities to make a direct call and return response

        baseUrl = self.sf.base_url
        fullUrl=baseUrl + fileUrl[-54:]
        response = self.sf._call_salesforce(method="GET", url=fullUrl)

        if response.status_code!=200:
            return {'status': 'Error', 'responseText': "Invalid URL"}
        else:
            return {'status': 'Ok', 'data': io.BytesIO(response.content)}


    # Class Utilities

    def updateLoanData(self,sfID,srcDict):
        for item, value in srcDict.items():
            self.sf.Loan__c.update(sfID, {item: value})
        return {'status': 'Ok'}

    def setResultsPrefix(self, prefix):
        self.resultsPrefix=prefix


    def __getContentDocumentID(self,LinkID):
        #returns link ID to Content Version table
        docLink=self.execSOQLQuery('DocumentLink', LinkID)
        if docLink['rows']==0:
            return None
        else:
            return str(docLink['data'].iloc[0]["ContentDocumentId"])

    def __getFileUrl(self,ContentDocumentID):
        #returns URL
        Url=self.execSOQLQuery('ContentVersion', ContentDocumentID)
        if Url['rows']==0:
            return None
        else:
            return str(Url['data'].iloc[0]["VersionData"])


