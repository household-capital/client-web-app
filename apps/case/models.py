#Python imports
import uuid

#Django Imports
from django.conf import settings
from django.db.models.signals import post_save
from django.db import models
from django.utils.encoding import smart_text
from django.urls import reverse_lazy

#Local Application Imports
from apps.lib.enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,\
    pensionTypesEnum, loanTypesEnum, ragTypesEnum, channelTypesEnum, stateTypesEnum


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


class Case(models.Model):
    # Main model - extended by Loan, ModelSettings and LossData

    caseTypes=(
                  (caseTypesEnum.LEAD.value,"Lead"),
                  (caseTypesEnum.OPPORTUNITY.value, "Opportunity"),
                  (caseTypesEnum.MEETING_HELD.value, "Meeting Held"),
                  (caseTypesEnum.APPLICATION.value, "Application"),
                  (caseTypesEnum.PRE_APPROVAL.value, "Pre-approval"),
                  (caseTypesEnum.CLOSED.value, "Closed"),
                  (caseTypesEnum.APPROVED.value,"Approved")
    )

    clientTypes=(
        (clientTypesEnum.BORROWER.value, 'Borrower'),
        (clientTypesEnum.NOMINATED_OCCUPANT.value, 'Nominated Occupant'),
        (clientTypesEnum.POWER_OF_ATTORNEY.value, 'Power of Attorney'),)

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


    caseID = models.AutoField(primary_key=True)
    caseUID = models.UUIDField(default=uuid.uuid4, editable=False)
    caseType = models.IntegerField(choices=caseTypes)
    caseDescription = models.CharField(max_length=60, null=False, blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    adviser = models.CharField(max_length=60, null=False, blank=False)
    caseNotes = models.TextField(blank=True, null=True)

    phoneNumber=models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    loanType=models.IntegerField(choices=loanTypes,null=True, blank=True)
    clientType1=models.IntegerField(choices=clientTypes,null=True, blank=True)
    surname_1=models.CharField(max_length=30, null=True, blank=True)
    firstname_1=models.CharField(max_length=30, null=True, blank=True)
    birthdate_1=models.DateField(null=True, blank=True)
    age_1=models.IntegerField(null=True, blank=True)
    sex_1=models.IntegerField(choices=clientSex,null=True, blank=True)
    clientType2 = models.IntegerField(choices=clientTypes, null=True, blank=True)
    surname_2=models.CharField(max_length=30, null=True, blank=True)
    firstname_2=models.CharField(max_length=30, null=True, blank=True)
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
    pensionAmount=models.IntegerField(null=True, blank=True)

    meetingDate = models.DateTimeField(blank=True, null=True)
    summaryDocument = models.FileField(max_length=150,null=True, blank=True)
    responsibleDocument= models.FileField(max_length=150,null=True, blank=True)
    privacyDocument= models.FileField(max_length=150,null=True, blank=True)
    electronicDocument= models.FileField(max_length=150,null=True, blank=True)
    dataDocument= models.FileField(max_length=150,null=True, blank=True)
    enquiryDocument = models.FileField(max_length=150,null=True, blank=True)
    valuationDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments')
    solicitorInstruction = models.FileField(max_length=150,null=True, blank=True)
    valuerInstruction= models.FileField(max_length=150, null=True, blank=True)
    titleDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments')
    specialConditions=models.TextField(null=True, blank=True)
    dataCSV = models.FileField(max_length=150, null=True, blank=True, upload_to='customerDocuments')

    valuerFirm=models.CharField(max_length=20, null=True, blank=True)
    valuerEmail=models.EmailField(null=True, blank=True)
    valuerContact=models.TextField(null=True, blank=True)

    salesChannel = models.IntegerField(choices=channelTypes,null=True, blank=True)

    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    sfOpportunityID = models.CharField(max_length=20, null=True, blank=True)
    sfLoanID=models.CharField(max_length=20, null=True, blank=True)

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
        try:
            return dict(self.loanTypes)[self.loanType]
        except:
            return ""

    def enumStateType(self):
        try:
            return dict(self.stateTypes)[self.state]
        except:
            return ""

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

    def get_absolute_url(self):
        return reverse_lazy("case:caseDetail", kwargs={"pk":self.caseID})




# Pre-save function to extend Case
def create_case_extensions(sender, instance, created, **kwargs):
    if created:
       loan, created = Loan.objects.get_or_create(case=instance)
       modelSettings, created = ModelSetting.objects.get_or_create(case=instance)
       lossData, created = LossData.objects.get_or_create(case=instance)

post_save.connect(create_case_extensions, sender=Case)



class Loan(models.Model):

    protectedChoices = (
        (0, "0%"),
        (5, "5%"),
        (10, "10%"),
        (15, "15%"),
        (20, "20%"))

    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    localLoanID = models.AutoField(primary_key=True)
    maxLVR=models.FloatField(null=False, blank=False,default=0)
    actualLVR = models.FloatField(null=True, blank=True, default=0)
    establishmentFee=models.IntegerField(default=0)
    protectedEquity=models.IntegerField(default=0, choices=protectedChoices)
    totalLoanAmount=models.IntegerField(default=0)
    topUpAmount=models.IntegerField(default=0)
    topUpIncome=models.IntegerField(default=0)
    refinanceAmount=models.IntegerField(default=0)
    giveAmount=models.IntegerField(default=0)
    renovateAmount=models.IntegerField(default=0)
    travelAmount=models.IntegerField(default=0)
    careAmount=models.IntegerField(default=0)
    giveDescription=models.CharField(max_length=30, null=True, blank=True)
    renovateDescription=models.CharField(max_length=30, null=True, blank=True)
    travelDescription=models.CharField(max_length=30, null=True, blank=True)
    careDescription=models.CharField(max_length=30, null=True, blank=True)
    incomeObjective=models.IntegerField(default=0)
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

    objects=CaseManager()

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)


class ModelSetting(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    inflationRate=models.FloatField(null=True, blank=True)
    investmentRate=models.FloatField(null=True, blank=True)
    housePriceInflation=models.FloatField(null=True, blank=True)
    interestRate=models.FloatField(null=True, blank=True)
    lendingMargin=models.FloatField(null=True, blank=True)
    comparisonRateIncrement=models.FloatField(null=True, blank=True)
    projectionAge=models.IntegerField(null=True, blank=True)

    objects=CaseManager()


    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)


class LossData(models.Model):

    ragTypes = (
        (ragTypesEnum.RED.value, 'RED'),
        (ragTypesEnum.AMBER.value, 'AMBER'),
        (ragTypesEnum.GREEN.value, 'GREEN'),)

    trueFalse = (
        (False, 'No'),
        (True,'Yes')
    )

    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    lossNotes=models.TextField(blank=True, null=True)
    lossDate = models.DateField(blank=True, null=True)
    ragStatus = models.IntegerField(blank=True, null=True, choices=ragTypes)
    followUp=models.BooleanField(default=False, blank=True,null=True, choices=trueFalse)
    followUpDate=models.DateField(blank=True, null=True)
    followUpNotes = models.TextField(blank=True, null=True)
    purposeTopUp = models.BooleanField(default=False)
    purposeRefi=models.BooleanField(default=False)
    purposeLive=models.BooleanField(default=False)
    purposeGive=models.BooleanField(default=False)
    purposeCare=models.BooleanField(default=False)

    objects = CaseManager()

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    def enumRagStatus(self):
        return self.ragTypes[self.ragStatus][1]

