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
from apps.lib.site_Enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,\
    pensionTypesEnum, loanTypesEnum, ragTypesEnum, channelTypesEnum, stateTypesEnum, incomeFrequencyEnum, \
    closeReasonEnum, salutationEnum, maritalEnum


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
        closedTypes = [caseTypesEnum.CLOSED.value, caseTypesEnum.FUNDED.value]
        return Case.objects.exclude(caseType__in=closedTypes)


class Case(models.Model):
    # Main model - extended by Loan, ModelSettings and LossData

    caseTypes=(
                  (caseTypesEnum.DISCOVERY.value,"Discovery"),
                  (caseTypesEnum.MEETING_HELD.value, "Meeting Held"),
                  (caseTypesEnum.APPLICATION.value, "Application"),
                  (caseTypesEnum.DOCUMENTATION.value, "Documentation"),
                  (caseTypesEnum.FUNDED.value, "Funded"),
                  (caseTypesEnum.CLOSED.value, "Closed"),    )

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

    valuers=(
        ('WBP Group','WBP Group'),
        ('Opteon Solutions','Opteon Solutions')
    )

    valuerEmails=(
        ('valuations@wbpgroup.com.au','valuations@wbpgroup.com.au'),
        ('instructions@opteonsolutions.com','instructions@opteonsolutions.com'),
        ('quotes@opteonsolutions.com', 'quotes@opteonsolutions.com')
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
    caseType = models.IntegerField(choices=caseTypes)
    caseDescription = models.CharField(max_length=60, null=False, blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    adviser = models.CharField(max_length=60, null=True, blank=True)
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
    privacyDocument= models.FileField(max_length=150,null=True, blank=True)
    electronicDocument= models.FileField(max_length=150,null=True, blank=True)
    dataDocument= models.FileField(max_length=150,null=True, blank=True)
    enquiryDocument = models.FileField(max_length=150,null=True, blank=True)
    valuationDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments')
    solicitorInstruction = models.FileField(max_length=150,null=True, blank=True)
    valuerInstruction= models.FileField(max_length=150, null=True, blank=True)
    titleDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments')
    titleRequest = models.BooleanField(null=True, blank=True)
    specialConditions=models.TextField(null=True, blank=True)
    dataCSV = models.FileField(max_length=150, null=True, blank=True, upload_to='customerDocuments')
    lixiFile= models.FileField(max_length=150, null=True, blank=True)

    valuerFirm=models.CharField(max_length=20, null=True, blank=True, choices=valuers)
    valuerEmail=models.EmailField(null=True, blank=True, choices=valuerEmails)
    valuerContact=models.TextField(null=True, blank=True)

    salesChannel = models.IntegerField(choices=channelTypes,null=True, blank=True)

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

    def enumCaseType(self):
        return dict(self.caseTypes)[self.caseType]

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
        if self.clientType2 is None:
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
        if self.clientType2 is None:
            return [dict(self.maritalTypes)[self.maritalStatus_1],None]
        else:
            return [dict(self.maritalTypes)[self.maritalStatus_1],dict(self.maritalTypes)[self.maritalStatus_2]]

    def enumSalutation(self):
        if self.clientType2 is None:
            return [dict(self.salutationTypes)[self.salutation_1],None]
        else:
            return [dict(self.salutationTypes)[self.salutation_1],dict(self.salutationTypes)[self.salutation_2]]

    def get_absolute_url(self):
        return reverse_lazy("case:caseDetail", kwargs={"uid": self.caseUID})


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
        (incomeFrequencyEnum.FORTNIGHTLY.value, 'fortnightly'),
        (incomeFrequencyEnum.MONTHLY.value, 'monthly'))

    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    localLoanID = models.AutoField(primary_key=True)
    maxLVR=models.FloatField(null=False, blank=False,default=0)
    actualLVR = models.FloatField(null=True, blank=True, default=0)
    establishmentFee=models.IntegerField(default=0)
    planEstablishmentFee=models.IntegerField(default=0)
    protectedEquity=models.IntegerField(default=0, choices=protectedChoices)
    totalLoanAmount=models.IntegerField(default=0)
    totalPlanAmount=models.IntegerField(default=0)
    topUpAmount=models.IntegerField(default=0)
    topUpDrawdownAmount=models.IntegerField(default=0)
    topUpPlanAmount=models.IntegerField(default=0)
    topUpIncomeAmount = models.IntegerField(default=0)
    topUpFrequency = models.IntegerField(default=2, choices=drawdownFrequency)
    topUpPeriod = models.IntegerField(default=5)
    topUpBuffer = models.IntegerField(default=0)
    topUpContingencyAmount = models.IntegerField(default=0)
    topUpDescription = models.CharField(max_length=60, null=True, blank=True)
    topUpContingencyDescription = models.CharField(max_length=60, null=True, blank=True)
    refinanceAmount=models.IntegerField(default=0)
    renovateAmount=models.IntegerField(default=0)
    travelAmount=models.IntegerField(default=0)
    renovateDescription=models.CharField(max_length=60, null=True, blank=True)
    travelDescription=models.CharField(max_length=60, null=True, blank=True)
    giveAmount=models.IntegerField(default=0)
    giveDescription = models.CharField(max_length=60, null=True, blank=True)
    careAmount=models.IntegerField(default=0)
    careDrawdownAmount=models.IntegerField(default=0)
    carePlanAmount=models.IntegerField(default=0)
    careRegularAmount=models.IntegerField(default=0)
    careFrequency=models.IntegerField(default=2, choices=drawdownFrequency)
    carePeriod=models.IntegerField(default=3)
    careDrawdownDescription = models.CharField(max_length=60, null=True, blank=True)
    careDescription=models.CharField(max_length=60, null=True, blank=True)
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

    #Version 1 Fields
    topUpIncome=models.IntegerField(default=0)
    incomeObjective=models.IntegerField(default=0)


    objects=CaseManager()

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    def enumDrawdownFrequency(self):
        if self.topUpFrequency:
            return dict(self.drawdownFrequency)[self.topUpFrequency]

    def enumCareFrequency(self):
        if self.careFrequency:
            return dict(self.drawdownFrequency)[self.careFrequency]

class ModelSetting(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    inflationRate=models.FloatField(null=True, blank=True)
    housePriceInflation=models.FloatField(null=True, blank=True)
    interestRate=models.FloatField(null=True, blank=True)
    lendingMargin=models.FloatField(null=True, blank=True)
    comparisonRateIncrement=models.FloatField(null=True, blank=True)
    establishmentFeeRate=models.FloatField(null=True, blank=True)

    objects=CaseManager()


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
        verbose_name_plural = "Loss Data"

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

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)


#AMAL Tables

class FundedData(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    approved = models.FloatField(default=0,blank=True, null=True)
    advanced = models.FloatField(default=0,blank=True, null=True)
    principal = models.FloatField(default=0,blank=True, null=True)
    totalValuation = models.FloatField(default=1,blank=True, null=True)
    currentLVR = models.FloatField(default=0,blank=True, null=True)
    settlementDate = models.DateTimeField(blank=True, null=True)
    dischargeDate = models.DateTimeField(blank=True, null=True)
    bPayCode = models.CharField(max_length=30, blank=True, null=True)
    bPayRef = models.CharField(max_length=30, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    objects = CaseManager()

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    class Meta:
        verbose_name_plural = "Funded Data"

    def get_absolute_url(self):
        return reverse_lazy("case:loanDetail", kwargs={"uid": self.case.caseUID})

class TransactionData(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    description = models.CharField(max_length=120, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)
    transactionDate = models.DateTimeField(blank=True, null=True)
    effectiveDate = models.DateTimeField(blank=True, null=True)
    tranRef = models.CharField(max_length=30,blank=False, null=False)
    debitAmount =  models.FloatField(default=0,blank=True, null=True)
    creditAmount = models.FloatField(default=0, blank=True, null=True)
    balance = models.FloatField(default=0, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    objects = CaseManager()

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    class Meta:
        verbose_name_plural = "Transaction Data"
        unique_together = (('case', 'tranRef'),)

