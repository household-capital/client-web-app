from math import log
# Django Imports
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_DataMapping import serialisePurposes
from apps.lib.site_Enums import loanTypesEnum, dwellingTypesEnum, appTypesEnum, productTypesEnum, incomeFrequencyEnum, clientTypesEnum
from apps.lib.site_Globals import ECONOMIC, APP_SETTINGS, LOAN_LIMITS
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import firstNameSplit, loan_api_response, get_loan_status

from apps.application.models import Application
from apps.case.models import Case, Loan, ModelSetting
from apps.enquiry.models import Enquiry

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
    # loanVal = LoanValidator(clientDict, loanDict, modelDict)
    # loanStatus = loanVal.getStatus()

    loanStatus = get_loan_status({**clientDict, **loanDict, **modelDict}, loanDict['product_type'])

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
    loanStatus = get_loan_status(appDict) 

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


def getAsicProjectionPeriodsFromSourceDict(sourceDict):
    minProjectionAge = 90
    minProjectionYears = 10
    if sourceDict['loanType'] == loanTypesEnum.SINGLE_BORROWER.value:
        minAge = sourceDict['age_1']
    else:
        if sourceDict.get('age_2'): 
            minAge = min(sourceDict['age_1'], sourceDict['age_2'])
        else:
            return None, None
    projectionAge = max(minProjectionAge, minAge + minProjectionYears)
    projectionYears = projectionAge - minProjectionYears
    if minAge < 75:
        asicProjAge1 = minAge + 15
    elif minAge < 80:
        asicProjAge1 = minAge + 10
    else:
        asicProjAge1 = minAge + 5

    asicProjAge2 = projectionAge
    return asicProjAge1 - minAge, asicProjAge2 - minAge

def myround(val, base=5):
    if val == 100:
        return 100
    else:
        #Floor of 2% for graph purposes
        return min(base * round(val / base), 98)

def getPeriodResultsCalcArray(calcArray, period, **kwargs):
    """Returns results for specific period"""


    if len(calcArray) == 0:
        return {'status': 'Error', 'responseText': 'Projections not calculated'}

    results = calcArray[period * 12]
    home_equity_percentile = str(int(myround(results['BOPHomeEquityPC'], 5)))

    return calcArray[period * 12], home_equity_percentile

def getResultsListCalcArray(calcArray, keyName, **kwargs):
    """Returns results list for keyName
    * standard result points 0, 5, 10 and 15 years
    * primarily for used to pass to templates in Django views
    * optionally calculates scaling for images
        """
    def logOrZero(val):
        if val <= 0:
            return 0
        return log(val)

    if len(calcArray) == 0:
        return {'status': 'Error', 'responseText': 'Projections not calculated'}

    scaleList = []

    if 'Income' in keyName:
        # Flow variables (next 12 months)
        figuresList = []
        for period in [0, 5, 10, 15]:
            income = 0
            for subPeriod in range(12):
                income += calcArray[(period * 12) + subPeriod + 1][keyName]

            figuresList.append(int(round(income, 0)))
    else:
        # Stock variables (point in time)
        figuresList = [int(round(calcArray[i * 12][keyName], 0)) for i in [0, 5, 10, 15]]

    if 'imageSize' in kwargs:
        if kwargs['imageMethod'] == 'exp':
            # Use a log scaling method for images (arbitrary)
            maxValueLog = logOrZero(max(figuresList)) ** 3
            if maxValueLog == 0:
                maxValueLog = 1
            scaleList = [int(logOrZero(figuresList[i]) ** 3 / maxValueLog * kwargs['imageSize']) for i
                            in range(4)]
        elif kwargs['imageMethod'] == 'lin':
            maxValueLog = max(figuresList)
            scaleList = [int(figuresList[i] / maxValueLog * kwargs['imageSize']) for i in range(4)]

    return {'status': 'Ok', 'data': figuresList + scaleList}

def getImageListCalcArray(calcArray, keyName, imageURL):
    """Returns populated image list for specific keyName"""

    if len(calcArray) == 0:
        return {'status': 'Error', 'responseText': 'Projections not calculated'}

    figuresList = getResultsListCalcArray(calcArray, keyName)['data'] #self.getResultsList(keyName)['data']
    imageList = [staticfiles_storage.url(imageURL.replace('{0}', str(int(myround(figuresList[i], 5))))) for i in range(4)]

    return {'status': 'Ok', 'data': imageList}


def getProjectionResults(sourceDict, scenarioList, img_url=None):
    """ Builds required projections by calling the Loan Projection class with appropriate state shocks

    This is a CORE function that is used to retrieve projection results throughout the clientApp

    """

    if img_url == None:
        img_url = 'img/icons/block_equity_{0}_icon.png'
    
    loanProj = LoanProjection()
    result = loanProj.create(sourceDict)
    _product_type = sourceDict.get('product_type', 'HHC.RM.2021')
    _source_dict = sourceDict.copy()
    _source_dict.update(
        {
            'years': 15,
            "product": _product_type
        }
    )
    calcArray = loan_api_response(
        "/api/calc/v1/proj/primary",
        _source_dict,
        {
            'years': 15,
            "product": _product_type
        }
    )
    result = loanProj.calcProjections()

    # if result['status'] == "Error":
    #     write_applog("ERROR", 'site_utilities', 'getProjectionResults', result['responseText'])
    #     return

    # result = loanProj.calcProjections()
    # if result['status'] == "Error":
    #     write_applog("ERROR", 'site_utilities', 'getProjectionResults', result['responseText'])
    #     return

    context = {}

    if 'pointScenario' in scenarioList:
        # Get point results - as required by ASIC projections

        period1, period2 = getAsicProjectionPeriodsFromSourceDict(sourceDict) # loanProj.getAsicProjectionPeriods()

        results, home_equity_percentile = getPeriodResultsCalcArray(calcArray, period1) # loanProj.getPeriodResults(period1)
        context['pointYears1'] = period1
        context['pointAge1'] = int(round(results['BOPAge'], 0))
        context['pointHouseValue1'] = int(round(results['BOPHouseValue'], 0))
        context['pointLoanValue1'] = int(round(results['BOPLoanValue'], 0))
        context['pointHomeEquity1'] = int(round(results['BOPHomeEquity'], 0))
        context['pointHomeEquityPC1'] = int(round(results['BOPHomeEquityPC'], 0))
        context['pointImage1'] = staticfiles_storage.url('img/icons/result_{0}_icon.png'.format(home_equity_percentile))

        results, home_equity_percentile = getPeriodResultsCalcArray(calcArray, period2) # loanProj.getPeriodResults(period2)
        context['pointYears2'] = period2
        context['pointAge2'] = int(round(results['BOPAge'], 0))
        context['pointHouseValue2'] = int(round(results['BOPHouseValue'], 0))
        context['pointLoanValue2'] = int(round(results['BOPLoanValue'], 0))
        context['pointHomeEquity2'] = int(round(results['BOPHomeEquity'], 0))
        context['pointHomeEquityPC2'] = int(round(results['BOPHomeEquityPC'], 0))
        context['pointImage2'] = staticfiles_storage.url('img/icons/result_{0}_icon.png'.format(home_equity_percentile))

    if 'baseScenario' in scenarioList:

        # Build results dictionaries
        context['resultsAge'] = getResultsListCalcArray(calcArray, 'BOPAge')['data'] # loanProj.getResultsList('BOPAge')['data']
        context['resultsLoanBalance'] = getResultsListCalcArray(calcArray, 'BOPLoanValue')['data'] #loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity'] = getResultsListCalcArray(calcArray, 'BOPHomeEquity')['data'] #loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC'] = getResultsListCalcArray(calcArray, 'BOPHomeEquityPC')['data'] #loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages'] =  getImageListCalcArray(calcArray, 'BOPHomeEquityPC', img_url)['data'] #loanProj.getImageList('BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue'] = getResultsListCalcArray(calcArray, 'BOPHouseValue', imageSize=110, imageMethod='lin')['data'] #loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')['data']

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

        context['cumLumpSum'] = getResultsListCalcArray(calcArray, 'CumLumpSum')['data'] # loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular'] = getResultsListCalcArray(calcArray, 'CumRegular')['data'] # loanProj.getResultsList('CumRegular')['data']
        context['cumFee'] = getResultsListCalcArray(calcArray, 'CumFee')['data'] # loanProj.getResultsList('CumFee')['data']
        context['cumDrawn'] = getResultsListCalcArray(calcArray, 'CumDrawn')['data'] #loanProj.getResultsList('CumDrawn')['data']
        context['cumInt'] = getResultsListCalcArray(calcArray, 'CumInt')['data'] #loanProj.getResultsList('CumInt')['data']

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
            context['resultsTotalIncome'] = getResultsListCalcArray(calcArray, 'TotalIncome', imageSize=150, imageMethod='lin')['data'] # loanProj.getResultsList('TotalIncome', imageSize=150, imageMethod='lin')[ 'data']
            context['resultsIncomeImages'] = \
                getImageListCalcArray(calcArray, 'PensionIncomePC', 'img/icons/income_{0}_icon.png')['data']

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
        _source_dict = sourceDict.copy()
        _source_dict.update(
            {
                "hpiStressLevel": APP_SETTINGS['hpiHighStressLevel'],
                "product": _product_type
            }
        )
        calcArray = loan_api_response(
            "/api/calc/v1/proj/primary",
            _source_dict,
            {
                "hpiStressLevel": APP_SETTINGS['hpiHighStressLevel'],
                "product": _product_type
            }
        )
        # result = loanProj.calcProjections(hpiStressLevel=APP_SETTINGS['hpiHighStressLevel'])
        context['hpi2'] = APP_SETTINGS['hpiHighStressLevel']
        context['intRate2'] = context['totalInterestRate']

        context['resultsLoanBalance2'] =  getResultsListCalcArray(calcArray, 'BOPLoanValue')['data']# loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity2'] = getResultsListCalcArray(calcArray, 'BOPHomeEquity')['data'] # loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC2'] = getResultsListCalcArray(calcArray, 'BOPHomeEquityPC')['data'] #loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages2'] = getImageListCalcArray(calcArray, 'BOPHomeEquityPC', img_url)['data'] #loanProj.getImageList('BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue2'] = getResultsListCalcArray(calcArray,'BOPHouseValue', imageSize=110, imageMethod='lin')['data'] # loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')['data']
        context['cumLumpSum2'] = getResultsListCalcArray(calcArray, 'CumLumpSum')['data'] # loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular2'] = getResultsListCalcArray(calcArray, 'CumRegular')['data'] # loanProj.getResultsList('CumRegular')['data']
        context['cumFee2'] = getResultsListCalcArray(calcArray, 'CumFee')['data'] # loanProj.getResultsList('CumFee')['data']
        context['cumDrawn2'] = getResultsListCalcArray(calcArray, 'CumDrawn')['data'] # loanProj.getResultsList('CumDrawn')['data']
        context['cumInt2'] = getResultsListCalcArray(calcArray, 'CumInt')['data'] # loanProj.getResultsList('CumInt')['data']

        # Stress-3
        # result = loanProj.calcProjections(intRateStress=APP_SETTINGS['intRateStress'])
        _source_dict = sourceDict.copy()
        _source_dict.update(
            {
                "intRateStress": APP_SETTINGS['intRateStress'],
                "product": _product_type
            }
        )
        calcArray = loan_api_response(
            "/api/calc/v1/proj/primary",
            _source_dict,
            {
                "intRateStress": APP_SETTINGS['intRateStress'],
                "product": _product_type
            }
        )

        context['hpi3'] = sourceDict['housePriceInflation']
        context['intRate3'] = context['totalInterestRate'] + APP_SETTINGS['intRateStress']

        context['resultsLoanBalance3'] = getResultsListCalcArray(calcArray, 'BOPLoanValue')['data'] # loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity3'] = getResultsListCalcArray(calcArray, 'BOPHomeEquity')['data'] # loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC3'] = getResultsListCalcArray(calcArray, 'BOPHomeEquityPC')['data'] # loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages3'] = getImageListCalcArray(calcArray, 'BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue3'] = getResultsListCalcArray(calcArray, 'BOPHouseValue', imageSize=110, imageMethod='lin')['data'] # loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')['data']
        context['cumLumpSum3'] = getResultsListCalcArray(calcArray, 'CumLumpSum')['data'] # loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular3'] = getResultsListCalcArray(calcArray, 'CumRegular')['data'] # loanProj.getResultsList('CumRegular')['data']
        context['cumFee3'] = getResultsListCalcArray(calcArray, 'CumFee')['data'] # loanProj.getResultsList('CumFee')['data']
        context['cumDrawn3'] = getResultsListCalcArray(calcArray, 'CumDrawn')['data'] # loanProj.getResultsList('CumDrawn')['data']
        context['cumInt3' ] = getResultsListCalcArray(calcArray, 'CumInt')['data'] # loanProj.getResultsList('CumInt')['data']

    if 'intPayScenario' in scenarioList:
        # Stress-4
        # result = loanProj.calcProjections(makeIntPayment=True)
        # sourceDict['makeIntPayment'] = True
        _source_dict = sourceDict.copy()
        _source_dict['makeIntPayment'] = True
        calcArray = loan_api_response(
            "/api/calc/v1/proj/primary",
            _source_dict,
            {
                "makeIntPayment": True,
                "product": _product_type
            }
        )
        context['resultsLoanBalance4'] = getResultsListCalcArray(calcArray, 'BOPLoanValue')['data'] # loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity4'] = getResultsListCalcArray(calcArray, 'BOPHomeEquity')['data'] # loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC4'] = getResultsListCalcArray(calcArray, 'BOPHomeEquityPC')['data'] # loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages4'] = getImageListCalcArray(calcArray, 'BOPHomeEquityPC', img_url)['data']# loanProj.getImageList('BOPHomeEquityPC', img_url)['data']
        context['resultsHouseValue4'] = getResultsListCalcArray(calcArray, 'BOPHouseValue', imageSize=110, imageMethod='lin')['data']# loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')['data']
        context['cumLumpSum4'] = getResultsListCalcArray(calcArray, 'CumLumpSum')['data'] # loanProj.getResultsList('CumLumpSum')['data']
        context['cumRegular4'] = getResultsListCalcArray(calcArray, 'CumRegular')['data'] # loanProj.getResultsList('CumRegular')['data']
        context['cumFee4'] = getResultsListCalcArray(calcArray, 'CumFee')['data'] #loanProj.getResultsList('CumFee')['data']
        context['cumDrawn4'] = getResultsListCalcArray(calcArray, 'CumDrawn')['data'] # loanProj.getResultsList('CumDrawn')['data']
        context['cumInt4'] = getResultsListCalcArray(calcArray, 'CumInt')['data'] # loanProj.getResultsList('CumInt')['data']

    return context


def validateLead(caseUID):
    obj = Case.objects.get(caseUID=caseUID)
    context = {}
    context.update(obj.__dict__)
    context["obj"] = obj

    # Set initial values (given this is an under-specified enquiry) based on product
    context.update(enquiryProductContext(obj))

    # Validate loan to get limit amounts
    return get_loan_status(context, obj.loan.product_type)


def validateEnquiry(enqUID):
    """Wrapper utility to enable validator to be used with under-specified enquiry """
    obj = Enquiry.objects.queryset_byUID(enqUID).get()
    context = {}
    context.update(obj.__dict__)
    context["obj"] = obj

    # Set initial values (given this is an under-specified enquiry) based on product
    context.update(enquiryProductContext(obj))

    # Validate loan to get limit amounts
    return get_loan_status(context, obj.product_type)


def getCaseProjections(caseUID):
    obj = Case.objects.get(caseUID=caseUID)
    context = {}
    context.update(obj.__dict__)
    obj.user = obj.owner
    context['obj'] = obj

    loanStatus = get_loan_status(context, obj.loan.product_type)['data']
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
    
    loanStatus = get_loan_status(context, obj.product_type)['data']
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
