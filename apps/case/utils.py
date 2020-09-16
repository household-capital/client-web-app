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
from apps.lib.site_Enums import purposeIntentionEnum, purposeCategoryEnum
from apps.lib.site_Utilities import createCaseModelSettings
from apps.servicing.models import FacilityPurposes
from apps.case.models import Case, Loan, LoanPurposes, ModelSetting



def createLoanVariation(facilityObj):

    # 1. Create New Case Object

    payload = mapFacilityToCase(facilityObj)

    try:
        newCaseObj = Case.objects.create(**payload)
    except:
        return {'status': "Error", 'responseText':'Could not create variation'}

    # 2. Create Case Loan Object

    orgLoanDict={}

    orgLoanDict['purposeAmount'] = facilityObj.totalPurposeAmount
    orgLoanDict['establishmentFee'] = facilityObj.totalEstablishmentFee
    orgLoanDict['totalLoanAmount'] = facilityObj.totalLoanAmount

    # Plan Amounts
    orgLoanDict['planPurposeAmount']  = facilityObj.totalPlanPurposeAmount
    orgLoanDict['planEstablishmentFee'] = facilityObj.totalPlanEstablishmentFee
    orgLoanDict['totalPlanAmount'] = facilityObj.totalPlanAmount


    orgLoanDict['accruedInterest'] = int(max(facilityObj.currentBalance - facilityObj.advancedAmount, 0))
    orgLoanDict['orgTotalLoanAmount'] = facilityObj.totalLoanAmount
    orgLoanDict['orgPurposeAmount'] = facilityObj.totalPurposeAmount
    orgLoanDict['orgEstablishmentFee'] = facilityObj.totalEstablishmentFee

    Loan.objects.filter(case=newCaseObj).update(**orgLoanDict)
    newLoanObj = Loan.objects.filter(case=newCaseObj).get()

    # 3. Case ModelSetting Object
    settingsDict={}
    settingsDict['establishmentFeeRate'] = facilityObj.establishmentFeeRate

    createCaseModelSettings(str(newCaseObj.caseUID))
    ModelSetting.objects.filter(case=newCaseObj).update(**settingsDict)

    #4. Create Purposes
    orgPurposesQs = FacilityPurposes.objects.filter(facility=facilityObj)
    for purpose in orgPurposesQs:
        orgPurposeDict = model_to_dict(purpose, exclude=['facility', 'sfPurposeID', 'id'])
        orgPurposeDict['loan'] = newLoanObj
        orgPurposeDict['originalAmount'] = orgPurposeDict['amount']
        orgPurposeDict['category'] = purpose.category
        orgPurposeDict['intention'] = purpose.intention
        LoanPurposes.objects.create(**orgPurposeDict)

    # 5. Create SF Opportunity
    app.send_task('SF_Create_Variation', kwargs={'newCaseUID': str(newCaseObj.caseUID), 'orgCaseUID': facilityObj.originalCaseUID })

    return {'status':'Ok', 'data':{'caseUID':str(newCaseObj.caseUID)}}