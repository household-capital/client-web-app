#Python imports
import uuid
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db.models.signals import post_save
from django.db import models
from django.utils.encoding import smart_text
from django.utils import timezone
from django.urls import reverse_lazy

#Local Application Imports
from apps.lib.site_Enums import caseStagesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,\
    pensionTypesEnum, loanTypesEnum, ragTypesEnum, channelTypesEnum, stateTypesEnum, incomeFrequencyEnum, \
    closeReasonEnum, salutationEnum, maritalEnum, appTypesEnum, purposeCategoryEnum, purposeIntentionEnum

from apps.accounts.models import Referer

from apps.accounts.models import Referer


class FundDetail(models.Model):
    #Model for Fund Names/Images
    fundID=models.AutoField(primary_key=True)
    fundName=models.CharField(max_length=30,blank=False, null=False)
    fundImage = models.ImageField(null=False, blank=False, upload_to='fundImages')

    def __str__(self):
        return smart_text(self.fundName)

    def __unicode__(self):
        return smart_text(self.fundName)

    class Meta:
        ordering = ('fundName',)
        verbose_name_plural = "Superfund Definitions"


class CaseManager(models.Manager):

    #Custom model manager to return related querysets (using UID)
    def queryset_byUID(self,uidString):
       if self.model.__name__=='Case':
            searchCase=Case.objects.get(caseUID=uuid.UUID(uidString)).caseID
            return super(CaseManager,self).filter(caseID=searchCase)
       else:
           searchCase = Case.objects.get(caseUID=uuid.UUID(uidString))
           return super(CaseManager, self).filter(case=searchCase)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

    # Custom data queries
    def openCases(self):
        closedTypes = [caseStagesEnum.CLOSED.value, caseStagesEnum.FUNDED.value]
        return Case.objects.exclude(caseStage__in=closedTypes)

    def referrerQueueCount(self):
        return Case.objects.filter(user__profile__referrer__isnull=False).count()


class Case(models.Model):
    # Main model - extended by Loan, ModelSettings and LossData

    appTypes = (
        (appTypesEnum.NEW_APPLICATION.value, "Application"),
        (appTypesEnum.VARIATION.value, "Variation"),
    )

    caseStages=(
                  (caseStagesEnum.DISCOVERY.value,"Discovery"),
                  (caseStagesEnum.MEETING_HELD.value, "Meeting Held"),
                  (caseStagesEnum.APPLICATION.value, "Application"),
                  (caseStagesEnum.DOCUMENTATION.value, "Documentation"),
                  (caseStagesEnum.FUNDED.value, "Funded"),
                  (caseStagesEnum.CLOSED.value, "Closed"),    )

    clientTypes=(
        (clientTypesEnum.BORROWER.value, 'Borrower'),
        (clientTypesEnum.NOMINATED_OCCUPANT.value, 'Nominated Occupant'),
        (clientTypesEnum.PERMITTED_COHABITANT.value, 'Permitted Cohabitant'),
        (clientTypesEnum.POWER_OF_ATTORNEY.value, 'Power of Attorney'),
    )

    clientSex=(
        (clientSexEnum.FEMALE.value, 'Female'),
        (clientSexEnum.MALE.value, 'Male'))

    dwellingTypes=(
        (dwellingTypesEnum.HOUSE.value, 'House'),
        (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    pensionTypes=(
        (pensionTypesEnum.FULL_PENSION.value, 'Full'),
        (pensionTypesEnum.PARTIAL_PENSION.value, 'Partial'),
        (pensionTypesEnum.NO_PENSION.value, 'None')
    )

    loanTypes=(
        (loanTypesEnum.SINGLE_BORROWER.value,'Single'),
        (loanTypesEnum.JOINT_BORROWER.value,'Joint')
    )

    channelTypes=(
        (channelTypesEnum.IND_FINANCIAL_ADVISERS.value, "Independent Financial Advisers"),
        (channelTypesEnum.INST_FINANCIAL_ADVISERS.value, "Institutional Financial Advisers"),
        (channelTypesEnum.SUPER_FINANCIAL_ADVISERS.value, "Super Financial Advisers"),
        (channelTypesEnum.AGED_CARE_ADVISERS.value, "Aged Care Advisers"),
        (channelTypesEnum.AGED_CARE_PROVIDERS_CONSULTANTS.value, "Aged Care Provider/Consultants"),
        (channelTypesEnum.ACCOUNTANTS.value, "Accountants"),
        (channelTypesEnum.CENTRELINK_ADVISERS.value, "Centrelink Advisers"),
        (channelTypesEnum.BROKERS.value, "Brokers"),
        (channelTypesEnum.BANK_REFERRAL.value, "Bank Referral"),
        (channelTypesEnum.BANK_REFI.value, "Refinance"),
        (channelTypesEnum.SUPER_MEMBERS_DIRECT.value, "Super Direct"),
        (channelTypesEnum.DIRECT_ACQUISITION.value, "Direct Acquisition")
    )

    stateTypes=(
        (stateTypesEnum.NSW.value, "NSW"),
        (stateTypesEnum.VIC.value, "VIC"),
        (stateTypesEnum.ACT.value, "ACT"),
        (stateTypesEnum.QLD.value, "QLD"),
        (stateTypesEnum.SA.value, "SA"),
        (stateTypesEnum.WA.value, "WA"),
        (stateTypesEnum.TAS.value, "TAS"),
        (stateTypesEnum.NT.value, "NT"),
    )


    salutationTypes=(
        (salutationEnum.MR.value,"Mr."),
        (salutationEnum.MS.value, "Ms."),
        (salutationEnum.MRS.value, "Mrs."),
        (salutationEnum.DR.value, "Dr."),
        (salutationEnum.PROF.value, "Prof."),
    )

    maritalTypes=(
        (maritalEnum.SINGLE.value, "Single"),
        (maritalEnum.MARRIED.value, "Married"),
        (maritalEnum.DIVORCED.value, "Divorced"),
        (maritalEnum.WIDOWED.value, "Widowed"),
        (maritalEnum.DEFACTO.value, "Defacto"),
    )

    caseID = models.AutoField(primary_key=True)
    caseUID = models.UUIDField(default=uuid.uuid4, editable=False)
    refCaseUID = models.UUIDField(null=True, blank=True)
    caseStage = models.IntegerField(choices=caseStages)
    appType = models.IntegerField(default = 0, choices = appTypes)
    caseDescription = models.CharField(max_length=60, null=False, blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    caseNotes = models.TextField(blank=True, null=True)

    phoneNumber=models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    loanType=models.IntegerField(choices=loanTypes,null=True, blank=True)
    clientType1=models.IntegerField(choices=clientTypes,null=True, blank=True)
    salutation_1 = models.IntegerField(choices=salutationTypes,null=True, blank=True)
    middlename_1 = models.CharField(max_length=30, null=True, blank=True)
    maritalStatus_1 = models.IntegerField(choices=maritalTypes,null=True, blank=True)
    surname_1=models.CharField(max_length=30, null=True, blank=True)
    firstname_1=models.CharField(max_length=30, null=True, blank=True)
    preferredName_1=models.CharField(max_length=30, null=True, blank=True)
    birthdate_1=models.DateField(null=True, blank=True)
    age_1=models.IntegerField(null=True, blank=True)
    sex_1=models.IntegerField(choices=clientSex,null=True, blank=True)
    clientType2 = models.IntegerField(choices=clientTypes, null=True, blank=True)
    salutation_2 = models.IntegerField(choices=salutationTypes,null=True, blank=True)
    middlename_2 = models.CharField(max_length=30, null=True, blank=True)
    maritalStatus_2 = models.IntegerField(choices=maritalTypes,null=True, blank=True)
    surname_2=models.CharField(max_length=30, null=True, blank=True)
    firstname_2=models.CharField(max_length=30, null=True, blank=True)
    preferredName_2=models.CharField(max_length=30, null=True, blank=True)
    birthdate_2=models.DateField(null=True, blank=True)
    age_2=models.IntegerField(null=True, blank=True)
    sex_2=models.IntegerField(choices=clientSex,null=True, blank=True)
    street=models.CharField(max_length=60, null=True, blank=True)
    suburb=models.CharField(max_length=30, null=True, blank=True)
    postcode=models.IntegerField(null=True, blank=True)
    state=models.IntegerField(choices=stateTypes,null=True, blank=True)
    valuation=models.IntegerField(null=True, blank=True)
    dwellingType=models.IntegerField(choices=dwellingTypes,null=True, blank=True)
    propertyImage=models.ImageField(null=True, blank=True,upload_to='customerImages')
    mortgageDebt=models.IntegerField(null=True, blank=True)
    superFund=models.ForeignKey(FundDetail,null=True, blank=True, on_delete=models.SET_NULL)
    superAmount=models.IntegerField(null=True, blank=True)
    pensionType=models.IntegerField(choices=pensionTypes,default=2)
    pensionAmount=models.IntegerField(default=0)

    meetingDate = models.DateTimeField(blank=True, null=True)
    summaryDocument = models.FileField(max_length=150,null=True, blank=True)
    summarySentDate = models.DateTimeField(blank=True, null=True)
    summarySentRef = models.CharField(max_length=30, null=True, blank=True)
    responsibleDocument= models.FileField(max_length=150,null=True, blank=True)
    enquiryDocument = models.FileField(max_length=150,null=True, blank=True)
    valuationDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments')
    titleDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments')
    titleRequest = models.BooleanField(null=True, blank=True)
    lixiFile= models.FileField(max_length=150, null=True, blank=True)

    salesChannel = models.IntegerField(choices=channelTypes,null=True, blank=True)
    adviser = models.CharField(max_length=60, null=True, blank=True)
    referralCompany = models.ForeignKey(Referer ,null=True, blank=True, on_delete=models.SET_NULL)
    referralRepNo = models.CharField(max_length=60, null=True, blank=True)


    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    sfOpportunityID = models.CharField(max_length=20, null=True, blank=True)
    sfLoanID=models.CharField(max_length=20, null=True, blank=True)

    amalIdentifier=models.CharField(max_length=40, null=True, blank=True)
    amalLoanID=models.CharField(max_length=40, null=True, blank=True)

    isZoomMeeting=models.BooleanField(default=False, null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects=CaseManager()

    def __str__(self):
        return smart_text(self.caseDescription)

    def __unicode__(self):
        return smart_text(self.caseDescription)

    class Meta:
        ordering = ('-updated',)
        verbose_name_plural = "Case"

    def enumCaseStage(self):
        return dict(self.caseStages)[self.caseStage]

    def enumLoanType(self):
        if self.loanType is not None:
            return dict(self.loanTypes)[self.loanType]

    def enumStateType(self):
        if self.state is not None:
            return dict(self.stateTypes)[self.state]

    def enumDwellingType(self):
        return dict(self.dwellingTypes)[self.dwellingType]

    def enumSex(self):
        if self.loanType==loanTypesEnum.SINGLE_BORROWER.value:
            return [dict(self.clientSex)[self.sex_1],None]
        else:
            return [dict(self.clientSex)[self.sex_1],dict(self.clientSex)[self.sex_2]]

    def enumClientType(self):
        if self.loanType==loanTypesEnum.SINGLE_BORROWER.value:
            return [dict(self.clientTypes)[self.clientType1],None]
        else:
            return [dict(self.clientTypes)[self.clientType1],dict(self.clientTypes)[self.clientType2]]

    def enumChannelType(self):
        if self.salesChannel is not None:
            return dict(self.channelTypes)[self.salesChannel]

    def enumPensionType(self):
        if self.pensionType is not None:
            return dict(self.pensionTypes)[self.pensionType]

    def enumMaritalStatus(self):
        if self.loanType==loanTypesEnum.SINGLE_BORROWER.value:
            return [dict(self.maritalTypes)[self.maritalStatus_1],None]
        else:
            return [dict(self.maritalTypes)[self.maritalStatus_1],dict(self.maritalTypes)[self.maritalStatus_2]]

    def enumSalutation(self):
        if self.loanType==loanTypesEnum.SINGLE_BORROWER.value:
            return [dict(self.salutationTypes)[self.salutation_1],None]
        else:
            return [dict(self.salutationTypes)[self.salutation_1],dict(self.salutationTypes)[self.salutation_2]]

    def get_absolute_url(self):
        return reverse_lazy("case:caseDetail", kwargs={"uid": self.caseUID})

    def get_referrer_url(self):
        return reverse_lazy("referrer:caseDetail", kwargs={"uid": self.caseUID})


# Pre-save function to extend Case
def create_case_extensions(sender, instance, created, **kwargs):
    if created:
       loan, created = Loan.objects.get_or_create(case=instance)
       modelSettings, created = ModelSetting.objects.get_or_create(case=instance)
       lossData, created = LossData.objects.get_or_create(case=instance)
       factFind, created = FactFind.objects.get_or_create(case=instance)

post_save.connect(create_case_extensions, sender=Case)


class Loan(models.Model):

    protectedChoices = (
        (0, "0%"),
        (5, "5%"),
        (10, "10%"),
        (15, "15%"),
        (20, "20%"))

    drawdownFrequency=(
        (incomeFrequencyEnum.FORTNIGHTLY.value, 'Fortnightly'),
        (incomeFrequencyEnum.MONTHLY.value, 'Monthly'))

    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    localLoanID = models.AutoField(primary_key=True)
    maxLVR=models.FloatField(null=False, blank=False,default=0)
    actualLVR = models.FloatField(null=True, blank=True, default=0)
    protectedEquity=models.IntegerField(default=0, choices=protectedChoices)
    # Contract Amounts
    purposeAmount =models.IntegerField(default=0)
    establishmentFee=models.IntegerField(default=0)
    totalLoanAmount=models.IntegerField(default=0)
    # Plan Amounts
    planPurposeAmount =models.IntegerField(default=0)
    planEstablishmentFee=models.IntegerField(default=0)
    totalPlanAmount=models.IntegerField(default=0)

    interestPayAmount=models.IntegerField(default=0)
    interestPayPeriod=models.IntegerField(default=0)
    annualPensionIncome=models.IntegerField(default=0)
    choiceRetireAtHome = models.BooleanField(default=False)
    choiceAvoidDownsizing = models.BooleanField(default=False)
    choiceAccessFunds = models.BooleanField(default=False)
    choiceTopUp = models.BooleanField(default=False)
    choiceRefinance = models.BooleanField(default=False)
    choiceGive = models.BooleanField(default=False)
    choiceReserve = models.BooleanField(default=False)
    choiceLive = models.BooleanField(default=False)
    choiceCare = models.BooleanField(default=False)
    choiceFuture = models.BooleanField(default=False)
    choiceCenterlink= models.BooleanField(default=False)
    choiceVariable = models.BooleanField(default=False)
    consentPrivacy= models.BooleanField(default=False)
    consentElectronic = models.BooleanField(default=False)
    detailedTitle = models.BooleanField(default=False)

    #Variations
    accruedInterest = models.IntegerField(null=True, blank=True)

    objects=CaseManager()

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    class Meta:
        verbose_name_plural = "Case Loan Details"

    def get_purposes(self):
        dict={}
        qs = LoanPurposes.objects.filter(loan = self)
        for purpose in qs:
            if purpose.enumCategory in dict:
                dict[purpose.enumCategory][purpose.enumIntention] = purpose
            else:
                dict[purpose.enumCategory]={purpose.enumIntention:purpose}
        return dict

    def purpose(self, category, intention):
        qs = LoanPurposes.objects.filter(loan=self)
        for purpose in qs:
            if purpose.enumCategory == category and purpose.enumIntention == intention:
                return purpose



class LoanPurposes(models.Model):

    drawdownFrequencyTypes=(
        (incomeFrequencyEnum.FORTNIGHTLY.value, 'Fortnightly'),
        (incomeFrequencyEnum.MONTHLY.value, 'Monthly'))

    categoryTypes = {
        (purposeCategoryEnum.TOP_UP.value, "TOP_UP"),
        (purposeCategoryEnum.REFINANCE.value, "REFINANCE"),
        (purposeCategoryEnum.LIVE.value, "LIVE"),
        (purposeCategoryEnum.GIVE.value, "GIVE"),
        (purposeCategoryEnum.CARE.value, "CARE")
    }

    intentionTypes = {
        (purposeIntentionEnum.INVESTMENT.value, "INVESTMENT"),
        (purposeIntentionEnum.CONTINGENCY.value, "CONTINGENCY"),
        (purposeIntentionEnum.REGULAR_DRAWDOWN.value, "REGULAR_DRAWDOWN"),
        (purposeIntentionEnum.GIVE_TO_FAMILY.value, "GIVE_TO_FAMILY"),
        (purposeIntentionEnum.RENOVATIONS.value, "RENOVATIONS"),
        (purposeIntentionEnum.TRANSPORT.value, "TRANSPORT"),
        (purposeIntentionEnum.LUMP_SUM.value, "LUMP_SUM"),
        (purposeIntentionEnum.MORTGAGE.value, "MORTGAGE")
    }

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    purposeID = models.AutoField(primary_key=True)
    purposeUID = models.UUIDField(default=uuid.uuid4, editable=False)
    active = models.BooleanField(default=True)
    category = models.IntegerField(choices=categoryTypes)
    intention = models.IntegerField(choices=intentionTypes)
    amount = models.IntegerField(default=0,blank=True, null=True)

    drawdownAmount = models.IntegerField(default=0,blank=True, null=True)
    drawdownFrequency = models.IntegerField(choices=drawdownFrequencyTypes, blank=True, null=True)
    drawdownStartDate = models.DateTimeField(blank=True, null=True)
    drawdownEndDate = models.DateTimeField(blank=True, null=True)

    planPeriod = models.IntegerField(default = 0, blank=True, null=True) #Years
    contractDrawdowns = models.IntegerField(default = 0, blank=True, null=True)
    planDrawdowns = models.IntegerField(default = 0, blank=True, null=True)
    planAmount = models.IntegerField(default=0,blank=True, null=True)

    topUpBuffer = models.BooleanField(default = False)
    description = models.CharField(max_length=60, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Case Loan Purposes"

    @property
    def enumCategory(self):
        return dict(self.categoryTypes)[self.category]

    @property
    def enumIntention(self):
        return dict(self.intentionTypes)[self.intention]

    @property
    def enumDrawdownFrequency(self):
        if self.drawdownFrequency:
            return dict(self.drawdownFrequencyTypes)[self.drawdownFrequency]

    def get_absolute_url(self):
        if self.intention == purposeIntentionEnum.REGULAR_DRAWDOWN.value:
            return reverse_lazy("case:caseVariationDrawdown", kwargs={"purposeUID": self.purposeUID})
        else:
            return reverse_lazy("case:caseVariationLumpSum", kwargs={"purposeUID": self.purposeUID})

    @property
    def enumCategoryPretty(self):
        return dict(self.categoryTypes)[self.category].replace("_"," ").lower().title()

    @property
    def enumIntentionPretty(self):
        return dict(self.intentionTypes)[self.intention].replace("_"," ").lower().title()


class ModelSetting(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    inflationRate=models.FloatField(null=True, blank=True)
    housePriceInflation=models.FloatField(null=True, blank=True)
    interestRate=models.FloatField(null=True, blank=True)
    lendingMargin=models.FloatField(null=True, blank=True)
    comparisonRateIncrement=models.FloatField(null=True, blank=True)
    establishmentFeeRate=models.FloatField(null=True, blank=True)

    objects=CaseManager()

    class Meta:
        verbose_name_plural = "Case Settings"

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)


class LossData(models.Model):

    closeReasonTypes=(
        (closeReasonEnum.AGE_RESTRICTION.value, 'Age Restriction'),
        (closeReasonEnum.POSTCODE_RESTRICTION.value, 'Postcode Restriction'),
        (closeReasonEnum.MINIMUM_LOAN_AMOUNT.value, 'Below minimum loan amount'),
        (closeReasonEnum.CREDIT.value, 'Credit History'),
        (closeReasonEnum.MORTGAGE.value, 'Mortgage too Large'),
        (closeReasonEnum.SHORT_TERM.value, 'Short-term / Bridging Requirement'),
        (closeReasonEnum.TENANTS.value, 'Tenants in common'),
        (closeReasonEnum.UNSUITABLE_PROPERTY.value, 'Unsuitable Property'),
        (closeReasonEnum.UNSUITABLE_PURPOSE.value, 'Unsuitable Purpose'),
        (closeReasonEnum.ALTERNATIVE_SOLUTION.value, 'Client Pursuing Alternative'),
        (closeReasonEnum.COMPETITOR.value, 'Client went to Competitor'),
        (closeReasonEnum.NO_CLIENT_ACTION.value, 'No further action by client'),
        (closeReasonEnum.OTHER.value , 'Other')
    )

    case = models.OneToOneField(Case, on_delete=models.CASCADE)

    lossNotes=models.TextField(blank=True, null=True) # remove this

    closeDate = models.DateField(blank=True, null=True)
    closeReason = models.IntegerField(blank=True, null=True, choices=closeReasonTypes)

    followUpDate=models.DateField(blank=True, null=True)
    followUpNotes = models.TextField(blank=True, null=True)
    doNotMarket = models.BooleanField(default=False)

    objects = CaseManager()

    class Meta:
        verbose_name_plural = "Case Loss Data"

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    def enumCloseReason(self):
        try:
            return dict(self.closeReasonTypes)[self.closeReason]
        except:
            return None

    class Meta:
        verbose_name_plural = "Case Loss Data"


class FactFind(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    backgroundNotes = models.TextField(blank=True, null=True)
    requirementsNotes = models.TextField(blank=True, null=True)
    topUpNotes = models.TextField(blank=True, null=True)
    refiNotes = models.TextField(blank=True, null=True)
    liveNotes = models.TextField(blank=True, null=True)
    giveNotes = models.TextField(blank=True, null=True)
    careNotes = models.TextField(blank=True, null=True)
    futureNotes = models.TextField(blank=True, null=True)
    clientNotes = models.TextField(blank=True, null=True)
    additionalNotes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = CaseManager()

    class Meta:
        verbose_name_plural = "Case Fact Find"

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)
