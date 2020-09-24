# Python Imports
import uuid
from datetime import datetime, timedelta

# Django Imports
from django.db import models
from django.urls import reverse_lazy
from django.utils.encoding import smart_text

# Local Imports
from apps.lib.site_Enums import appStatusEnum, salutationEnum, maritalEnum, clientSexEnum, dwellingTypesEnum, \
    productTypesEnum, incomeFrequencyEnum, purposeCategoryEnum, purposeIntentionEnum, loanTypesEnum, \
    clientTypesEnum, documentTypesEnum, stateTypesEnum


class ApplicationManager(models.Manager):
    """Model manager for Application and related (Foreign Key) objects"""
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
    """
    Model for Online Applications
        * similar to Case object fields (combining Case Loan fields)
        * related purpose objects (similar to Case)
    """

    appStatusTypes=(
        (appStatusEnum.CREATED.value, "Created"),
        (appStatusEnum.IN_PROGRESS.value, "In-Progress"),
        (appStatusEnum.EXPIRED.value, "Expired"),
        (appStatusEnum.SUBMITTED.value, "Submitted"),
        (appStatusEnum.CONTACT.value, "Contact"),
        (appStatusEnum.CLOSED.value, "Closed"),
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

    productTypes = (
        (productTypesEnum.INCOME.value, "Income"),
        (productTypesEnum.CONTINGENCY_20K.value, "Contingency 20K"),
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
    loanType = models.IntegerField(default=1, choices=loanTypes)
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
    state = models.IntegerField(choices=stateTypes, null=True, blank=True)
    postcode = models.IntegerField(blank=True, null=True)

    #Calculated Fields
    status = models.BooleanField(default=True, blank=False, null=False)
    maxLoanAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownMonthly = models.IntegerField(blank=True, null=True)
    maxLVR = models.FloatField(blank=True, null=True)
    actualLVR = models.FloatField(blank=True, null=True)
    isLowLVR = models.BooleanField(default=False)

    #Application Amount Fields
    purposeAmount = models.IntegerField(default=0)
    establishmentFee=models.IntegerField(default=0)
    totalLoanAmount=models.IntegerField(default=0)
    planPurposeAmount =models.IntegerField(default=0)
    planEstablishmentFee=models.IntegerField(default=0)
    totalPlanAmount=models.IntegerField(default=0)
    summaryDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerReports' )
    applicationDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerReports')

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

    #Choice Fields
    choiceProduct = models.BooleanField(default=True)
    choiceOtherNeeds = models.BooleanField(blank=True, null=True)
    choiceMortgage = models.BooleanField(blank=True, null=True)
    choiceOwnership = models.BooleanField(blank=True, null=True)
    choiceOccupants = models.BooleanField(blank=True, null=True)

    #Workflow
    pin = models.IntegerField(blank=True, null=True)
    pinExpiry = models.DateTimeField(blank=True, null=True)
    appStatus = models.IntegerField(choices=appStatusTypes, default=0 )
    summarySent = models.BooleanField(default=False)
    summarySentDate = models.DateTimeField(blank=True, null=True)
    summarySentRef = models.CharField(max_length=30, null=True, blank=True)
    loanSummaryAmount = models.IntegerField(default=0)
    signingName_1 = models.CharField(max_length=50, null=True, blank=True)
    signingName_2 = models.CharField(max_length=50, null=True, blank=True)
    signingDate = models.DateTimeField(blank=True, null=True)
    ip_address =  models.CharField(max_length=60, null=True, blank=True)
    user_agent = models.CharField(max_length=200, null=True, blank=True)
    followUpEmail = models.DateTimeField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = ApplicationManager()

    class Meta:
        verbose_name_plural = "Application"


    def __str__(self):
        return smart_text(self.email)

    def __unicode__(self):
        return smart_text(self.email)

    def get_purposes(self):
        """Returns a dictionary of related Application Purposes"""
        dict={}
        qs = ApplicationPurposes.objects.filter(application = self)
        for purpose in qs:
            if purpose.enumCategory in dict:
                dict[purpose.enumCategory][purpose.enumIntention] = purpose
            else:
                dict[purpose.enumCategory]={purpose.enumIntention:purpose}
        return dict

    def purpose(self, category, intention):
        """Returns a related Application Purpose object"""
        qs = ApplicationPurposes.objects.filter(application=self)
        for purpose in qs:
            if purpose.enumCategory == category and purpose.enumIntention == intention:
                return purpose

    def enumFreq(self, field):
        frequencyTypes = (
            (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
            (incomeFrequencyEnum.FORTNIGHTLY.value, "Fortnightly"),
            (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
            (incomeFrequencyEnum.QUARTERLY.value, "Quarterly"),
            (incomeFrequencyEnum.ANNUALLY.value, "Annually"))

        return dict(frequencyTypes)[getattr(self,field)].lower()

    @property
    def get_absolute_url(self):
        return reverse_lazy("application:appDetail", kwargs={"uid":self.appUID})

    @property
    def enumClientType(self):
        if self.clientType2 != None:
            return dict(self.clientTypes)[self.clientType2]

    @property
    def enumSalutation(self):
        if self.clientType2 == None:
            return [dict(self.salutationTypes)[self.salutation_1],None]
        else:
            return [dict(self.salutationTypes)[self.salutation_1],dict(self.salutationTypes)[self.salutation_2]]

    @property
    def enumDwellingType(self):
        return dict(self.dwellingTypes)[self.dwellingType]

    @property
    def enumStateType(self):
        if self.state is not None:
            return dict(self.stateTypes)[self.state]

    @property
    def enumAppStatus(self):
        if self.appStatus is not None:
            return dict(self.appStatusTypes)[self.appStatus]

    @property
    def enumProductType(self):
        if self.productType is not None:
            return dict(self.productTypes)[self.productType]


class ApplicationPurposes(models.Model):
    """Application Purposes - similar to Case Purposes"""

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
        (purposeIntentionEnum.TRANSPORT_AND_TRAVEL.value, "TRANSPORT_AND_TRAVEL"),
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


class ApplicationDocuments(models.Model):
    """Application documents loaded byy customers"""


    documentTypes= (
        (documentTypesEnum.RATES.value,'Rates Notice'),
        (documentTypesEnum.INSURANCE.value,'Insurance Certificate'),
        (documentTypesEnum.STRATA_LEVIES.value, 'Strata Levies'),
        (documentTypesEnum.OTHER.value,'Other')
    )

    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    docUID = models.UUIDField(default=uuid.uuid4, editable=False)
    documentType = models.IntegerField(choices=documentTypes, blank=False, null=False)
    document = models.FileField(max_length=150,null=False, blank=False, upload_to='customerDocuments')
    mimeType = models.CharField(max_length=100, null=True, blank=True)
    ip_address =  models.CharField(max_length=60, null=True, blank=True)
    user_agent = models.CharField(max_length=200, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = ApplicationManager()

    class Meta:
        verbose_name_plural = "Application Documents"

    @property
    def enumDocumentType(self):
        return dict(self.documentTypes)[self.documentType]

