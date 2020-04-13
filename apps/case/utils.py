# Python Imports
import datetime
import json
import base64
import os
import pathlib

# Django Imports
from django.contrib import messages
from django.forms.models import model_to_dict


from apps.lib.site_Logging import write_applog
from apps.lib.site_DataMapping import mapFacilityToCase
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Enums import roleEnum, caseStagesEnum, loanTypesEnum, appTypesEnum, clientTypesEnum, channelTypesEnum
from apps.case.models import Case, Loan, ModelSetting, LoanPurposes



def createLoanVariation(facilityObj, accruedInterest):

    # 1. Creaet New Case Object

    payload = mapFacilityToCase(facilityObj)

    try:
        newCaseObj = Case.objects.create(**payload)
    except:
        return {'status': "Error", 'responseText':'Could not create variation'}


    ## TEMPORARY APPROACH UNTIL SF OBJECTS UPDATED ##

    orgCaseUID = str(facilityObj.originalCaseUID)

    # 2. Case Loan Object
    orgLoanObj = Loan.objects.queryset_byUID(orgCaseUID).get()
    orgLoanDict = model_to_dict(orgLoanObj, exclude=['case', 'localLoanID'])
    orgLoanDict['accruedInterest'] = int(accruedInterest)

    Loan.objects.filter(case=newCaseObj).update(**orgLoanDict)
    newLoanObj = Loan.objects.filter(case=newCaseObj).get()

    # 3. Case ModelSetting Object
    orgSettingsObj = ModelSetting.objects.queryset_byUID(orgCaseUID).get()
    orgSettingsDict = model_to_dict(orgSettingsObj, exclude=['case', 'id'])

    ModelSetting.objects.filter(case=newCaseObj).update(**orgSettingsDict)

    #4. Create Purposes
    orgPurposesQs = LoanPurposes.objects.filter(loan=orgLoanObj)
    for purpose in orgPurposesQs:
        orgPurposeDict = model_to_dict(purpose, exclude=['loan', 'purposeID', 'purposeUID'])
        orgPurposeDict['loan'] = newLoanObj
        LoanPurposes.objects.create(**orgPurposeDict)

    # 5. Create SF Opportunity
    end_point = 'CreateLoanVariation/v1/'
    end_point_method = 'POST'

    orgSfOpportunityID = Case.objects.queryset_byUID(orgCaseUID).get().sfOpportunityID

    payload = {"opportunityId": orgSfOpportunityID}

    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)

    result = sfAPI.apexCall(end_point, end_point_method, data=payload)


    if result['status'] != 'Ok':
        write_applog("Error", 'Case', 'createLoanVariation', 'Could not create variation - ' + json.dumps(result['responseText']))

    else:
        # Save response data
        newCaseObj.sfOpportunityID = result['responseText']['opportunityid']
        newCaseObj.sfLoanID = result['responseText']['loanNumber']
        newCaseObj.save()

    return {'status':'Ok', 'data':{'caseUID':str(newCaseObj.caseUID)}}