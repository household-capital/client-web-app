import magic

# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.urls import reverse_lazy

from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_DataMapping import serialisePurposes
from apps.lib.site_Enums import loanTypesEnum, dwellingTypesEnum, appTypesEnum, productTypesEnum, incomeFrequencyEnum, stateTypesEnum
from apps.lib.site_Globals import ECONOMIC, APP_SETTINGS, LOAN_LIMITS
from apps.lib.site_Logging import write_applog

from apps.application.models import Application
from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case, LossData, Loan, ModelSetting, LoanPurposes
from apps.enquiry.models import Enquiry
from apps.servicing.models import FacilityEnquiry, Facility



# CLASSES
class HouseholdLoginRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(HouseholdLoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

    # Ensures views will not render unless Household employee, redirects to Landing
    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return super(HouseholdLoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))


class LoginOnlyRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginOnlyRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)


class ReferrerLoginRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(ReferrerLoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

        # Ensures views will not render unless Household employee, redirects to Landing

    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.referrer:
            return super(ReferrerLoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))

def raiseAdminError(title, body):
    msg_title = title
    from_email = settings.DEFAULT_FROM_EMAIL
    to = settings.ADMINS[0][1]
    msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
    msg.send()
    return

def raiseTaskAdminError(title, body):
    msg_title = "[Django] ERROR (Celery Task): " + title
    from_email = settings.DEFAULT_FROM_EMAIL
    to = settings.ADMINS[0][1]
    msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
    msg.send()
    return


# FUNCTIONS

def updateNavQueue(request):
    request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
    request.session['webContQueue'] = WebContact.objects.queueCount()
    request.session['enquiryQueue'] = Enquiry.objects.queueCount()
    request.session['loanEnquiryQueue'] = FacilityEnquiry.objects.queueCount()
    request.session['referrerQueue'] = Case.objects.queueCount()

    # Servicing
    recItems = Facility.objects.filter(amalReconciliation=False, settlementDate__isnull=False).count()
    breachItems = Facility.objects.filter(amalBreach=True, settlementDate__isnull=False).count()
    enquiryItems = FacilityEnquiry.objects.filter(actioned=False).count()

    request.session['servicingQueue'] = max(recItems,enquiryItems, breachItems)

    return


def firstNameSplit(str):
    if " " not in str:
        return str

    firstname, surname = str.split(" ", 1)
    if len(firstname) > 0:
        return firstname
    else:
        return str


def sendTemplateEmail(template_name, email_context, subject, from_email, to, cc=None, bcc=None, attachments=None):
    text_content = "Email Message"
    html = get_template(template_name)
    html_content = html.render(email_context)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to=ensureList(to), bcc=ensureList(bcc),
                                 cc=ensureList(cc))
    msg.attach_alternative(html_content, "text/html")

    #Attached files (if present) - list of tuples (filename, file location)
    if attachments:
        for attachment in attachments:
            if len(attachment) == 3:
               msg = attachFile(msg, attachment[0], attachment[1], attachment[2])
            else:
               msg = attachFile(msg,attachment[0],attachment[1])
    try:
        msg.send()
        return True
    except:
        return False

def attachFile(msg, filename, fileLocation, isStatic=False):

    if isStatic:
        # is a static file
        localfile = staticfiles_storage.open(fileLocation, 'rb')
    else:
        #is a media file
        localfile = default_storage.open(fileLocation, 'rb')

    fileContents = localfile.read()
    mimeType = magic.from_buffer(fileContents,mime=True)
    msg.attach(filename, fileContents, mimeType)

    return msg


def getFileFieldMimeType(fieldObj):

    if hasattr(fieldObj, 'temporary_file_path'):
        # file is temporary on the disk, so we can get full path of it
        mime_type = magic.from_file(fieldObj.temporary_file_path(), mime=True)
    else:
        # file is in memory
        mime_type = magic.from_buffer(fieldObj.read(), mime=True)

    return mime_type



def ensureList(sourceItem):
    return [sourceItem] if type(sourceItem) is str else sourceItem


def createCaseModelSettings(caseUID):
    # Instantiate model settings if required
    qs = ModelSetting.objects.queryset_byUID(caseUID)
    obj = qs.get()
    if not obj.housePriceInflation:
        economicSettings = ECONOMIC.copy()
        economicSettings.pop('defaultMargin')
        economicSettings['establishmentFeeRate'] = LOAN_LIMITS['establishmentFee']
        qs.update(**economicSettings)
    return


def validateLoanGetContext(caseUID):
    # common function to validate a loan and return full context

    loanObj = Loan.objects.queryset_byUID(caseUID).get()

    # get dictionaries from model
    clientDict = Case.objects.dictionary_byUID(caseUID)
    loanDict = Loan.objects.dictionary_byUID(caseUID)
    modelDict = ModelSetting.objects.dictionary_byUID(caseUID)

    # extend loanDict with purposes
    loanDict.update(serialisePurposes(loanObj))
    # also provide purposes dictonary
    purposes = loanObj.get_purposes()

    # validate loan
    loanVal = LoanValidator(clientDict, loanDict, modelDict)
    loanStatus = loanVal.getStatus()

    # update loan

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

        isLowLVR = loanStatus['data']['isLowLVR']
    )

    #Save Variation Amount
    if clientDict['appType'] == appTypesEnum.VARIATION.value:
        loanQS.update(
            variationTotalAmount = max(loanStatus['data']['totalLoanAmount']-loanDict['orgTotalLoanAmount'],0),
            variationPurposeAmount = max(loanStatus['data']['purposeAmount']-loanDict['orgPurposeAmount'],0),
            variationFeeAmount=max(loanStatus['data']['establishmentFee'] - loanDict['orgEstablishmentFee'], 0),
                      )


    # create context
    context = {}
    context.update(clientDict)
    context.update(loanDict)
    context.update(modelDict)
    context.update(loanStatus['data'])
    context['purposes'] = purposes

    # additional enum
    caseObj = Case.objects.queryset_byUID(caseUID).get()
    context['enumState'] = caseObj.enumStateType()
    context['enumChannelType']  = caseObj.enumChannelType()
    context['owner'] = caseObj.owner
    context['enumInvestmentLabel'] = caseObj.enumInvestmentLabel()


    return context

def validateApplicationGetContext(appUID):
    # common function to validate a loan and return full context

    appObj = Application.objects.queryset_byUID(appUID).get()

    # get dictionaries from model
    appDict = Application.objects.dictionary_byUID(appUID)

    # extend appDict with purposes
    appDict.update(serialisePurposes(appObj))

    # also provide purposes dictionary
    purposes = appObj.get_purposes()

    # validate app
    loanVal = LoanValidator(appDict)
    loanStatus = loanVal.getStatus()


    # update loan

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
        isLowLVR = loanStatus['data']['isLowLVR']
    )

    # create context
    context = {}
    context.update(appDict)
    context.update(loanStatus['data'])
    context['purposes'] = purposes

    return context



def getProjectionResults(sourceDict, scenarioList, img_url = None):
    # Loan Projections - calls the Loan Projection class to provide required projection scenarios

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

        # Get point results
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

        context['totalInterestRate'] = sourceDict['interestRate'] + sourceDict['lendingMargin']
        context['comparisonRate'] = context['totalInterestRate'] + sourceDict['comparisonRateIncrement']
        context['loanTypesEnum'] = loanTypesEnum
        context['absolute_media_url'] = settings.MEDIA_URL

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

    obj = Enquiry.objects.queryset_byUID(enqUID).get()
    context={}
    context.update(obj.__dict__)
    context["obj"] = obj

    # Set initial values (given this is an under-specified enquiry)
    context.update(enquiryProductContext(obj))

    #Validate loan to get limit amounts
    loanObj = LoanValidator(context)
    return loanObj.getStatus()

def getEnquiryProjections(enqUID):
    # Wrapper for getProjectionResults
    # Given this is based off enquiry information only, need to enhance inputs to Loan Projection as required

    # Create dictionaries
    obj = Enquiry.objects.queryset_byUID(enqUID).get()
    context={}
    context.update(obj.__dict__)
    context["obj"] = obj

    #Validate loan to get limit amounts
    loanObj = LoanValidator(context)
    loanStatus = loanObj.getStatus()['data']
    context.update(loanStatus)

    context["transfer_img"] = staticfiles_storage.url("img/icons/transfer_" + str(
        context['maxLVRPercentile']) + "_icon.png")

    context['loanTypesEnum'] = loanTypesEnum
    context['dwellingTypesEnum'] = dwellingTypesEnum
    context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL

    # Set initial values (given this is an under-specified enquiry)
    context.update(enquiryProductContext(obj))

    context.update(ECONOMIC)
    context['totalInterestRate'] = ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
    context['housePriceInflation'] = ECONOMIC['housePriceInflation']
    context['comparisonRate'] = context['totalInterestRate'] + ECONOMIC['comparisonRateIncrement']

    # Get Loan Projections
    results = getProjectionResults(context, ['baseScenario'])
    context.update(results)

    return context

def enquiryProductContext(enqObj):
    """Populate enquiry dictionary of initial values based on productType"""

    context={}

    if enqObj.productType == productTypesEnum.LUMP_SUM.value:
        # Override the loan amount to maximum if not provided
        if enqObj.calcLumpSum == None or enqObj.calcLumpSum == 0:
            topUpAmount = enqObj.maxLoanAmount
        else:
            topUpAmount = enqObj.calcLumpSum

        context['topUpAmount'] = int(round(topUpAmount/ (1 + LOAN_LIMITS['establishmentFee']),0))
        context['totalLoanAmount'] = int(round(topUpAmount,0))
        context['totalPlanAmount'] = int(round(topUpAmount,0))

    elif enqObj.productType == productTypesEnum.INCOME.value:

        if enqObj.calcIncome == None or enqObj.calcIncome == 0:
            topUpIncomeAmount = enqObj.maxDrawdownMonthly
        else:
            topUpIncomeAmount = enqObj.calcIncome

        context['topUpIncomeAmount'] = topUpIncomeAmount/ (1 + LOAN_LIMITS['establishmentFee'])
        context['topUpFrequency'] = incomeFrequencyEnum.MONTHLY.value
        context['topUpPlanDrawdowns'] = APP_SETTINGS['incomeProjectionYears'] * 12
        context['topUpContractDrawdowns'] = LOAN_LIMITS['maxDrawdownYears'] * 12
        context["topUpDrawdownAmount"] = int(round(context['topUpIncomeAmount'] * 12 ,0))
        context["topUpPlanAmount"] = int(round(context['topUpIncomeAmount'] * context['topUpPlanDrawdowns'],0))
        
        context['totalLoanAmount'] = int(round(context['topUpContractDrawdowns'] * topUpIncomeAmount, 0))
        context['totalPlanAmount'] = int(round(context['topUpPlanDrawdowns'] * topUpIncomeAmount, 0))



    elif enqObj.productType == productTypesEnum.CONTINGENCY_20K.value:
        context['topUpAmount'] = LOAN_LIMITS['lumpSum20K']/ (1 + LOAN_LIMITS['establishmentFee'])
        context['totalLoanAmount'] = LOAN_LIMITS['lumpSum20K']
        context['totalPlanAmount'] = LOAN_LIMITS['lumpSum20K']


    elif enqObj.productType == productTypesEnum.COMBINATION.value:

        #Income Component
        if enqObj.calcIncome == None or enqObj.calcIncome == 0:
            topUpIncomeAmount = 0
        else:
            topUpIncomeAmount = enqObj.calcIncome

        context['topUpIncomeAmount'] = topUpIncomeAmount / (1 + LOAN_LIMITS['establishmentFee'])
        context['topUpFrequency'] = incomeFrequencyEnum.MONTHLY.value
        context['topUpPlanDrawdowns'] = APP_SETTINGS['incomeProjectionYears'] * 12
        context['topUpContractDrawdowns'] = LOAN_LIMITS['maxDrawdownYears'] * 12
        context["topUpDrawdownAmount"] = int(round(context['topUpIncomeAmount'] * 12, 0))
        context["topUpPlanAmount"] = int(round(context['topUpIncomeAmount'] * context['topUpPlanDrawdowns'], 0))

        totalLoanAmount = context['topUpContractDrawdowns'] * topUpIncomeAmount
        totalPlanAmount = context['topUpPlanDrawdowns'] * topUpIncomeAmount

        #Lump Sum Component

        if enqObj.calcLumpSum == None or enqObj.calcLumpSum == 0:
            topUpAmount = enqObj.maxLoanAmount
        else:
            topUpAmount = enqObj.calcLumpSum

        context['topUpAmount'] = int(round(topUpAmount/ (1 + LOAN_LIMITS['establishmentFee']),0))
        totalLoanAmount += topUpAmount
        totalPlanAmount += topUpAmount

        context['totalLoanAmount'] = totalLoanAmount
        context['totalPlanAmount'] = totalPlanAmount

    return context


def populateDrawdownPurpose(purposeObj):
    # Calculate Amounts and Periods (form specified in years)
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

def cleanPhoneNumber(phone):
    if phone:
        number = phone.replace(" ", "").replace("(", "").replace(")", "").replace("+61", "0").replace("-", "")
        number = remove_prefix(number,"61")
        if number[0:1] != "0":
            return "0"+number
        else:
            return number

def remove_prefix(text, prefix):
    if text.startswith(prefix):
         text = text.replace(prefix, "", 1)
    return text

def checkMobileNumber(number):
    result = cleanPhoneNumber(number)
    if len(result) != 10:
        return False
    if result[0:2] == "04":
        return True
    else:
        result = False


def chkNone(arg):
    return arg if arg else ''