# Python Imports
import uuid
from datetime import datetime, timedelta

# Django Imports
from django.db import models
from django.utils.encoding import smart_text

# Local Imports
from apps.lib.site_Enums import appStatusEnum, salutationEnum, maritalEnum, clientSexEnum, dwellingTypesEnum, \
    productTypesEnum, incomeFrequencyEnum, purposeCategoryEnum, purposeIntentionEnum, loanTypesEnum, clientTypesEnum

class ApplicationManager(models.Manager):
    def queryset_byUID(self,uidString):
       if self.model.__name__=='Application':
            searchCase=Application.objects.get(appUID=uuid.UUID(uidString)).appUID
            return super(ApplicationManager,self).filter(appUID=searchCase)
       else:
           searchCase = Application.objects.get(appUID=uuid.UUID(uidString))
           return super(ApplicationManager, self).filter(appUID=searchCase)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]


class Application(models.Model):
    #Model for Income Application

    appStatusTypes=(
        (appStatusEnum.CREATED.value, "Created"),
        (appStatusEnum.IN_PROGRESS.value, "In-Progress"),
        (appStatusEnum.EXPIRED.value, "Expired"),
        (appStatusEnum.SUBMITTED.value, "Submitted"),
        (appStatusEnum.CONTACT.value, "Contact")
    )

    clientSex=(
        (clientSexEnum.FEMALE.value, 'Female'),
        (clientSexEnum.MALE.value, 'Male'))

    drawdownFrequencyTypes=(
        (incomeFrequencyEnum.FORTNIGHTLY.value, 'Fortnightly'),
        (incomeFrequencyEnum.MONTHLY.value, 'Monthly'))

    expenseFrequencyTypes = (
        (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
        (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        (incomeFrequencyEnum.QUARTERLY.value, "Quarterly"),
        (incomeFrequencyEnum.ANNUALLY.value, "Annually")
    )

    incomeFrequencyTypes = (
        (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
        (incomeFrequencyEnum.FORTNIGHTLY.value, "Fortnightly"),
        (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        (incomeFrequencyEnum.ANNUALLY.value, "Annually")
    )

    maritalTypes = (
        (maritalEnum.SINGLE.value, "Single"),
        (maritalEnum.MARRIED.value, "Married"),
        (maritalEnum.DIVORCED.value, "Divorced"),
        (maritalEnum.WIDOWED.value, "Widowed"),
        (maritalEnum.DEFACTO.value, "Defacto"),
    )

    salutationTypes=(
        (salutationEnum.MR.value,"Mr."),
        (salutationEnum.MS.value, "Ms."),
        (salutationEnum.MRS.value, "Mrs."),
        (salutationEnum.DR.value, "Dr."),
        (salutationEnum.PROF.value, "Prof."),
    )

    dwellingTypes = (
        (dwellingTypesEnum.HOUSE.value, 'House'),
        (dwellingTypesEnum.APARTMENT.value, 'Apartment'))


    productTypes = (
        (productTypesEnum.LUMP_SUM.value, "Lump Sum"),
        (productTypesEnum.INCOME.value, "Income")
    )

    loanTypes = (
        (loanTypesEnum.SINGLE_BORROWER.value, "Single"),
        (loanTypesEnum.JOINT_BORROWER.value, "Joint")
    )

    clientTypes=(
        (clientTypesEnum.BORROWER.value, 'Borrower'),
        (clientTypesEnum.NOMINATED_OCCUPANT.value, 'Nominated Occupant'),
        (clientTypesEnum.PERMITTED_COHABITANT.value, 'Permitted Cohabitant')
    )

    appUID = models.UUIDField(default=uuid.uuid4, editable=False)

    #Product
    productType = models.IntegerField(choices = productTypes, default=0)

    #Client Data
    name = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    loanType = models.BooleanField(default=True, choices=loanTypes)
    age_1 = models.IntegerField(blank=True, null=True)
    age_2 = models.IntegerField(blank=True, null=True)
    dwellingType = models.IntegerField(default=True, choices=dwellingTypes)
    valuation = models.IntegerField(blank=True, null=True)

    #Applicant Data
    surname_1 = models.CharField(max_length=30, null=True, blank=True)
    firstname_1 = models.CharField(max_length=30, null=True, blank=True)
    birthdate_1 = models.DateField(null=True, blank=True)
    sex_1 = models.IntegerField(choices=clientSex, null=True, blank=True)
    salutation_1 = models.IntegerField(choices=salutationTypes, null=True, blank=True)
    surname_2 = models.CharField(max_length=30, null=True, blank=True)
    firstname_2 = models.CharField(max_length=30, null=True, blank=True)
    birthdate_2 = models.DateField(null=True, blank=True)
    sex_2 = models.IntegerField(choices=clientSex, null=True, blank=True)
    salutation_2 = models.IntegerField(choices=salutationTypes, null=True, blank=True)
    clientType2 = models.IntegerField(choices=clientTypes, null=True, blank=True)
    consentPrivacy= models.BooleanField(default=False)
    consentElectronic = models.BooleanField(default=False)
    bankBsbNumber = models.CharField(max_length=7, null=True, blank=True)
    bankAccountName = models.CharField(max_length=20, null=True, blank=True)
    bankAccountNumber = models.CharField(max_length=12, null=True, blank=True)

    #Address Data
    streetAddress = models.CharField(max_length=80,blank= True,null=True)
    suburb = models.CharField(max_length=40, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    postcode = models.IntegerField(blank=True, null=True)

    #Calculated Fields
    status = models.BooleanField(default=True, blank=False, null=False)
    maxLoanAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownMonthly = models.IntegerField(blank=True, null=True)
    maxLVR = models.FloatField(blank=True, null=True)
    actualLVR = models.FloatField(blank=True, null=True)

    #Application Amount Fields
    purposeAmount = models.IntegerField(default=0)
    establishmentFee=models.IntegerField(default=0)
    totalLoanAmount=models.IntegerField(default=0)
    planPurposeAmount =models.IntegerField(default=0)
    planEstablishmentFee=models.IntegerField(default=0)
    totalPlanAmount=models.IntegerField(default=0)
    summaryDocument = models.FileField(max_length=150,null=True, blank=True)

    #Application Financial Fields
    assetSaving = models.IntegerField(default=0)
    assetVehicles = models.IntegerField(default=0)
    assetOther = models.IntegerField(default=0)
    liabLoans = models.IntegerField(default=0)
    liabCards = models.IntegerField(default=0)
    liabOther = models.IntegerField(default=0)
    limitCards = models.IntegerField(default=0)
    totalAnnualIncome = models.IntegerField(default=0)
    incomePension = models.IntegerField(default=0)
    incomePensionFreq = models.IntegerField(choices=incomeFrequencyTypes, default=incomeFrequencyEnum.FORTNIGHTLY.value)
    incomeSavings = models.IntegerField(default=0)
    incomeSavingsFreq = models.IntegerField(choices=incomeFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    incomeOther = models.IntegerField(default=0)
    incomeOtherFreq = models.IntegerField(choices=incomeFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    totalAnnualExpenses = models.IntegerField(default=0)
    expenseHomeIns = models.IntegerField(default=0)
    expenseHomeInsFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseRates = models.IntegerField(default=0)
    expenseRatesFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.QUARTERLY.value)
    expenseGroceries = models.IntegerField(default=0)
    expenseGroceriesFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.WEEKLY.value)
    expenseUtilities = models.IntegerField(default=0)
    expenseUtilitiesFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.QUARTERLY.value)
    expenseMedical = models.IntegerField(default=0)
    expenseMedicalFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseTransport = models.IntegerField(default=0)
    expenseTransportFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseRepay = models.IntegerField(default=0)
    expenseRepayFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseOther = models.IntegerField(default=0)
    expenseOtherFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)

    #Income Fields
    choiceIncome = models.BooleanField(default=True)
    choiceOtherNeeds = models.BooleanField(blank=True, null=True)
    choiceMortgage = models.BooleanField(blank=True, null=True)
    choiceOwnership = models.BooleanField(blank=True, null=True)

    #Workflow
    pin = models.IntegerField(blank=True, null=True)
    pinExpiry = models.DateTimeField(blank=True, null=True)
    appStatus = models.IntegerField(choices=appStatusTypes, default=0 )
    loanSummarySent = models.BooleanField(default=False)
    loanSummaryAmount = models.IntegerField(default=0)
    signingName_1 = models.CharField(max_length=50, null=True, blank=True)
    signingName_2 = models.CharField(max_length=50, null=True, blank=True)
    signingDate = models.DateTimeField(blank=True, null=True)
    ip_address =  models.CharField(max_length=60, null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = ApplicationManager()

    def __str__(self):
        return smart_text(self.email)

    def __unicode__(self):
        return smart_text(self.email)

    def get_purposes(self):
        dict={}
        qs = ApplicationPurposes.objects.filter(application = self)
        for purpose in qs:
            if purpose.enumCategory in dict:
                dict[purpose.enumCategory][purpose.enumIntention] = purpose
            else:
                dict[purpose.enumCategory]={purpose.enumIntention:purpose}
        return dict

    def purpose(self, category, intention):
        qs = ApplicationPurposes.objects.filter(application=self)
        for purpose in qs:
            if purpose.enumCategory == category and purpose.enumIntention == intention:
                return purpose


class ApplicationPurposes(models.Model):

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

    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    category = models.IntegerField(choices=categoryTypes, blank=True, null=True)
    intention = models.IntegerField(choices=intentionTypes, blank=True, null=True)
    amount = models.IntegerField(default=0,blank=True, null=True)

    drawdownAmount = models.IntegerField(default=0,blank=True, null=True)
    drawdownFrequency = models.IntegerField(choices=drawdownFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)

    contractDrawdowns = models.IntegerField(default = 0, blank=True, null=True)
    planDrawdowns = models.IntegerField(default = 0, blank=True, null=True)
    planAmount = models.IntegerField(default=0,blank=True, null=True)

    planPeriod = models.IntegerField(default=0, blank=True, null=True)  # used for simple input
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Application Loan Purposes"

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

    @property
    def enumCategoryPretty(self):
        return dict(self.categoryTypes)[self.category].replace("_"," ").lower().title()

    @property
    def enumIntentionPretty(self):
        return dict(self.intentionTypes)[self.intention].replace("_"," ").lower().title().replace(" To ", " to ")
