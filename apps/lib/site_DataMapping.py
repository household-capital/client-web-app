# Python Imports
import datetime
import math

# Django Imports
from django.forms import model_to_dict
from django.utils import timezone

# Local Imports
from apps.lib.site_Enums import *

from apps.servicing.models import FacilityRoles, FacilityProperty, FacilityPropertyVal
from apps.case.models import LoanPurposes, Loan
from apps.enquiry.models import Enquiry

from apps.base.model_utils import db_to_sf_map

# INTERNAL MAPPING

def mapEnquiryForSF(enqUID): 
    # mock function, however as the data model evolves, the mappings will begin to differ. 
    SF_LEAD_MAPPING = {
        'phoneNumber': 'Phone__c',
        'email': 'Email__c',
        'age_1': 'Age_of_1st_Applicant__c',
        'age_2': 'Age_of_2nd_Applicant__c',
        'dwellingType': 'Dwelling_Type__c',
        'valuation': 'Estimated_Home_Value__c',
        'suburb': 'Suburb__c',
        'postcode': 'Postal_Code__c',
        'isTopUp': 'IsTopUp__c',
        'isRefi': 'IsRefi__c',
        'isLive': 'IsLive__c',
        'isGive': 'IsGive__c',
        'isCare': 'IsCare__c',
        'enquiryNotes': 'External_Notes__c',
        'payIntPeriod': 'Pay_Interest_Period__c',
        'maxLoanAmount': 'Maximum_Loan__c',
        'maxLVR': 'Maximum_LVR__c',
       # 'referrerID': 'Referral_UserID__c',
        'mortgageDebt': 'Mortgage_Debt__c',
        'mortgageRepayment': 'Mortgage_Repayment__c',
        'base_specificity': 'Unit__c',
        'street_number': 'Street_Number__c',
        'street_name': 'Street_Name__c',
        'street_type': 'Street_Type__c',
        # gnaf not stored in uat
    }

    BooleanList = ['isTopUp', 'isRefi', 'isLive', 'isGive', 'isCare', 'doNotMarket']

    qs = Enquiry.objects.queryset_byUID(enqUID)
    enquiry = qs.get()

    payload = {}
    enquiryDict = enquiry.__dict__

    for app_field, sf_field in SF_LEAD_MAPPING.items():
        payload[sf_field] = enquiryDict[app_field]
        # Ensure Boolean fields are not null
        if app_field in BooleanList and not enquiryDict[app_field]:
            payload[sf_field] = False

    # Ensure name fields populated
    if not enquiryDict['name']:
        payload['Last_Name__c'] = 'Unknown'
    elif " " in enquiryDict['name']:
        payload['First_Name__c'], payload['Last_Name__c'] = enquiryDict['name'].split(" ", 1)
    else:
        payload['Last_Name__c'] = enquiryDict['name']

    payload['External_Id__c'] = str(enquiryDict['enqUID'])
    if enquiry.user and enquiry.user.profile and enquiry.user.profile.salesforceID:
        payload['CreatedById'] = enquiry.user.profile.salesforceID
    payload['Loan_Type__c'] = enquiry.enumLoanType()
    payload['Dwelling_Type__c'] = enquiry.enumDwellingType()
    payload['Lead_Source__c'] = enquiry.enumReferrerType()
    payload['Marketing_Source__c'] = enquiry.enumMarketingSource()
    payload['State__c'] = sfStateEnum(enquiry.state)
    # payload['Enquiry_Status__c'] = enquiry.enumEnquiryStage()
    payload['Propensity_Score__c'] = enquiry.enumPropensityCategory()
    payload['Marketing_Campaign__c'] = ''
    if enquiry.marketing_campaign: 
        payload['Marketing_Campaign__c'] = enquiry.marketing_campaign.campaign_name


    # Map / create other fields
    if enquiry.referralUser:
        payload['Referral_UserID__c'] = enquiry.referralUser.last_name
   
    return payload

def mapEnquiryToLead(enqUID):
    """Build SF REST API payload: Enquiry -> SF Lead"""

    SF_LEAD_MAPPING = {
        'phoneNumber': 'Phone',
        'email': 'Email',
        'age_1': 'Age_of_1st_Applicant__c',
        'age_2': 'Age_of_2nd_Applicant__c',
        'dwellingType': 'Dwelling_Type__c',
        'valuation': 'Estimated_Home_Value__c',
        'streetAddress': 'Street',
        'suburb': 'Suburb__c',
        'postcode': 'PostCode__c',
        'isTopUp': 'IsTopUp__c',
        'isRefi': 'IsRefi__c',
        'isLive': 'IsLive__c',
        'isGive': 'IsGive__c',
        'isCare': 'IsCare__c',
        'calcTopUp': 'CalcTopUp__c',
        'calcRefi': 'CalcRefi__c',
        'calcLive': 'CalcLive__c',
        'calcGive': 'CalcGive__c',
        'calcCare': 'CalcCare__c',
        'calcTotal': 'CalcTotal__c',
        'enquiryNotes': 'External_Notes__c',
        'payIntAmount': 'payIntAmount__c',
        'payIntPeriod': 'payIntPeriod__c',
        'status': 'HCC_Loan_Eligible__c',
        'maxLoanAmount': 'Maximum_Loan__c',
        'maxLVR': 'Maximum_LVR__c',
        'errorText': 'Ineligibility_Reason__c',
        'referrerID': 'Referrer_ID__c',
        'isCalendly': 'isCalendly__c',
        'mortgageDebt': 'Mortgage_Debt__c',
        'mortgageRepayment': 'Mortgage_Repayment__c',
        'submissionOrigin': 'Submission_Origin__c',
        'requestedCallback': 'Requested_Callback__c',
        'base_specificity': 'Unit__c',
        'street_number': 'Street_Number__c',
        'street_name': 'Street_Name__c',
        'street_type': 'Street_Type__c',
        # gnaf not stored in uat
    }

    BooleanList = ['isTopUp', 'isRefi', 'isLive', 'isGive', 'isCare']

    qs = Enquiry.objects.queryset_byUID(enqUID)
    enquiry = qs.get()

    payload = {}
    enquiryDict = enquiry.__dict__

    for app_field, sf_field in SF_LEAD_MAPPING.items():
        payload[sf_field] = enquiryDict[app_field]
        # Ensure Boolean fields are not null
        if app_field in BooleanList and not enquiryDict[app_field]:
            payload[sf_field] = False

    # Ensure name fields populated
    if not enquiryDict['name']:
        payload['Lastname'] = 'Unknown'
    elif " " in enquiryDict['name']:
        payload['Firstname'], payload['Lastname'] = enquiryDict['name'].split(" ", 1)
    else:
        payload['Lastname'] = enquiryDict['name']

    payload['External_ID__c'] = str(enquiryDict['enqUID'])
    payload['OwnerID'] = enquiry.user.profile.salesforceID
    payload['Loan_Type__c'] = enquiry.enumLoanType()
    payload['Dwelling_Type__c'] = enquiry.enumDwellingType()
    payload['LeadSource'] = enquiry.enumReferrerType()
    payload['Marketing_Source__c'] = enquiry.enumMarketingSource()
    payload['State__c'] = sfStateEnum(enquiry.state)
    payload['Status__c'] = enquiry.enumEnquiryStage()
    payload['Propensity_Category__c'] = enquiry.enumPropensityCategory()
    payload['Marketing_Campaign__c'] = ''
    if enquiry.marketing_campaign: 
        payload['Marketing_Campaign__c'] = enquiry.marketing_campaign.campaign_name


    # Map / create other fields
    if enquiry.referralUser:
        payload['Referral_UserID__c'] = enquiry.referralUser.last_name
    if enquiry.followUp:
        payload['Last_External_Followup_Date__c'] = enquiry.followUp.strftime("%Y-%m-%d")

    if enquiry.followUpDate:
        payload['Scheduled_Followup_Date_External__c'] = enquiry.followUpDate.strftime("%Y-%m-%d")
    payload['Scheduled_Followup_Notes__c'] = enquiry.followUpNotes

    if enquiry.closeDate:
        payload['Park_Lead__c'] = True
    else:
        payload['Park_Lead__c'] = False

    payload['Reason_for_Parking_Lead__c'] = enquiry.enumCloseReason()

    return payload


def mapFacilityToCase(facilityObj):
    """Reverse map from Facility to Case - for Loan Variation Creation
    This should be replaced with query direct from Salesforce when Serciving is complete
    """

    # Source objects
    roleQs = FacilityRoles.objects.filter(facility=facilityObj)
    roleDict = get_role_dict(roleQs)
    propertyObj = FacilityProperty.objects.filter(facility=facilityObj).get()
    valuationObj = FacilityPropertyVal.objects.filter(property=propertyObj).order_by('-valuationDate').first()

    # Data map
    payload = {
        'caseStage': caseStagesEnum.UNQUALIFIED_CREATED.value,
        'appType': appTypesEnum.VARIATION.value,
        'caseDescription': roleDict['borrowers'][0]['lastName'] + " - " + str(propertyObj.postcode) + " - Variation",
        'owner': facilityObj.owner,
        'caseNotes': '[# Variation - please update #]',
        'phoneNumber': roleDict['borrowers'][0]['mobile'] if roleDict['borrowers'][0]['mobile'] is not None else
        roleDict['borrowers'][0]['phone'],
        'email': roleDict['borrowers'][0]['email'],
        'loanType': loanTypesEnum.SINGLE_BORROWER.value if roleDict[
                                                               'number'] == 1 else loanTypesEnum.JOINT_BORROWER.value,
        'clientType1': clientTypesEnum.BORROWER.value,
        'salutation_1': roleDict['borrowers'][0]['salutation'],
        'firstname_1': roleDict['borrowers'][0]['firstName'],
        'middlename_1': roleDict['borrowers'][0]['middleName'],
        'preferredName_1': roleDict['borrowers'][0]['preferredName'],
        'surname_1': roleDict['borrowers'][0]['lastName'],
        'birthdate_1': roleDict['borrowers'][0]['birthdate'],
        'age_1': int((datetime.date.today() - roleDict['borrowers'][0]['birthdate']).days / 365.25),
        'sex_1': roleDict['borrowers'][0]['gender'],
        'maritalStatus_1': roleDict['borrowers'][0]['maritalStatus'],
        'street': propertyObj.street,
        'suburb': propertyObj.suburb,
        'postcode': propertyObj.postcode,
        'state': propertyObj.state,
        'dwellingType': propertyObj.dwellingType,
        'valuation': valuationObj.valuationAmount,
        'salesChannel': channelTypesEnum.DIRECT_ACQUISITION.value,
        'titleRequest' : True,

        'refCaseUID': facilityObj.originalCaseUID,
        'sfLeadID': "NO LEAD",
        'meetingDate': timezone.now()
    }

    if roleDict['number'] == 2:
        payload.update({
            'clientType2': clientTypesEnum.BORROWER.value,
            'salutation_2': roleDict['borrowers'][1]['salutation'],
            'firstname_2': roleDict['borrowers'][1]['firstName'],
            'middlename_2': roleDict['borrowers'][1]['middleName'],
            'surname_2': roleDict['borrowers'][1]['lastName'],
            'preferredName_2': roleDict['borrowers'][1]['preferredName'],
            'birthdate_2': roleDict['borrowers'][1]['birthdate'],
            'age_2': int((datetime.date.today() - roleDict['borrowers'][1]['birthdate']).days / 365.25),
            'sex_2': roleDict['borrowers'][1]['gender'],
            'maritalStatus_2': roleDict['borrowers'][1]['maritalStatus'],
        })

    return payload


def get_role_dict(roleQs):
    borrowerQs = roleQs.filter(role__in=[roleEnum.PRINCIPAL_BORROWER.value,
                                         roleEnum.SECONDARY_BORROWER.value,
                                         roleEnum.BORROWER.value]).order_by('role')
    roleDict = {'number': borrowerQs.count()}
    borrowerList = []
    for borrower in borrowerQs:
        borrowerList.append(model_to_dict(borrower))
    roleDict['borrowers'] = borrowerList

    return roleDict


# CLIENT APP TO SF MAPPING

def mapCaseToOpportunity(caseObj, lossObj):
    """CASE ->  Opportunity Map"""

    payload = {
        # Core case data
        'sfOpportunityId': caseObj.sfOpportunityID,
        'caseUID': str(caseObj.caseUID),
        'caseDescription': caseObj.caseDescription,
        'user': caseObj.owner.profile.salesforceID,
        'adviser': caseObj.adviser,
        'loanType': caseObj.enumLoanType(),
        'salesChannel': caseObj.enumChannelType(),
        "channelDetail": caseObj.enumChannelDetailType(),
        'closeReason': caseObj.lossdata.enumCloseReason(),
        'followUpNotes': caseObj.lossdata.followUpNotes,
        'doNotMarket': caseObj.doNotMarket,
        'mortgageDebt': caseObj.mortgageDebt,
        'superAmount': caseObj.superAmount,
        'pensionType': caseObj.enumPensionType(),
        'pensionAmount': caseObj.pensionAmount,
        'clientType1': caseObj.enumClientType()[0],
        'salutation_1': caseObj.enumSalutation()[0],
        'surname_1': caseObj.surname_1,
        'firstname_1': caseObj.firstname_1,
        'preferredName_1': caseObj.preferredName_1,
        'middlename_1': caseObj.middlename_1,
        'age_1': caseObj.age_1,
        'sex_1': caseObj.enumSex()[0],
        'maritalStatus_1': caseObj.enumMaritalStatus()[0],
        'phoneNumber': caseObj.phoneNumber,
        'email': caseObj.email,
        'street': caseObj.street,
        'suburb': caseObj.suburb,
        'postcode': caseObj.postcode,
        'state': caseObj.enumStateType(),
        'valuation': caseObj.valuation,
        'dwellingType': caseObj.enumDwellingType(),
        'meetingDate': caseObj.meetingDate,
        'enquiryCreateDate': caseObj.enquiryCreateDate,
        'isReferPostcode' : caseObj.isReferPostcode,
        'referPostcodeStatus': caseObj.enumReferPostcodeStatus(),

        # Meeting Data
        'maxLVR': caseObj.loan.maxLVR,
        'actualLVR': caseObj.loan.actualLVR,
        'establishmentFee': caseObj.loan.establishmentFee,
        'totalLoanAmount': caseObj.loan.totalLoanAmount,
        'annualPensionIncome': caseObj.loan.annualPensionIncome,
        'choiceRetireAtHome': caseObj.loan.choiceRetireAtHome,
        'choiceAvoidDownsizing': caseObj.loan.choiceAvoidDownsizing,
        'choiceAccessFunds': caseObj.loan.choiceAccessFunds,
        'choiceTopUp': caseObj.loan.choiceTopUp,
        'choiceRefinance': caseObj.loan.choiceRefinance,
        'choiceGive': caseObj.loan.choiceGive,
        'choiceReserve': caseObj.loan.choiceReserve,
        'choiceLive': caseObj.loan.choiceLive,
        'choiceCare': caseObj.loan.choiceCare,
        'choiceFuture': caseObj.loan.choiceFuture,
        'choiceCenterlink': caseObj.loan.choiceCenterlink,
        'choiceVariable': caseObj.loan.choiceVariable,
        'consentPrivacy': caseObj.loan.consentPrivacy,
        'consentElectronic': caseObj.loan.consentElectronic,
        'protectedEquity': caseObj.loan.protectedEquity,
        'interestPayAmount': caseObj.loan.interestPayAmount,
        'interestPayPeriod': caseObj.loan.interestPayPeriod,
        'detailedTitle': caseObj.loan.detailedTitle,
        'isLowLVR': caseObj.loan.isLowLVR,

        # Model Setting Data
        'inflationRate': caseObj.modelsetting.inflationRate,
        'housePriceInflation': caseObj.modelsetting.housePriceInflation,
        'interestRate': caseObj.modelsetting.interestRate,
        'lendingMargin': caseObj.modelsetting.lendingMargin,
        'comparisonRateIncrement': caseObj.modelsetting.comparisonRateIncrement,
        'establishmentFeeRate': caseObj.modelsetting.establishmentFeeRate,

        # Notes/ Fact Find Fields
        'caseNotes': caseObj.caseNotes,
        'backgroundNotes': caseObj.factfind.backgroundNotes,
        'requirementsNotes': caseObj.factfind.requirementsNotes,
        'topUpNotes': caseObj.factfind.topUpNotes,
        'refiNotes': caseObj.factfind.refiNotes,
        'liveNotes': caseObj.factfind.liveNotes,
        'giveNotes': caseObj.factfind.giveNotes,
        'careNotes': caseObj.factfind.careNotes,
        'futureNotes': caseObj.factfind.futureNotes,
        'clientNotes': caseObj.factfind.clientNotes,

        'isApplicantsEngaged': caseObj.factfind.all_applications_are_engaged,
        'applicantDisagreementReason': caseObj.factfind.applicants_disengagement_reason,
        'isThirdPartyEngaged': caseObj.factfind.is_third_party_engaged,
        'reasonForThirdPartyEngagement': caseObj.factfind.reason_for_thirdparty_engagement,
        'isPOASign': caseObj.factfind.applicant_poa_signing,
        'PlannedLengthOfStay': caseObj.factfind.enumPlannedLengthOfStay,
        'PlannedMethodOfDischarge': caseObj.factfind.enumPlannedMethodOfDischarge,
        'isVulnerable': caseObj.factfind.is_vulnerable_customer,
        'vulnerableDescription': caseObj.factfind.vulnerability_description,
        'considredAltDownsizingOpts': caseObj.factfind.considered_alt_downsizing_opts,
        'planForGiving': caseObj.factfind.plan_for_future_giving,
        'planForCare': caseObj.factfind.plan_for_aged_care,
        'additionalCreditInfo': caseObj.factfind.additional_info_credit,

        
    }
    # syncing new address fields - hm-2097
    for db_field, sf_name in db_to_sf_map.items(): 
        payload[sf_name] = getattr(caseObj, db_field)

    # Second Borrower
    if caseObj.clientType2 != None:
        payload.update({

            'clientType2': caseObj.enumClientType()[1],
            'salutation_2': caseObj.enumSalutation()[1],
            'surname_2': caseObj.surname_2,
            'firstname_2': caseObj.firstname_2,
            'preferredName_2': caseObj.preferredName_2,
            'middlename_2': caseObj.middlename_2,
            'age_2': caseObj.age_2,
            'sex_2': caseObj.enumSex()[1],
            'maritalStatus_2': caseObj.enumMaritalStatus()[1],

        })

    # ProductType
    productMap = {
        productTypesEnum.CONTINGENCY_20K.value: 'Contingency 20K',
        productTypesEnum.INCOME.value: 'Home Income Loan',
        productTypesEnum.LUMP_SUM.value: 'Household Loan',
        productTypesEnum.COMBINATION.value: 'Household Loan',
        productTypesEnum.REFINANCE.value: 'Household Loan',
    }

    payload['productType'] = productMap[caseObj.productType]

    # Purposes

    loanObj = Loan.objects.queryset_byUID(str(caseObj.caseUID)).get()

    purposes=[]
    purposeQs = LoanPurposes.objects.filter(loan = loanObj)

    for purpose in purposeQs:
        if (purpose.amount != 0) or ((purpose.amount == 0) and (purpose.variationAmount != 0)):

            purposes.append(
                    {'purposeUID': str(purpose.purposeUID),
                     'category': purpose.enumCategoryPretty,
                     'intention': purpose.enumIntentionPretty,
                     'amount': purpose.amount,
                     'active': purpose.active,
                     'drawdownAmount': purpose.drawdownAmount,
                     'drawdownFrequency': purpose.enumDrawdownFrequency.lower() if purpose.enumDrawdownFrequency else None,
                     'drawdownStartDate': purpose.drawdownStartDate.strftime("%Y-%m-%d") if purpose.drawdownStartDate else None,
                     'drawdownEndDate': purpose.drawdownEndDate.strftime("%Y-%m-%d") if purpose.drawdownEndDate else None,
                     'contractDrawdowns': purpose.contractDrawdowns,
                     'planDrawdowns': purpose.planDrawdowns,
                     'planAmount': purpose.planAmount,
                     'description': purpose.description,
                     'notes': purpose.notes,
                     'variationAmount': purpose.variationAmount}
            )

    payload['purposes'] = purposes

    # Date Fields
    SF_DATE_FIELDS = ['timestamp', 'updated', 'birthdate_1', 'birthdate_2', 'closeDate', 'followUpDate']
    SF_DATE_TIME_FIELDS = ['meetingDate', 'enquiryCreateDate']

    objDict = caseObj.__dict__
    objDict.update(lossObj.__dict__)

    for field in SF_DATE_FIELDS:
        if objDict[field]:
            payload[field] = objDict[field].strftime("%Y-%m-%d")
        else:
            payload[field] = None


    for field in SF_DATE_TIME_FIELDS:
        if objDict[field]:
            payload[field] = objDict[field].strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            payload[field] = None

    # Super Fund
    if caseObj.superFund:
        payload['superFund'] = caseObj.superFund.fundName
    else:
        payload['superFund'] = ""


    return payload


# SERIALISE PURPOSES 

def serialisePurposes(loanObj, enum=False):
    """Create purpose dictionary (retro fit data from new purpose objects)"""

    def __getItem(category, intention, attr, default=None):
        try:
            return getattr(srcDict[category][intention], attr)
        except:
            return default

    srcDict = loanObj.get_purposes()

    purposeDict = {
        'topUpAmount': __getItem('TOP_UP', 'INVESTMENT', 'amount', 0),
        'topUpContingencyAmount': __getItem('TOP_UP', 'CONTINGENCY', 'amount', 0),
        'refinanceAmount': __getItem('REFINANCE', 'MORTGAGE', 'amount', 0),
        'renovateAmount': __getItem('LIVE', 'RENOVATIONS', 'amount', 0),
        'travelAmount': __getItem('LIVE', 'TRANSPORT_AND_TRAVEL', 'amount', 0),
        'giveAmount': __getItem('GIVE', 'GIVE_TO_FAMILY', 'amount', 0),
        'careAmount': __getItem('CARE', 'LUMP_SUM', 'amount', 0),

        'topUpDrawdownAmount': __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'amount', 0),
        'topUpIncomeAmount': __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'drawdownAmount', 0),
        'topUpFrequency': __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'drawdownFrequency', 0),
        'topUpPeriod': __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'planPeriod', 0),
        'topUpPlanDrawdowns': __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'planDrawdowns', 0),
        'topUpContractDrawdowns': __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'contractDrawdowns', 0),
        'topUpPlanAmount': __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'planAmount', 0),
        'topUpBuffer': 0,

        'careDrawdownAmount': __getItem('CARE', 'REGULAR_DRAWDOWN', 'amount', 0),
        'careRegularAmount': __getItem('CARE', 'REGULAR_DRAWDOWN', 'drawdownAmount', 0),
        'careFrequency': __getItem('CARE', 'REGULAR_DRAWDOWN', 'drawdownFrequency', 0),
        'carePeriod': __getItem('CARE', 'REGULAR_DRAWDOWN', 'planPeriod', 0),
        'carePlanDrawdowns': __getItem('CARE', 'REGULAR_DRAWDOWN', 'planDrawdowns', 0),
        'careContractDrawdowns': __getItem('CARE', 'REGULAR_DRAWDOWN', 'contractDrawdowns', 0),
        'carePlanAmount': __getItem('CARE', 'REGULAR_DRAWDOWN', 'planAmount', 0),

        'topUpDescription': __getItem('TOP_UP', 'INVESTMENT', 'description', ""),
        'topUpContingencyDescription': __getItem('TOP_UP', 'CONTINGENCY', 'description', ""),
        'renovateDescription': __getItem('LIVE', 'RENOVATIONS', 'description', ""),
        'travelDescription': __getItem('LIVE', 'TRANSPORT_AND_TRAVEL', 'description', ""),
        'careDescription': __getItem('CARE', 'LUMP_SUM', 'description', ""),
        'careDrawdownDescription': __getItem('CARE', 'REGULAR_DRAWDOWN', 'description', ""),
        'giveDescription': __getItem('GIVE', 'GIVE_TO_FAMILY', 'description', ""),

    }

    purposeDict['enumTopUpFrequency'] = __getItem('TOP_UP', 'REGULAR_DRAWDOWN', 'enumDrawdownFrequency')
    purposeDict['enumCareFrequency'] = __getItem('CARE', 'REGULAR_DRAWDOWN', 'enumDrawdownFrequency')

    if enum:
         # Overwrite with enum
        if purposeDict['topUpFrequency']:
            purposeDict['topUpFrequency']=purposeDict['enumTopUpFrequency'].lower()

        if purposeDict['careFrequency']:
            purposeDict['careFrequency'] = purposeDict['enumCareFrequency'].lower()
    else:
        if purposeDict['topUpFrequency']:
            purposeDict['enumTopUpFrequency'] = purposeDict['enumTopUpFrequency'].lower()

        if purposeDict['careFrequency']:
            purposeDict['enumCareFrequency'] = purposeDict['enumCareFrequency'].lower()

    return purposeDict


# FACILITY: AMAL LOAN OBJECT MAPPING

def mapTransToFacility(loan, transaction):
    """AMAL Transaction map"""

    payload = {
        'facility': loan,
        'description': transaction['description'],
        'type': transaction['type'],
        'transactionDate': transaction['transactionDate'],
        'effectiveDate': transaction['effectiveDate'],
        'tranRef': transaction['tranRef'],
        'debitAmount': transaction['debitAmount'],
        'creditAmount': transaction['creditAmount'],
        'balance': transaction['balance'],
    }

    return payload


# SF LOAN OBJECT MAPPING

def mapLoanToFacility(caseObj, loanDict):
    """Map SF Loan Object to Facility (includes temporary workarounds)
    This should be removed when Servicing established in Salesforce"""

    facilityStatus = {"Inactive": 0, "Active": 1, "Repaid": 2, "Suspended": 3}

    payload = {
        'owner': caseObj.owner,
        'originalCaseUID': caseObj.caseUID,
        'sfLoanName': caseObj.surname_1 + ", " + caseObj.street + ", " + caseObj.suburb + ", " + caseObj.enumStateType() + ", " + str(
            caseObj.postcode),
        'sfLoanID': loanDict['LoanNumber__c'],
        'sfID': loanDict['Id'],
        # 'sfAccountID': 'unknown',
        # 'sfReferrerAccount' : 'unknown',
        'amalID': loanDict['Mortgage_Number__c'],
        'sfOriginatorID': caseObj.owner.profile.salesforceID,  # Temporary
        'status': facilityStatus[loanDict['Status__c']],
        'totalPurposeAmount': round(loanDict['Total_Limits__c'],0),
        'totalLoanAmount': round(loanDict['Total_Loan_Amount__c'],0),
        'totalEstablishmentFee': round(loanDict['Total_Establishment_Fee__c'],0),
        'establishmentFeeRate': loanDict['Establishment_Fee_Percent__c'] / 100,
        'totalPlanPurposeAmount': round(loanDict['Total_Plan_Purpose_Amount__c'],0),
        'totalPlanAmount': round(loanDict['TotalPlanAmount__c'],0),
        'totalPlanEstablishmentFee': round(loanDict['TotalPlanEstablishmentFee__c'],0),
        'bankAccountNumber': loanDict['Account_Number__c'],
        'bsbNumber': loanDict['BSB__c'],
        'meetingDate': caseObj.meetingDate,  # Temporary
    }

    return payload


def mapRolesToFacility(loan, contact, role):
    roleTypes = {"Principal Borrower": 0,
                 "Secondary Borrower": 1,
                 "Borrower": 2,
                 "Nominated Occupant": 3,
                 "Permitted Cohabitant": 4,
                 "Power of Attorney": 5,
                 "Authorised 3rd Party": 6,
                 "Distribution Partner Contact": 7,
                 "Adviser": 8,
                 "Loan Originator": 9,
                 "Loan Writer": 10,
                 "Valuer": 11,
                 "Executor": 12,
                 "Solicitor": 13}

    payload = {'facility': loan,
               'sfContactID': contact['Id'],
               'role': roleTypes[role['Role__c']],
               # 'isContact': False,  ####
               # 'isInformation:
               # 'isAuthorised
               'lastName': contact['LastName'],
               'firstName': contact['FirstName'],
               'preferredName': contact['PreferredName__c'],
               'middleName': contact['MiddleName'],
               'birthdate': contact['Birthdate__c'],
               'mobile': contact['MobilePhone'],
               'phone': contact['Phone'],
               'email': contact['Email'],
               'street': contact['MailingStreet'],
               'suburb': contact['MailingCity'],
               'postcode': contact['MailingPostalCode'],
               'roleNotes': None
               }

    if contact['Marital_Status__c']:
        payload['maritalStatus'] = maritalEnum[contact['Marital_Status__c'].upper().replace(" ","")].value

    if contact['Salutation']:
        payload['salutation'] = salutationEnum[contact['Salutation'].replace('.', '').upper()].value

    if contact['Gender__c']:
        payload['gender'] = clientSexEnum[contact['Gender__c'].upper()].value

    if contact['MailingStateCode']:
        payload['state'] = stateTypesEnum[contact["MailingStateCode"]].value

    return payload


def mapPropertyToFacility(loan, propertyObj):
    stateShortCode = {'Victoria': 'VIC', "New South Wales": 'NSW', "Queensland": 'QLD', "Tasmania": 'TAS',
                      "South Australia": 'SA', "Western Australia": 'WA', "Northern Territory": 'NT',
                      "Australian Capital Territory": 'ACT'}

    payload = {'facility': loan,
               'sfPropertyID': propertyObj['Id'],
               'street': propertyObj['Street_Address__c'],
               'suburb': propertyObj['Suburb_City__c'],
               'postcode': propertyObj['Postcode__c'],
               'dwellingType': get_property_type(propertyObj['Property_Type__c']),
               'insuranceCompany': propertyObj['Insurer__c'],
               'insurancePolicy': propertyObj['Policy_Number__c'],
               'insuranceExpiryDate': propertyObj['Insurance_Expiry_Date__c'],
               'insuredAmount': propertyObj['Minimum_Insurance_Value__c']
               }

    if propertyObj['State__c']:
        stateCode = stateShortCode[propertyObj['State__c']]
        payload['state'] = stateTypesEnum[stateCode].value

    return payload


def get_property_type(arg):
    # Convert SF Property Type:
    if arg == "House":
        return dwellingTypesEnum.HOUSE.value
    else:
        return dwellingTypesEnum.APARTMENT.value


def mapValuationsToFacility(propertyRef, propertyObj):
    # Separate Facility Table for Valuations

    payload = {'property': propertyRef,
               'valuationAmount': propertyObj['Home_Value_FullVal__c'],
               'valuationDate': propertyObj['Last_Valuation_Date__c'],
               'valuationType': 1,  ###
               'valuationCompany': propertyObj['Valuer__c'],
               'valuerName': propertyObj['Valuer_Name__c']
               }

    return payload


def mapPurposesToFacility(loan, purpose):
    # SF Purposes to Facility Purposes


    sfCategoryMap = {'Care':'CARE',
                     'Give': 'GIVE',
                     'Live': 'LIVE',
                     'Refinance': 'REFINANCE',
                     'Top Up': 'TOP_UP'
                     }

    sfIntentionMap = {
                    'Investment':'INVESTMENT',
                    'Contingency':'CONTINGENCY',
                    'Regular Drawdown':'REGULAR_DRAWDOWN',
                    'Give to Family':'GIVE_TO_FAMILY',
                    'Renovations':'RENOVATIONS',
                    'Transport, Travel, and Other':'TRANSPORT_AND_TRAVEL',
                    'Transport': 'TRANSPORT_AND_TRAVEL',
                    'Transport and Travel': 'TRANSPORT_AND_TRAVEL',
                    'Lump Sum':'LUMP_SUM',
                    'Mortgage':'MORTGAGE'
    }


    payload = {'facility': loan,
               'sfPurposeID': purpose['Id'],
               'category': purposeCategoryEnum[sfCategoryMap[purpose['Category__c']]].value,
               'intention': purposeIntentionEnum[sfIntentionMap[purpose['Intention__c']]].value,
               'amount': chkVal(purpose['Amount__c']),
               'drawdownAmount': chkVal(purpose['Drawdown_Amount__c']),
               'drawdownFrequency': incomeFrequencyEnum[purpose['Drawdown_Frequency__c'].upper()].value if purpose['Drawdown_Frequency__c'] else None ,
               'drawdownStartDate': None,  ###
               'drawdownEndDate': None,  ###
               'planAmount': chkVal(purpose['Plan_Amount__c']),
               'planPeriod': chkVal(purpose['Plan_Period__c']),
               'topUpBuffer': purpose['TopUp_Buffer__c'],
               'description': purpose['Description__c'],
               'notes': purpose['Notes__c'],
               'contractDrawdowns': chkVal(purpose['Contract_Drawdowns__c']),
               'planDrawdowns': chkVal(purpose['Plan_Drawdowns__c']),
               'active': purpose['Active__c'],

               }

    return payload


def chkVal(arg):
    if arg == None:
        return None
    if math.isnan(arg):
        return None
    else:
        return arg



def sfStateEnum(state):
    """Enumerate SF longform State"""
    if state == None:
        return None

    stateMap = {
        stateTypesEnum.NSW.value: "New South Wales",
        stateTypesEnum.VIC.value: "Victoria",
        stateTypesEnum.ACT.value: "Australian Capital Territory",
        stateTypesEnum.QLD.value: "Queensland",
        stateTypesEnum.SA.value: "South Australia",
        stateTypesEnum.WA.value: "Western Australia",
        stateTypesEnum.TAS.value: "Tasmania",
        stateTypesEnum.NT.value: "Northern Territory"
    }

    return stateMap[state]