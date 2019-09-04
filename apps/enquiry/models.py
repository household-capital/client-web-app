#Python Imports
import uuid
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import smart_text
from django.urls import reverse_lazy

#Local Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum, directTypesEnum, closeReasonTypes


class EnquiryManager(models.Manager):

    #Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self,uidString):
        searchWeb = Enquiry.objects.get(enqUID=uuid.UUID(uidString)).pk
        return super(EnquiryManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

    # Custom data queries
    def queueCount(self):
        return Enquiry.objects.filter(user__isnull=True,actioned=0).count()

    def openEnquiries(self):
        return Enquiry.objects.filter(actioned=0, followUp__isnull=True).exclude(status=False,user__isnull=False)

    def pipelineHealth(self):
        startdate = timezone.now() - timedelta(days=14)
        openEnq=self.openEnquiries().count()
        currentEnq=self.openEnquiries().filter(updated__gte=startdate).count()
        return [0] if openEnq == 0 else [round(currentEnq/openEnq,2),round(1-currentEnq/openEnq,2)]

class Enquiry(models.Model):

    loanTypes = (
        (loanTypesEnum.SINGLE_BORROWER.value, 'Single'),
        (loanTypesEnum.JOINT_BORROWER.value, 'Joint')
    )

    dwellingTypes = (
        (dwellingTypesEnum.HOUSE.value, 'House'),
        (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    referrerTypes=(
        (directTypesEnum.PHONE.value,'Phone'),
        (directTypesEnum.EMAIL.value, 'Email'),
        (directTypesEnum.WEB_ENQUIRY.value,'Web'),
        (directTypesEnum.REFERRAL.value, 'Referral'),
        (directTypesEnum.OTHER.value,'Other'),
        (directTypesEnum.WEB_CALCULATOR.value, 'Calculator')
    )

    closeReasons=(
        (closeReasonTypes.AGE_RESTRICTION.value, 'Age Restriction'),
        (closeReasonTypes.POSTCODE_RESTRICTION.value, 'Postcode Restriction'),
        (closeReasonTypes.MINIMUM_LOAN_AMOUNT.value, 'Below minimum loan amount'),
        (closeReasonTypes.CREDIT.value, 'Credit History'),
        (closeReasonTypes.MORTGAGE.value, 'Mortgage too Large'),
        (closeReasonTypes.SHORT_TERM.value, 'Short-term / Bridging Requirement'),
        (closeReasonTypes.TENANTS.value, 'Tenants in common'),
        (closeReasonTypes.UNSUITABLE_PROPERTY.value, 'Unsuitable Property'),
        (closeReasonTypes.UNSUITABLE_PURPOSE.value, 'Unsuitable Purpose'),
        (closeReasonTypes.ALTERNATIVE_SOLUTION.value, 'Client Pursuing Alternative'),
        (closeReasonTypes.COMPETITOR.value, 'Client went to Competitor'),
        (closeReasonTypes.OTHER.value , 'Other')
    )

    enqUID = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    loanType = models.IntegerField(choices=loanTypes, null=True, blank=True, default=True)
    name=models.CharField(max_length=30,blank= True,null=True)
    age_1=models.IntegerField(blank=True, null=True)
    age_2 = models.IntegerField(blank=True, null=True)
    dwellingType=models.IntegerField(blank=True, null=True, choices=dwellingTypes)
    valuation=models.IntegerField(blank=True, null=True)
    postcode=models.IntegerField(blank=True, null=True)
    status=models.BooleanField(default=True, blank=False, null=False)
    maxLoanAmount=models.IntegerField(blank=True, null=True)
    maxLVR=models.FloatField(blank=True, null=True)
    errorText=models.CharField(max_length=40,blank= True,null=True)
    isRefi=models.BooleanField(default=False, blank=True, null=True)
    isTopUp=models.BooleanField(default=False, blank=True, null=True)
    isLive=models.BooleanField(default=False, blank=True, null=True)
    isGive=models.BooleanField(default=False, blank=True, null=True)
    isCare = models.BooleanField(default=False, blank=True, null=True)
    calcTopUp=models.IntegerField( blank=True, null=True)
    calcRefi=models.IntegerField(blank=True, null=True)
    calcLive=models.IntegerField( blank=True, null=True)
    calcGive=models.IntegerField(blank=True, null=True)
    calcCare = models.IntegerField( blank=True, null=True)
    calcTotal=models.IntegerField(blank=True, null=True)
    payIntAmount=models.IntegerField(blank=True, null=True)
    payIntPeriod = models.IntegerField(blank=True, null=True)
    email=models.EmailField(blank=True, null=True)
    referrer=models.IntegerField(blank=False,null=False,choices=referrerTypes)
    referrerID=models.CharField(max_length=200,blank= True,null=True)
    actioned=models.IntegerField(default=0,blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    followUp = models.DateTimeField(null=True, blank=True, auto_now_add=False, auto_now=False)

    lossNotes=models.TextField(blank=True, null=True) #remove this

    closeDate = models.DateField(blank=True, null=True)
    closeReason=models.IntegerField(blank=True, null=True, choices=closeReasons)

    followUpDate=models.DateField(blank=True, null=True)
    followUpNotes = models.TextField(blank=True, null=True)
    doNotMarket = models.BooleanField(default=False)

    summaryDocument = models.FileField(null=True, blank=True)
    referralUser=models.ForeignKey(settings.AUTH_USER_MODEL, related_name='referralUser', null=True, blank=True, on_delete=models.SET_NULL)
    phoneNumber=models.CharField(max_length=15,blank=True,null=True)
    enquiryNotes=models.TextField(null=True,blank=True)
    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    isCalendly=models.BooleanField(default=False, blank=True, null=True)

    objects = EnquiryManager()

    def get_absolute_url(self):
        return reverse_lazy("enquiry:enquiryDetail", kwargs={"uid":self.enqUID})

    def enumReferrerType(self):
        if self.referrer:
            return dict(self.referrerTypes)[self.referrer]

    def enumLoanType(self):
        if self.loanType is not None:
            return dict(self.loanTypes)[self.loanType]

    def referralCompany(self):
        if self.referralUser:
            return self.referralUser.profile.referrer

    def enumDwellingType(self):
        if self.dwellingType is not None:
            return dict(self.dwellingTypes)[self.dwellingType]

    def enumCloseReason(self):
        if self.closeReason is not None:
            return dict(self.closeReasons)[self.closeReason]

    def __str__(self):
        return smart_text(self.email)

    class Meta:
        ordering = ('-updated',)
