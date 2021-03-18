
# Django Imports
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_DataMapping import serialisePurposes
from apps.lib.site_Enums import loanTypesEnum, dwellingTypesEnum, appTypesEnum, productTypesEnum, incomeFrequencyEnum, clientTypesEnum
from apps.lib.site_Globals import ECONOMIC, APP_SETTINGS, LOAN_LIMITS
from apps.lib.site_Logging import write_applog

from apps.application.models import Application
from apps.case.models import Case, Loan, ModelSetting
from apps.enquiry.models import Enquiry
from apps.lib.site_Utilities import firstNameSplit

from urllib.parse import urljoin


# CORE FUNCTIONS
def validateLoanGetContext(caseUID):
    """ A common function to validate a Case, save calculated summary results and return full context"""

    loanObj = Loan.objects.queryset_byUID(caseUID).get()

    # 1. Get dictionaries from model
    clientDict = Case.objects.dictionary_byUID(caseUID)
    loanDict = Loan.objects.dictionary_byUID(caseUID)
    modelDict = ModelSetting.objects.dictionary_byUID(caseUID)

    # 2. Extend loanDict with purposes
    loanDict.update(serialisePurposes(loanObj))
    # also provide purposes dictonary
    purposes = loanObj.get_purposes()

    # 3. Validate loan
    loanVal = LoanValidator(clientDict, loanDict, modelDict)
    loanStatus = loanVal.getStatus()

    # 4. Update Case
    loanQS = Loan.objects.queryset_byUID(caseUID)
    loanQS.update(

        purposeAmount=loanStatus['data']['purposeAmount'],
        establishmentFee=loanStatus['data']['establishmentFee'],
        totalLoanAmount=loanStatus['data']['totalLoanAmount'],

        planPurposeAmount=loanStatus['data']['planPurposeAmount'],
        planEstablishmentFee=loanStatus['data']['planEstablishmentFee'],
        totalPlanAmount=loanStatus['data']['totalPlanAmount'],

        maxLVR=loanStatus['data']['maxLVR'],
        actualLVR=loanStatus['data']['actualLVR'],
        detailedTitle=loanStatus['data']['detailedTitle'],

        isLowLVR=loanStatus['data']['isLowLVR']
    )

    # Save Variation Amount
    if clientDict['appType'] == appTypesEnum.VARIATION.value:
        loanQS.update(
            variationTotalAmount=max(loanStatus['data']['totalLoanAmount'] - loanDict['orgTotalLoanAmount'], 0),
            variationPurposeAmount=max(loanStatus['data']['purposeAmount'] - loanDict['orgPurposeAmount'], 0),
            variationFeeAmount=max(loanStatus['data']['establishmentFee'] - loanDict['orgEstablishmentFee'], 0),
        )

    # 5. Create context
    context = {}
    context.update(clientDict)
    context.update(loanDict)
    context.update(modelDict)
    context.update(loanStatus['data'])
    context['purposes'] = purposes

    # additional enum
    caseObj = Case.objects.queryset_byUID(caseUID).get()
    context['enumState'] = caseObj.enumStateType()
    context['enumChannelType'] = caseObj.enumChannelType()
    context['owner'] = caseObj.owner
    context['enumInvestmentLabel'] = caseObj.enumInvestmentLabel()

    return context


def validateApplicationGetContext(appUID):
    """A common function to validate a loan application and return full context"""

    appObj = Application.objects.queryset_byUID(appUID).get()

    # 1. Get dictionaries from model
    appDict = Application.objects.dictionary_byUID(appUID)

    # 2. Extend appDict with purposes
    appDict.update(serialisePurposes(appObj))

    # also provide purposes dictionary
    purposes = appObj.get_purposes()

    # 3. Validate app
    loanVal = LoanValidator(appDict)
    loanStatus = loanVal.getStatus()

    # 4. Update app
    appQS = Application.objects.queryset_byUID(appUID)
    appQS.update(

        purposeAmount=loanStatus['data']['purposeAmount'],
        establishmentFee=loanStatus['data']['establishmentFee'],
        totalLoanAmount=loanStatus['data']['totalLoanAmount'],

        planPurposeAmount=loanStatus['data']['planPurposeAmount'],
        planEstablishmentFee=loanStatus['data']['planEstablishmentFee'],
        totalPlanAmount=loanStatus['data']['totalPlanAmount'],

        maxLVR=loanStatus['data']['maxLVR'],
        actualLVR=loanStatus['data']['actualLVR'],
        isLowLVR=loanStatus['data']['isLowLVR']
    )

    # create context
    context = {}
    context.update(appDict)
    context.update(loanStatus['data'])
    context['purposes'] = purposes

    return context


def getProjectionResults(sourceDict, scenarioList, img_url=None):
    """ Builds required projections by calling the Loan Projection class with appropriate state shocks

    This is a CORE function that is used to retrieve projection results throughout the clientApp

    """

    if img_url == None:
        img_url = 'img/icons/block_equity_{0}_icon.png'

    loanProj = LoanProjection()
    result = loanProj.create(sourceDict)
    if result['status'] == "Error":
        write_applog("ERROR", 'site_utilities', 'getProjectionResults', result['responseText'])
        return

    result = loanProj.calcProjections()
    if result['status'] == "Error":
        write_applog("ERROR", 'site_utilities', 'getProjectionResults', result['responseText'])
        return

    context = {}

    if 'pointScenario' in scenarioList:
        # Get point results - as required by ASIC projections

        period1, period2 = loanProj.getAsicProjectionPeriods()

        results = loanProj.getPeriodResults(period1)
        context['pointYears1'] = period1
        context['pointAge1'] = int(round(results['BOPAge'], 0))
        context['pointHouseValue1'] = int(round(results['BOPHouseValue'], 0))
        context['pointLoanValue1'] = int(round(results['BOPLoanValue'], 0))
        context['pointHomeEquity1'] = int(round(results['BOPHomeEquity'], 0))
        context['pointHomeEquityPC1'] = int(round(results['BOPHomeEquityPC'], 0))
        context['pointImage1'] = staticfiles_storage.url('img/icons/result_{0}_icon.png'.format(
            results['HomeEquityPercentile']))

        results = loanProj.getPeriodResults(period2)
        context['pointYears2'] = period2
        context['pointAge2'] = int(round(results['BOPAge'], 0))
        context['pointHouseValue2'] = int(round(results['BOPHouseValue'], 0))
        context['pointLoanValue2'] = int(round(results['BOPLoanValue'], 0))
        context['pointHomeEquity2'] = int(round(results['BOPHomeEquity'], 0))
        context['pointHomeEquityPC2'] = int(round(results['BOPHomeEquityPC'], 0))
        context['pointImage2'] = staticfiles_storage.url('img/icons/result_{0}_icon.png'.format(
            results['HomeEquityPercentile']))

    if 'baseScenario' in scenarioList:

        # Build results dictionaries
        context['resultsAge'] = loanProj.getResultsList('BOPAge')['data']
        context['resultsLoanBalance'] = loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity'] = loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages'] = \
            loanProj.getImageList('BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
            'data']

        context['totalInterestRate'] = round(sourceDict['interestRate'] + sourceDict['lendingMargin'], 2)
        context['comparisonRate'] = round(context['totalInterestRate'] + sourceDict['comparisonRateIncrement'], 2)
        context['loanTypesEnum'] = loanTypesEnum
        context['clientTypesEnum'] = clientTypesEnum

        if 'firstname_1' not in sourceDict:
            if sourceDict['loanType'] == loanTypesEnum.JOINT_BORROWER.value:
                context['ageAxis'] = "Youngest borrower's age"
            else:
                context['ageAxis'] = "Your age"
        else:
            if sourceDict['loanType'] == loanTypesEnum.JOINT_BORROWER.value:
                if sourceDict['age_1'] < sourceDict['age_2']:
                    context['ageAxis'] = firstNameSplit(sourceDict['firstname_1']) + "'s age"
                    context['personLabel'] = firstNameSplit(sourceDict['firstname_1']) + " is"
                else:
                    context['ageAxis'] = firstNameSplit(sourceDict['firstname_2']) + "'s age"
                    context['personLabel'] = firstNameSplit(sourceDict['firstname_2']) + " is"
            else:
                context['ageAxis'] = "Your age"
                context['personLabel'] = "you are"

        context['cumLumpSum'] = loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular'] = loanProj.getResultsList('CumRegular')['data']
        context['cumFee'] = loanProj.getResultsList('CumFee')['data']
        context['cumDrawn'] = loanProj.getResultsList('CumDrawn')['data']
        context['cumInt'] = loanProj.getResultsList('CumInt')['data']

    if 'incomeScenario' in scenarioList:
        # Determine whether there is an income Scenario
        context['topUpProjections'] = False
        topUpDrawdown = None
        careDrawdown = None

        # Only show if top-up income
        if "TOP_UP" in sourceDict['purposes']:
            if "REGULAR_DRAWDOWN" in sourceDict['purposes']["TOP_UP"]:
                topUpDrawdown = sourceDict['purposes']["TOP_UP"]["REGULAR_DRAWDOWN"]
                if topUpDrawdown.amount != 0:
                    context['topUpProjections'] = True

        if "CARE" in sourceDict['purposes']:
            if "REGULAR_DRAWDOWN" in sourceDict['purposes']["CARE"]:
                careDrawdown = sourceDict['purposes']["CARE"]["REGULAR_DRAWDOWN"]

        if context['topUpProjections'] == True:
            context['resultsTotalIncome'] = loanProj.getResultsList('TotalIncome', imageSize=150, imageMethod='lin')[
                'data']
            context['resultsIncomeImages'] = \
                loanProj.getImageList('PensionIncomePC', 'img/icons/income_{0}_icon.png')['data']

            if topUpDrawdown:
                context["totalDrawdownAmount"] = topUpDrawdown.amount
                context["totalDrawdownPlanAmount"] = topUpDrawdown.planAmount

            # However, if showing top-up income, also show care income
            if careDrawdown:
                context["totalDrawdownAmount"] += careDrawdown.amount
                context["totalDrawdownPlanAmount"] += careDrawdown.planAmount
    else:
        context['topUpProjections'] = False

    if 'stressScenario' in scenarioList:
        # Stress-2
        result = loanProj.calcProjections(hpiStressLevel=APP_SETTINGS['hpiHighStressLevel'])
        context['hpi2'] = APP_SETTINGS['hpiHighStressLevel']
        context['intRate2'] = context['totalInterestRate']

        context['resultsLoanBalance2'] = loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity2'] = loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC2'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages2'] = \
            loanProj.getImageList('BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue2'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
            'data']
        context['cumLumpSum2'] = loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular2'] = loanProj.getResultsList('CumRegular')['data']
        context['cumFee2'] = loanProj.getResultsList('CumFee')['data']
        context['cumDrawn2'] = loanProj.getResultsList('CumDrawn')['data']
        context['cumInt2'] = loanProj.getResultsList('CumInt')['data']

        # Stress-3
        result = loanProj.calcProjections(intRateStress=APP_SETTINGS['intRateStress'])
        context['hpi3'] = sourceDict['housePriceInflation']
        context['intRate3'] = context['totalInterestRate'] + APP_SETTINGS['intRateStress']

        context['resultsLoanBalance3'] = loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity3'] = loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC3'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages3'] = \
            loanProj.getImageList('BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue3'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
            'data']
        context['cumLumpSum3'] = loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular3'] = loanProj.getResultsList('CumRegular')['data']
        context['cumFee3'] = loanProj.getResultsList('CumFee')['data']
        context['cumDrawn3'] = loanProj.getResultsList('CumDrawn')['data']
        context['cumInt3'] = loanProj.getResultsList('CumInt')['data']

    if 'intPayScenario' in scenarioList:
        # Stress-4
        result = loanProj.calcProjections(makeIntPayment=True)
        context['resultsLoanBalance4'] = loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity4'] = loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC4'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages4'] = \
            loanProj.getImageList('BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue4'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
            'data']
        context['cumLumpSum4'] = loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular4'] = loanProj.getResultsList('CumRegular')['data']
        context['cumFee4'] = loanProj.getResultsList('CumFee')['data']
        context['cumDrawn4'] = loanProj.getResultsList('CumDrawn')['data']
        context['cumInt4'] = loanProj.getResultsList('CumInt')['data']

    return context


def validateEnquiry(enqUID):
    """Wrapper utility to enable validator to be used with under-specified enquiry """
    obj = Enquiry.objects.queryset_byUID(enqUID).get()
    context = {}
    context.update(obj.__dict__)
    context["obj"] = obj

    # Set initial values (given this is an under-specified enquiry) based on product
    context.update(enquiryProductContext(obj))

    # Validate loan to get limit amounts
    loanObj = LoanValidator(context)
    return loanObj.getStatus()


def getEnquiryProjections(enqUID):
    """Wrapper for using enquiries with getProjectionResults
    Given this is based off enquiry information only, need to enhance inputs to Loan Projection as required
    """

    # Create dictionaries
    obj = Enquiry.objects.queryset_byUID(enqUID).get()
    context = {}
    context.update(obj.__dict__)
    context["obj"] = obj

    # Validate loan to get limit amounts
    loanObj = LoanValidator(context)
    loanStatus = loanObj.getStatus()['data']
    context.update(loanStatus)

    context["transfer_img"] = staticfiles_storage.url("img/icons/transfer_" + str(
        context['maxLVRPercentile']) + "_icon.png")

    context['loanTypesEnum'] = loanTypesEnum
    context['dwellingTypesEnum'] = dwellingTypesEnum
    context['absolute_url'] = urljoin(
        settings.SITE_URL,
        settings.STATIC_URL
    )

    # Set initial values (given this is an under-specified enquiry)
    context.update(enquiryProductContext(obj))

    context.update(ECONOMIC)
    context['totalInterestRate'] = round(ECONOMIC['interestRate'] + ECONOMIC['lendingMargin'], 2)
    context['housePriceInflation'] = ECONOMIC['housePriceInflation']
    context['comparisonRate'] = round(context['totalInterestRate'] + ECONOMIC['comparisonRateIncrement'], 2)

    # Get Loan Projections
    results = getProjectionResults(context, ['baseScenario'])
    context.update(results)

    return context


def enquiryProductContext(enqObj):
    """Populate enquiry dictionary of initial values based on productType"""

    context = {}

    if enqObj.productType == productTypesEnum.LUMP_SUM.value:
        # Override the loan amount to maximum if not provided
        if enqObj.calcLumpSum == None or enqObj.calcLumpSum == 0:
            topUpAmount = enqObj.maxLoanAmount
        else:
            topUpAmount = enqObj.calcLumpSum

        context['topUpAmount'] = int(round(topUpAmount / (1 + LOAN_LIMITS['establishmentFee']), 0))
        context['totalLoanAmount'] = int(round(topUpAmount, 0))
        context['totalPlanAmount'] = int(round(topUpAmount, 0))

    elif enqObj.productType == productTypesEnum.REFINANCE.value:
        # Override the loan amount to maximum if not provided
        if enqObj.calcLumpSum == None or enqObj.calcLumpSum == 0:
            topUpAmount = enqObj.mortgageDebt if enqObj.mortgageDebt else LOAN_LIMITS['minLoanSize']
        else:
            topUpAmount = enqObj.calcLumpSum

        context['topUpAmount'] = int(round(topUpAmount, 0))
        context['totalLoanAmount'] = int(round(topUpAmount * (1 + LOAN_LIMITS['establishmentFee']), 0))
        context['totalPlanAmount'] = int(round(topUpAmount * (1 + LOAN_LIMITS['establishmentFee']), 0))

    elif enqObj.productType == productTypesEnum.INCOME.value:

        if enqObj.calcIncome == None or enqObj.calcIncome == 0:
            topUpIncomeAmount = enqObj.maxDrawdownMonthly
        else:
            topUpIncomeAmount = enqObj.calcIncome

        context['totalTopUpIncomeAmount'] = int(round(topUpIncomeAmount, 0))
        context['topUpIncomeAmount'] = topUpIncomeAmount / (1 + LOAN_LIMITS['establishmentFee'])
        context['topUpFrequency'] = incomeFrequencyEnum.MONTHLY.value
        context['topUpPlanDrawdowns'] = APP_SETTINGS['incomeProjectionYears'] * 12
        context['topUpContractDrawdowns'] = LOAN_LIMITS['maxDrawdownYears'] * 12
        context["topUpDrawdownAmount"] = int(round(context['topUpIncomeAmount'] * 12, 0))
        context["topUpPlanAmount"] = int(round(context['topUpIncomeAmount'] * context['topUpPlanDrawdowns'], 0))

        context['totalLoanAmount'] = int(round(context['topUpContractDrawdowns'] * topUpIncomeAmount, 0))
        context['totalPlanAmount'] = int(round(context['topUpPlanDrawdowns'] * topUpIncomeAmount, 0))


    elif enqObj.productType == productTypesEnum.CONTINGENCY_20K.value:
        context['topUpAmount'] = LOAN_LIMITS['lumpSum20K'] / (1 + LOAN_LIMITS['establishmentFee'])
        context['totalLoanAmount'] = LOAN_LIMITS['lumpSum20K']
        context['totalPlanAmount'] = LOAN_LIMITS['lumpSum20K']

    elif enqObj.productType == productTypesEnum.COMBINATION.value:

        # Income Component
        if enqObj.calcIncome == None or enqObj.calcIncome == 0:
            topUpIncomeAmount = 0
        else:
            topUpIncomeAmount = enqObj.calcIncome

        context['totalTopUpIncomeAmount'] = int(round(topUpIncomeAmount, 0))
        context['topUpIncomeAmount'] = topUpIncomeAmount / (1 + LOAN_LIMITS['establishmentFee'])
        context['topUpFrequency'] = incomeFrequencyEnum.MONTHLY.value
        context['topUpPlanDrawdowns'] = APP_SETTINGS['incomeProjectionYears'] * 12
        context['topUpContractDrawdowns'] = LOAN_LIMITS['maxDrawdownYears'] * 12
        context["topUpDrawdownAmount"] = int(round(context['topUpIncomeAmount'] * 12, 0))
        context["topUpPlanAmount"] = int(round(context['topUpIncomeAmount'] * context['topUpPlanDrawdowns'], 0))

        totalLoanAmount = context['topUpContractDrawdowns'] * topUpIncomeAmount
        totalPlanAmount = context['topUpPlanDrawdowns'] * topUpIncomeAmount

        # Lump Sum Component

        if enqObj.calcLumpSum == None or enqObj.calcLumpSum == 0:
            topUpAmount = enqObj.maxLoanAmount
        else:
            topUpAmount = enqObj.calcLumpSum

        context['totalTopUpAmount'] = int(round(topUpAmount, 0))
        context['topUpAmount'] = int(round(topUpAmount / (1 + LOAN_LIMITS['establishmentFee']), 0))
        totalLoanAmount += topUpAmount
        totalPlanAmount += topUpAmount

        context['totalLoanAmount'] = totalLoanAmount
        context['totalPlanAmount'] = totalPlanAmount

    return context


def populateDrawdownPurpose(purposeObj):
    """Calculate amounts and periods (based on simple year specification)"""

    if purposeObj.drawdownFrequency == incomeFrequencyEnum.FORTNIGHTLY.value:
        freqMultiple = 26
    else:
        freqMultiple = 12

    # Contract for lower of limit or plan period
    planDrawdowns = purposeObj.planPeriod * freqMultiple
    contractDrawdowns = min(purposeObj.planPeriod * freqMultiple, LOAN_LIMITS['maxDrawdownYears'] * freqMultiple)
    purposeObj.planDrawdowns = planDrawdowns

    purposeObj.contractDrawdowns = contractDrawdowns
    purposeObj.planAmount = purposeObj.drawdownAmount * planDrawdowns
    purposeObj.amount = purposeObj.drawdownAmount * contractDrawdowns

    return purposeObj
