#Python Imports
import uuid
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db import models
from django.forms import ValidationError
from django.utils.encoding import smart_text
from django.urls import reverse_lazy
from django.db.models import Count
from django.db.models.functions import TruncDate,TruncDay, Cast
from django.db.models.fields import DateField
from django.utils.timezone import get_current_timezone

from apps.lib.site_Enums import *


# WebCalculator

class WebManager(models.Manager):

    # Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self, uidString):
        searchWeb = WebCalculator.objects.get(calcUID=uuid.UUID(uidString)).pk
        return super(WebManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self, uidString):
        return self.queryset_byUID(uidString).values()[0]

    # Custom data queries
    def queueCount(self):
        return WebCalculator.objects.filter(email__isnull=False, actioned=0).count()


class WebCalculator(models.Model):
    dwellingTypes = (
        (dwellingTypesEnum.HOUSE.value, 'House'),
        (dwellingTypesEnum.APARTMENT.value, 'Apartment'))


    loanTypes=(
        (loanTypesEnum.SINGLE_BORROWER.value,'Single'),
        (loanTypesEnum.JOINT_BORROWER.value,'Joint')
    )

    productTypes = (
        (productTypesEnum.LUMP_SUM.value, "Lump Sum"),
        (productTypesEnum.INCOME.value, "Income"),
        (productTypesEnum.COMBINATION.value, "Combination"),
        (productTypesEnum.CONTINGENCY_20K.value, "Contingency 20K"),
        (productTypesEnum.REFINANCE.value, "Refinance"),
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

    calcUID = models.UUIDField(default=uuid.uuid4, editable=False)
    productType = models.IntegerField(choices=productTypes, null=True, blank=True, default=0)
    referrer = models.URLField(blank=True, null=True)

    # Client Data
    name = models.CharField(max_length=121, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phoneNumber = models.CharField(max_length=15, blank=True, null=True)
    loanType = models.BooleanField(default=True, blank=False, null=False)
    age_1 = models.IntegerField(blank=False, null=False)
    age_2 = models.IntegerField(blank=True, null=True)
    dwellingType = models.BooleanField(default=True, blank=False, null=False)
    valuation = models.IntegerField(blank=False, null=False)
    mortgageDebt = models.IntegerField(blank=True, null=True)
    mortgageRepayment = models.IntegerField(blank=True, null=True)

    # Address Data
    streetAddress = models.CharField(max_length=80, blank=True, null=True)
    suburb = models.CharField(max_length=40, blank=True, null=True)
    state = models.IntegerField(choices=stateTypes, null=True, blank=True)
    postcode = models.IntegerField(blank=True, null=True)

    # Calculated Fields
    status = models.BooleanField(default=True, blank=False, null=False)
    maxLoanAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownMonthly = models.IntegerField(blank=True, null=True)
    maxLVR = models.FloatField(blank=True, null=True)
    errorText = models.CharField(max_length=40, blank=True, null=True)

    # Calculator fields
    isTopUp = models.BooleanField(blank=True, null=True)
    isRefi = models.BooleanField(blank=True, null=True)
    isLive = models.BooleanField(blank=True, null=True)
    isGive = models.BooleanField(blank=True, null=True)
    isCare = models.BooleanField(blank=True, null=True)
    calcLumpSum = models.IntegerField(blank=True, null=True)
    calcIncome = models.IntegerField(blank=True, null=True)

    # Analytics fields
    submissionOrigin = models.CharField(max_length=200, blank=True, null=True)

    # Workflow
    application = models.BooleanField(default=False, blank=False, null=False)
    actioned=models.IntegerField(default=0,blank=True, null=True)
    actionedBy=models.CharField(max_length=40,blank= True,null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    sourceID = models.CharField(max_length=36, null=True, blank=True)
    requestedCallback = models.BooleanField(default=False, blank=False, null=False)

    # Other
    calcTopUp = models.IntegerField(blank=True, null=True) #deprecated
    calcRefi = models.IntegerField(blank=True, null=True) #deprecated
    calcLive = models.IntegerField(blank=True, null=True) #deprecated
    calcGive = models.IntegerField(blank=True, null=True) #deprecated
    calcCare = models.IntegerField(blank=True, null=True) #deprecated
    calcTotal = models.IntegerField(blank=True, null=True) #deprecated
    payIntAmount = models.IntegerField(blank=True, null=True) #deprecated
    payIntPeriod = models.IntegerField(blank=True, null=True) #deprecated

    objects = WebManager()

    def __str__(self):
        return smart_text(self.pk)

    def enumLoanType(self):
            if self.loanType is not None:
                return dict(self.loanTypes)[self.loanType]

    def enumDwellingType(self):
        return dict(self.dwellingTypes)[self.dwellingType]

    def enumProductType(self):
        return dict(self.productTypes)[self.productType]


# WebContact

class WebContactManager(models.Manager):
    def queueCount(self):
        return WebContact.objects.filter(actioned=0).count()

    def queryset_byUID(self, uidString):
        searchWeb = WebContact.objects.get(contUID=uuid.UUID(uidString)).pk
        return super(WebContactManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self, uidString):
        return self.queryset_byUID(uidString).values()[0]

class WebContact(models.Model):
    contUID = models.UUIDField(default=uuid.uuid4, editable=False)
    name=models.CharField(max_length=50,null=False, blank=False)
    email=models.EmailField(null=True,blank=True)
    phone=models.CharField(max_length=15,null=True,blank=True)
    age_1 = models.IntegerField(blank=True, null=True)
    postcode = models.IntegerField(blank=True, null=True)
    message=models.CharField(max_length=1000,null=False,blank=False)
    actioned = models.IntegerField(default=0, blank=True, null=True)
    actionNotes=models.CharField(max_length=1000,null=True,blank=True)
    actionedBy=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    actionDate=models.DateField(blank=True, null=True)
    sourceID = models.CharField(max_length=36, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = WebContactManager()

    def __str__(self):
        return smart_text(self.name)

    def clean(self):
        cleaned_data = super().clean()
        if self.email!=None or self.phone!=None:
            return cleaned_data
        else:
           raise ValidationError(
                    "Please provide an email or phone number"
                )

    def get_absolute_url(self):
        return reverse_lazy("calculator:contactDetail", kwargs={"uid":self.contUID})