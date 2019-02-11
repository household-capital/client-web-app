import uuid

from django import forms
from django.conf import settings
from django.db.models.signals import post_save
from django.db import models
from django.utils.encoding import smart_text
from django.urls import reverse_lazy


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

    caseTypes = (
        (0, 'Lead'),
        (1, 'Opportunity'),
        (2, 'Application'),
        (3, 'Settlement'),
        (4, 'Funded'),
        (5, 'Closed'))

    clientTypes=(
    (0, 'Borrower'),
    (1, 'Nominated Occupant'),
    (2, 'Power of Attorney'))

    clientSex=(
    (0, 'Female'),
    (1, 'Male'))

    dwellingTypes=(
    (0, 'House'),
    (1, 'Apartment'))

    pensionTypes=(
        (0, 'Full'),
        (1, 'Partial'),
        (2, 'None')
    )

    loanTypes=(
        (0,'Single'),
        (1,'Joint')
    )

    caseID = models.AutoField(primary_key=True)
    caseUID = models.UUIDField(default=uuid.uuid4, editable=False)
    caseType = models.IntegerField(choices=caseTypes)
    caseDescription = models.CharField(max_length=60, null=False, blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    adviser = models.CharField(max_length=60, null=False, blank=False)
    caseNotes = models.TextField(blank=True, null=True)

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
    postcode=models.IntegerField(null=True, blank=True)
    valuation=models.IntegerField(null=True, blank=True)
    dwellingType=models.IntegerField(choices=dwellingTypes,null=True, blank=True)
    mortgageDebt=models.IntegerField(null=True, blank=True)
    superName=models.CharField(max_length=30, null=True, blank=True)
    superAmount=models.IntegerField(null=True, blank=True)
    pensionType=models.IntegerField(choices=pensionTypes,default=2)
    pensionAmount=models.IntegerField(null=True, blank=True)

    meetingDate = models.DateTimeField(blank=True, null=True)
    summaryDocument = models.FileField(null=True, blank=True)

    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    sfOpportunityID = models.CharField(max_length=20, null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects=CaseManager()

    def __str__(self):
        return smart_text(self.caseDescription)

    def __unicode__(self):
        return smart_text(self.caseDescription)


    class Meta:
        ordering = ('-updated',)

    def get_absolute_url(self):
        return reverse_lazy("case:caseDetail", kwargs={"pk":self.caseID})


# Pre-save function to extend Casae
def create_case_extensions(sender, instance, created, **kwargs):
    if created:
       loan, created = Loan.objects.get_or_create(case=instance)
       modelSettings, created = ModelSetting.objects.get_or_create(case=instance)

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
        return smart_text(self.localLoanID)

    def __unicode__(self):
        return smart_text(self.localLoanID)


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
        return smart_text(self.id)

    def __unicode__(self):
        return smart_text(self.id)

