#Python Imports
import uuid
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db import models
from django.db.models.functions import TruncDate,TruncDay, Cast
from django.db.models import Count
from django.db.models.fields import DateField
from django.utils.timezone import get_current_timezone
from django.utils.encoding import smart_text
from django.urls import reverse_lazy

#Local Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum, directTypesEnum, closeReasonEnum, \
    productTypesEnum, reasonCodeEnum, marketingTypesEnum


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

    def __timeSeriesQry(self, qs, length):
        #utility function appended to base time series query
        tz = get_current_timezone()
        qryDate=datetime.now(tz)-timedelta(days=length)

        return qs.filter(timestamp__gte=qryDate).annotate(date=Cast(TruncDay('timestamp', tzinfo=tz), DateField())) \
                   .values_list('date') \
                   .annotate(interactions=Count('enqUID',distinct=True)) \
                   .values_list('date', 'interactions').order_by('-date')

    def timeSeries(self, seriesType, length, search=None):

        if seriesType == 'Phone':
            return self.__timeSeriesQry(Enquiry.objects.filter(referrer=directTypesEnum.PHONE.value),length)


class Enquiry(models.Model):

    productTypes = (
        (productTypesEnum.LUMP_SUM.value, "Lump Sum"),
        (productTypesEnum.INCOME.value, "Income")
    )

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

    reasonTypes = (
        (reasonCodeEnum.NEW_BASIC_INFO.value, 'New - Basic information'),
        (reasonCodeEnum.NEW_SPECIFIC_NEED.value, 'New - Specific need'),
        (reasonCodeEnum.WRONG_NUMBER.value, 'Wrong number'),
        (reasonCodeEnum.NUISANCE.value, 'Nuisance number'),
        (reasonCodeEnum.OTHER.value, 'Other'),
    )
    marketingTypes = (
        (marketingTypesEnum.TV_ADVERT.value, "TV Advert"),
        (marketingTypesEnum.TV_ADVERTORIAL.value, "TV Advertorial"),
        (marketingTypesEnum.RADIO.value, "Radio"),
        (marketingTypesEnum.WORD_OF_MOUTH.value, "Word of mouth"),
        (marketingTypesEnum.COMPETITOR.value, "Competitor"),
        (marketingTypesEnum.DIRECT_MAIL.value, "Direct mail/email"),
        (marketingTypesEnum.FACEBOOK.value, "Facebook"),
        (marketingTypesEnum.LINKEDIN.value, "LinkedIn"),
        (marketingTypesEnum.YOUR_LIFE_CHOICES.value, "Your Life Choices"),
        (marketingTypesEnum.OTHER.value, "Other"),

    )


    # Identifiers
    enqUID = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    referrer=models.IntegerField(blank=False,null=False,choices=referrerTypes)
    referrerID=models.CharField(max_length=200,blank= True,null=True)
    referralUser=models.ForeignKey(settings.AUTH_USER_MODEL, related_name='referralUser', null=True, blank=True, on_delete=models.SET_NULL)
    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    callReason = models.IntegerField(blank=True, null=True, choices=reasonTypes)
    marketingSource = models.IntegerField(blank=True, null=True, choices=marketingTypes )

    #Client Data
    email=models.EmailField(blank=True, null=True)
    phoneNumber = models.CharField(max_length=15, blank=True, null=True)
    enquiryNotes = models.TextField(null=True, blank=True)

    # Enquiry Inputs
    productType = models.IntegerField(choices=productTypes, null=True, blank=True, default=0)
    loanType = models.IntegerField(choices=loanTypes, null=True, blank=True)
    name=models.CharField(max_length=30,blank= True,null=True)
    age_1=models.IntegerField(blank=True, null=True)
    age_2 = models.IntegerField(blank=True, null=True)
    dwellingType=models.IntegerField(blank=True, null=True, choices=dwellingTypes)
    valuation=models.IntegerField(blank=True, null=True)
    postcode=models.IntegerField(blank=True, null=True)
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
    calcDrawdown = models.IntegerField(blank=True, null=True)
    payIntAmount=models.IntegerField(blank=True, null=True)
    payIntPeriod = models.IntegerField(blank=True, null=True)

    #Calculated Data
    status = models.BooleanField(default=True, blank=False, null=False)
    maxLoanAmount = models.IntegerField(blank=True, null=True)
    maxLVR = models.FloatField(blank=True, null=True)
    errorText = models.CharField(max_length=40, blank=True, null=True)
    summaryDocument = models.FileField(null=True, blank=True)

    #Workflow
    actioned=models.IntegerField(default=0,blank=True, null=True)
    isCalendly=models.BooleanField(default=False, blank=True, null=True)
    followUp = models.DateTimeField(null=True, blank=True, auto_now_add=False, auto_now=False)
    secondfollowUp = models.DateTimeField(null=True, blank=True, auto_now_add=False, auto_now=False)
    closeDate = models.DateField(blank=True, null=True)
    closeReason=models.IntegerField(blank=True, null=True, choices=closeReasons)
    followUpDate=models.DateField(blank=True, null=True)
    followUpNotes = models.TextField(blank=True, null=True)
    doNotMarket = models.BooleanField(default=False)
    lossNotes=models.TextField(blank=True, null=True) #remove this

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = EnquiryManager()

    def get_absolute_url(self):
        return reverse_lazy("enquiry:enquiryDetail", kwargs={"uid":self.enqUID})

    def get_SF_url(self):
        if self.sfLeadID:
            return "https://householdcapital.lightning.force.com/lightning/r/Lead/{0}/view".format(self.sfLeadID)


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
