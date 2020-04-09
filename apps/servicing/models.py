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

from apps.lib.site_Enums import caseStagesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,\
    pensionTypesEnum, loanTypesEnum, ragTypesEnum, channelTypesEnum, stateTypesEnum, incomeFrequencyEnum, \
    closeReasonEnum, salutationEnum, maritalEnum, appTypesEnum, roleEnum, authTypesEnum, facilityStatusEnum



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

class FacilityManager(models.Manager):

    def queueCount(self):
        return FacilityEnquiry.objects.filter(actioned=0).count()

    #Custom model manager to return related querysets (using UID)
    def queryset_byUID(self,uidString):
       if self.model.__name__=='Facility':
            searchCase=Facility.objects.get(facilityUID=uuid.UUID(uidString)).facilityUID
            return super(FacilityManager,self).filter(facilityUID=searchCase)
       else:
           searchCase = Facility.objects.get(caseUID=uuid.UUID(uidString))
           return super(FacilityManager, self).filter(facility=searchCase)

class Facility(models.Model):

    facilityStatus = (
                       (facilityStatusEnum.INACTIVE.value, "Inactive"),
                       (facilityStatusEnum.ACTIVE.value, "Active"),
                       (facilityStatusEnum.REPAID.value, "Repaid"),
                       (facilityStatusEnum.SUSPENDED.value, "Suspended")
    )

    facilityUID = models.UUIDField(default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    originalCaseUID = models.UUIDField(null=False, blank=False, unique=True )
    meetingDate = models.DateTimeField(blank=True, null=True)

    sfLoanName = models.CharField(max_length=80, null=False, blank=False)
    sfID = models.CharField(max_length=20, null=False, blank=False, unique=True)
    sfLoanID = models.CharField(max_length=20, null=True, blank=True)
    sfAccountID = models.CharField(max_length=20, null=False, blank=False)
    sfReferrerAccount = models.CharField(max_length=20, null=True, blank=True)
    amalID = models.CharField(max_length=20, null=False, blank=False)
    sfOriginatorID = models.CharField(max_length=20, null=False, blank=False)

    status = models.IntegerField(choices=facilityStatus)
    settlementDate =  models.DateTimeField(blank=True, null=True)
    dischargeDate = models.DateTimeField(blank=True, null=True)
    maxDrawdownDate =  models.DateTimeField(blank=True, null=True)
    maturityDate =  models.DateTimeField(blank=True, null=True)
    totalPurposeAmount =  models.FloatField(default=0)
    totalEstablishmentFee = models.FloatField(default=0)
    totalLoanAmount = models.FloatField(default=0)
    totalPlanPurposeAmount = models.FloatField(default=0)
    totalPlanEstablishmentFee = models.FloatField(default=0)
    totalPlanAmount = models.FloatField(default=0)
    totalValuation = models.FloatField(default=1, blank=True, null=True)
    establishmentFeeRate = models.FloatField(default=0)

    approvedAmount = models.FloatField(default=0)
    advancedAmount = models.FloatField(default=0)
    currentBalance = models.FloatField(default=0)
    currentLVR  = models.FloatField(default=0)
    bPayBillerCode = models.CharField(max_length=20, null=True, blank=True)
    bPayReference = models.CharField(max_length=20, null=True, blank=True)

    relationshipNotes = models.TextField(blank=True, null=True)
    bsbNumber = models.CharField(max_length=20, null=True, blank=True)
    bankAccountNumber = models.CharField(max_length=20, null=True, blank=True)
    lastAnnualService = models.DateTimeField(blank=True, null=True)

    amalReconciliation = models.BooleanField(default=False)
    amalBreach = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects=FacilityManager()

    class Meta:
        verbose_name_plural = "Facilities"

    def __str__(self):
        return smart_text(self.sfLoanName)

    def __unicode__(self):
        return smart_text(self.sfLoanName)

    def get_absolute_url(self):
        return reverse_lazy("servicing:loanDetail", kwargs={"uid": self.facilityUID})

    def enumStatus(self):
        return dict(self.facilityStatus)[self.status]


class FacilityTransactions(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
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

    objects = FacilityManager()

    def __str__(self):
        return smart_text(self.facility)

    def __unicode__(self):
        return smart_text(self.facility)

    class Meta:
        verbose_name_plural = "Facility Transactions"
        unique_together = (('facility', 'tranRef'),)


class FacilityRoles(models.Model):

    roleTypes = (
        (roleEnum.PRINCIPAL_BORROWER.value, "Principal Borrower"),
        (roleEnum.SECONDARY_BORROWER.value, "Secondary Borrower"),
        (roleEnum.BORROWER.value, "Borrower"),
        (roleEnum.NOMINATED_OCCUPANT.value, "Nominated Occupant"),
        (roleEnum.PERMITTED_COHABITANT.value, "Permitted Cohabitant"),
        (roleEnum.POWER_OF_ATTORNEY.value, "Power of Attorney"),
        (roleEnum.AUTH_3RD_PARTY.value, "Authorised 3rd Party"),
        (roleEnum.DISTRIBUTION_PARTNER.value, "Distribution Partner Contact"),
        (roleEnum.ADVISER.value, "Adviser"),
        (roleEnum.LOAN_ORIGINATOR.value, "Loan Originator"),
        (roleEnum.LOAN_WRITER.value, "Loan Writer"),
        (roleEnum.VALUER.value, "Valuer"),
        (roleEnum.EXECUTOR.value, "Executor"),
    )

    authorisationTypes = (
        (authTypesEnum.NO.value, "No"),
        (authTypesEnum.YES.value, "Yes"),
        (authTypesEnum.REFER_POA.value, "Refer POA"),
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

    clientSex=(
        (clientSexEnum.FEMALE.value, 'Female'),
        (clientSexEnum.MALE.value, 'Male'))

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    sfContactID = models.CharField(max_length=20, null=False, blank=False, unique=True)
    role = models.IntegerField(choices=roleTypes)
    isContact = models.BooleanField(default=False)
    isInformation = models.BooleanField(default=False)
    isAuthorised = models.IntegerField(choices=authorisationTypes, default=0)
    lastName = models.CharField(max_length=30, blank=True, null=True)
    firstName = models.CharField(max_length=30, blank=True, null=True)
    preferredName = models.CharField(max_length=30, blank=True, null=True)
    middleName =  models.CharField(max_length=30, blank=True, null=True)
    salutation = models.IntegerField(choices=salutationTypes, blank=True, null=True)
    birthdate = models.DateField(null=True, blank=True)
    gender = models.IntegerField(choices=clientSex, blank=True, null=True)
    maritalStatus = models.IntegerField(choices=maritalTypes, blank=True, null=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    street  = models.CharField(max_length=60, null=True, blank=True)
    suburb  = models.CharField(max_length=30, null=True, blank=True)
    state  = models.IntegerField(choices=stateTypes, null=True, blank=True)
    postcode = models.CharField(max_length=4, null=True, blank=True)
    roleNotes = models.TextField(blank=True, null=True)

    def enumRole(self):
        if self.role is not None:
            return dict(self.roleTypes)[self.role]

    def enumSalutation(self):
        if self.salutation is not None:
            return dict(self.salutationTypes)[self.salutation]

    def enumGender(self):
        if self.gender is not None:
            return dict(self.clientSex)[self.gender]

    def enumMaritalStatus(self):
        if self.maritalStatus is not None:
            return dict(self.maritalTypes)[self.maritalStatus]

    def enumState(self):
        if self.state is not None:
            return dict(stateTypes)[self.state]

    def enumAuthorisation(self):
        if self.isAuthorised is not None:
            return dict(self.authorisationTypes)[self.isAuthorised]

    class Meta:
        verbose_name_plural = "Facility Roles"
        ordering = ('role',)

    def __str__(self):
        return smart_text(self.firstName + " "+self.lastName+ " - "+ self.enumRole())

    def __unicode__(self):
        return smart_text(self.firstName + " "+self.lastName+ " - "+ self.enumRole())


class FacilityProperty(models.Model):

    dwellingTypes=(
        (dwellingTypesEnum.HOUSE.value, 'House'),
        (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    sfPropertyID = models.CharField(max_length=20, null=False, blank=False, unique=True)
    street = models.CharField(max_length=80, null=True, blank=True)
    suburb = models.CharField(max_length=30, null=True, blank=True)
    state = models.IntegerField(choices=stateTypes, null=True, blank=True)
    postcode = models.CharField(max_length=4, null=True, blank=True)
    dwellingType = models.IntegerField(choices=dwellingTypes, null=True, blank=True)
    insuranceCompany = models.CharField(max_length=60, null=True, blank=True)
    insurancePolicy = models.CharField(max_length=80, null=True, blank=True)
    insuranceExpiryDate = models.DateTimeField(blank=True, null=True)
    insuredAmount = models.FloatField(default=0,blank=True, null=True)

    def enumState(self):
        if self.state is not None:
            return dict(stateTypes)[self.state]

    class Meta:
        verbose_name_plural = "Facility Property"

    def __str__(self):
        return smart_text(self.facility.sfLoanName)

    def __unicode__(self):
        return smart_text(self.facility.sfLoanName)

class FacilityPropertyVal(models.Model):

    valTypes =(
        (0, "Auto Valuation"),
        (1, "Full Valuation"),
        (2, "Rates Valuation")
    )

    property = models.ForeignKey(FacilityProperty, on_delete=models.CASCADE)
    valuationAmount = models.FloatField(default=0,blank=True, null=True)
    valuationDate = models.DateTimeField(blank=True, null=True)
    valuationType = models.IntegerField(choices=valTypes, default=0)
    valuationCompany = models.CharField(max_length=20, blank=True, null=True)
    valuerName = models.CharField(max_length=40, blank=True, null=True)

    def enumValType(self):
        if self.valuationType is not None:
            return dict(self.valTypes)[self.valuationType]

    class Meta:
        verbose_name_plural = "Facility Property Valuation"


class FacilityPurposes(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    sfPurposeID = models.CharField(max_length=20, null=False, blank=False, unique=True)
    category = models.CharField(max_length=20, blank=False, null=False)
    intention = models.CharField(max_length=30, blank=False, null=False)
    amount = models.FloatField(default=0,blank=True, null=True)
    drawdownAmount = models.FloatField(default=0,blank=True, null=True)
    drawdownFrequency = models.CharField(max_length=20, blank=True, null=True)
    drawdownStartDate = models.DateTimeField(blank=True, null=True)
    drawdownEndDate = models.DateTimeField(blank=True, null=True)
    planAmount = models.FloatField(default=0,blank=True, null=True)
    planPeriod = models.IntegerField(default = 0, blank=True, null=True)
    topUpBuffer = models.BooleanField(default = False)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Facility Purposes"


class FacilityEvents(models.Model):

    eventTypes = (
        (1, 'Loan Settlement'),
        (2, 'Loan Variation'),
        (3, 'Loan Repaid'),
        (4, 'Death of a Borrower'),
        (5, 'Repayment Event'),
    )

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    eventDate = models.DateTimeField(blank=False, null=False)
    eventType = models.IntegerField(choices = eventTypes)
    eventNotes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Facility Events"

    def enumEventType(self):
        return dict(self.eventTypes)[self.eventType]

    def get_absolute_url(self):
        return self.facility.get_absolute_url()

class FacilityEnquiry(models.Model):

    actionChoices = (
        (False, "Open"),
        (True, "Actioned")
    )

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    identifiedEnquirer = models.ForeignKey(FacilityRoles, on_delete=models.CASCADE, blank=True, null=True)
    otherEnquirerName = models.CharField(max_length=60, blank=True, null=True)
    contactEmail=models.EmailField(null=True,blank=True)
    contactPhone=models.CharField(max_length=15,null=True,blank=True)
    actionNotes = models.TextField(blank=True, null=True)
    actioned = models.BooleanField(choices = actionChoices, default = False)
    actionedBy = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='actionedBy')
    actionDate = models.DateTimeField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects=FacilityManager()

    class Meta:
        verbose_name_plural = "Facility Enquiries"

    def enumAction(self):
        return dict(self.actionChoices)[self.actioned]

    def get_absolute_url(self):
        return reverse_lazy("servicing:loanEnquiryUpdate", kwargs={"uid": self.facility.facilityUID, 'pk':self.id})


class FacilityAdditional(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    additionalUID = models.UUIDField(default=uuid.uuid4, editable=False)
    amountRequested = models.IntegerField(default=0, null=True, blank=True)
    amountEstablishmentFee = models.FloatField(default=0, null=True, blank=True)
    amountTotal = models.FloatField(default=0, null=True, blank=True)
    establishmentFeeRate = models.FloatField(default=0, null=True, blank=True)
    identifiedRequester = models.ForeignKey(FacilityRoles, on_delete=models.CASCADE, blank=True, null=True)
    requestedEmail = models.EmailField(null=True,blank=True)
    requestedIP = models.CharField(max_length=45, null=True, blank=True)
    requestedDate = models.DateTimeField(null=True,blank=True)
    choicePurposes = models.BooleanField(default=False)
    choiceNoMaterialChange = models.BooleanField(default=False)
    submitted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        verbose_name_plural = "Facility Additional Drawdown"

