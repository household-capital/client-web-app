
# Python Imports
import datetime
import math


# Django Imports
from django.forms import model_to_dict


# Local Imports
from apps.lib.site_Enums import roleEnum, dwellingTypesEnum, \
    caseStagesEnum, clientSexEnum, clientTypesEnum, \
    loanTypesEnum, channelTypesEnum, stateTypesEnum, \
    salutationEnum, maritalEnum, appTypesEnum

from apps.servicing.models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, \
    FacilityPurposes, FacilityEvents, FacilityEnquiry, FacilityAdditional


# INTERNAL MAPPING

def mapFacilityToCase(facilityObj):
    # Reverse map from facility to case - for Loan Variation Creation

    #Source objects
    roleQs = FacilityRoles.objects.filter(facility=facilityObj)
    roleDict = get_role_dict(roleQs)
    propertyObj = FacilityProperty.objects.filter(facility=facilityObj).get()
    valuationObj = FacilityPropertyVal.objects.filter(property=propertyObj).order_by('-valuationDate').first()

    #Data map
    payload = {
        'caseStage': caseStagesEnum.DISCOVERY.value,
        'appType': appTypesEnum.VARIATION.value,
        'caseDescription': roleDict['borrowers'][0]['lastName'] + " - " + str(propertyObj.postcode) + " - Variation",
        'user': facilityObj.owner,
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
        'salesChannel': channelTypesEnum.DIRECT_ACQUISITION.value
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

    payload={
        # Core case data
        'sfOpportunityId': caseObj.sfOpportunityID,
        'caseUID': str(caseObj.caseUID),
        'caseDescription': caseObj.caseDescription,
        'user': caseObj.user.profile.salesforceID,
        'adviser': caseObj.adviser,
        'loanType': caseObj.enumLoanType(),
        'salesChannel': caseObj.enumChannelType(),
        'closeReason': caseObj.lossdata.enumCloseReason(),
        'followUpNotes': caseObj.lossdata.followUpNotes,
        'doNotMarket': caseObj.lossdata.doNotMarket,
        'mortgageDebt': caseObj.mortgageDebt,
        'superAmount': caseObj.superAmount,
        'pensionType': caseObj.enumPensionType(),
        'pensionAmount': caseObj.pensionAmount,
        'clientType1': caseObj.enumClientType()[0],
        'salutation_1':caseObj.enumSalutation()[0] ,
        'surname_1': caseObj.surname_1,
        'firstname_1': caseObj.firstname_1,
        'preferredName_1': caseObj.preferredName_1,
        'middlename_1':caseObj.middlename_1,
        'age_1': caseObj.age_1,
        'sex_1': caseObj.enumSex()[0],
        'maritalStatus_1':caseObj.enumMaritalStatus()[0],
        'phoneNumber': caseObj.phoneNumber,
        'email': caseObj.email,
        'clientType2': caseObj.enumClientType()[1],
        'salutation_2': caseObj.enumSalutation()[1],
        'surname_2': caseObj.surname_2,
        'firstname_2': caseObj.firstname_2,
        'preferredName_2': caseObj.preferredName_2,
        'middlename_2': caseObj.middlename_2,
        'age_2': caseObj.age_2,
        'sex_2': caseObj.enumSex()[1],
        'maritalStatus_2': caseObj.enumMaritalStatus()[1],
        'street': caseObj.street,
        'suburb': caseObj.suburb,
        'postcode': caseObj.postcode,
        'state': caseObj.enumStateType(),
        'valuation': caseObj.valuation,
        'dwellingType': caseObj.enumDwellingType(),

        #Meeting Data
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
        'topUpAmount': caseObj.loan.topUpAmount,
        'topUpDrawdownAmount': caseObj.loan.topUpDrawdownAmount,
        'topUpIncomeAmount': caseObj.loan.topUpIncomeAmount,
        'topUpFrequency': caseObj.loan.enumDrawdownFrequency(),
        'topUpPeriod': caseObj.loan.topUpPeriod,
        'topUpBuffer': caseObj.loan.topUpBuffer,
        'topUpContingencyAmount': caseObj.loan.topUpContingencyAmount,
        'refinanceAmount': caseObj.loan.refinanceAmount,
        'renovateAmount': caseObj.loan.renovateAmount,
        'travelAmount': caseObj.loan.travelAmount,
        'giveAmount': caseObj.loan.giveAmount,
        'careAmount': caseObj.loan.careAmount,
        'careDrawdownAmount': caseObj.loan.careDrawdownAmount,
        'careRegularAmount': caseObj.loan.careRegularAmount,
        'careFrequency': caseObj.loan.enumCareFrequency(),
        'carePeriod': caseObj.loan.carePeriod,
        'topUpDescription': caseObj.loan.topUpDescription,
        'topUpContingencyDescription': caseObj.loan.topUpContingencyDescription,
        'renovateDescription': caseObj.loan.renovateDescription,
        'travelDescription': caseObj.loan.travelDescription,
        'careDescription': caseObj.loan.careDescription,
        'careDrawdownDescription': caseObj.loan.careDrawdownDescription,
        'giveDescription': caseObj.loan.giveDescription,
        'detailedTitle' : caseObj.loan.detailedTitle,

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
    }

    SF_DATE_FIELDS = ['timestamp', 'updated', 'birthdate_1', 'birthdate_2', 'meetingDate', 'closeDate', 'followUpDate']

    objDict = caseObj.__dict__
    objDict.update(lossObj.__dict__)

    for field in SF_DATE_FIELDS:
        if objDict[field]:
            payload[field] = objDict[field].strftime("%Y-%m-%d")
        else:
            payload[field] = None

    if caseObj.superFund:
        payload['superFund'] = caseObj.superFund.fundName
    else:
        payload['superFund'] = ""


    return payload




# FACILITY: AMAL LOAN OBJECT MAPPING

def mapTransToFacility(loan, transaction):

    payload ={
        'facility': loan,
        'description':  transaction['description'],
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
    # Map SF Loan Object to Facility (includes temporary workarounds)

    facilityStatus = {"Inactive": 0, "Active": 1, "Repaid": 2, "Suspended": 3}

    payload = {
        'owner': caseObj.user,
        'originalCaseUID': caseObj.caseUID,
        'sfLoanName': caseObj.surname_1 + ", " + caseObj.street + ", " + caseObj.suburb + ", " + caseObj.enumStateType() + ", " + str(
            caseObj.postcode),
        'sfLoanID': loanDict['Loan.Name'],
        'sfID': loanDict['Loan.Id'],
        # 'sfAccountID': 'unknown',
        # 'sfReferrerAccount' : 'unknown',
        'amalID': loanDict['Loan.Mortgage_Number__c'],
        'sfOriginatorID': caseObj.user.profile.salesforceID,  # Temporary
        'status': facilityStatus[loanDict['Loan.Status__c']],
        'totalPurposeAmount': loanDict['Loan.Total_Limits__c'],
        'totalLoanAmount': loanDict['Loan.Total_Loan_Amount__c'],
        'totalEstablishmentFee': loanDict['Loan.Total_Establishment_Fee__c'],
        'establishmentFeeRate': loanDict['Loan.Establishment_Fee_Percent__c'] / 100,
        # 'totalPlanPurposeAmount': loanObj.totalPlanAmount,
        # 'totalPlanAmount': loanObj.totalPlanAmount,
        # 'totalPlanEstablishmentFee': loanObj.planEstablishmentFee,
        'bankAccountNumber': loanDict['Loan.Account_Number__c'],
        'bsbNumber': loanDict['Loan.BSB__c'],
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
                 "Executor": 12}

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
        payload['maritalStatus'] = maritalEnum[contact['Marital_Status__c'].upper()].value

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
    #Convert SF Property Type:
    if arg=="House":
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
    #SF Purposes to Facility Purposes

    payload = {'facility': loan,
               'sfPurposeID': purpose['Id'],
               'category': purpose['Category__c'],
               'intention': purpose['Intention__c'],
               'amount': chkVal(purpose['Amount__c']),
               'drawdownAmount': chkVal(purpose['Drawdown_Amount__c']),
               'drawdownFrequency': purpose['Drawdown_Frequency__c'],
               'drawdownStartDate': None,  ###
               'drawdownEndDate': None,  ###
               'planAmount': chkVal(purpose['Plan_Amount__c']),
               'planPeriod': chkVal(purpose['Plan_Period__c']),
               'topUpBuffer': purpose['TopUp_Buffer__c'],
               'description': purpose['Description__c'],
               'notes': purpose['Notes__c'],
               }

    return payload


def chkVal(arg):
    if arg == None:
        return None
    if math.isnan(arg):
        return None
    else:
        return arg