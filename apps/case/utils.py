# Python Imports
import datetime
import json
import base64
import os
import pathlib

# Django Imports
from django.contrib import messages
from django.forms.models import model_to_dict

# Third-party Imports
from config.celery import app


from apps.lib.site_Logging import write_applog
from apps.lib.site_DataMapping import mapFacilityToCase
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Enums import roleEnum, caseStagesEnum, loanTypesEnum, appTypesEnum, clientTypesEnum, channelTypesEnum
from apps.case.models import Case, Loan, ModelSetting, LoanPurposes



def createLoanVariation(facilityObj):

    # 1. Create New Case Object

    payload = mapFacilityToCase(facilityObj)

    try:
        newCaseObj = Case.objects.create(**payload)
    except:
        return {'status': "Error", 'responseText':'Could not create variation'}


    ## TEMPORARY MIXED APPROACH UNTIL SF OBJECTS UPDATED ##

    orgCaseUID = str(facilityObj.originalCaseUID)

    # 2. Case Loan Object
    orgLoanObj = Loan.objects.queryset_byUID(orgCaseUID).get()
    orgLoanDict = model_to_dict(orgLoanObj, exclude=['case', 'localLoanID'])

    orgLoanDict['accruedInterest'] = int(max(facilityObj.currentBalance - facilityObj.advancedAmount, 0))
    orgLoanDict['orgTotalLoanAmount'] = facilityObj.totalLoanAmount
    orgLoanDict['orgPurposeAmount'] = facilityObj.totalPurposeAmount
    orgLoanDict['orgEstablishmentFee'] = facilityObj.totalEstablishmentFee

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
    app.send_task('SF_Create_Variation', kwargs={'newCaseUID': str(newCaseObj.caseUID), 'orgCaseUID': orgCaseUID })

    return {'status':'Ok', 'data':{'caseUID':str(newCaseObj.caseUID)}}