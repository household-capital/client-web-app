# Python Imports
import uuid
from datetime import datetime, timedelta

# Django Imports
from django.db import models
from django.utils.encoding import smart_text


# WebCalculator

class WebManager(models.Manager):

    # Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self, uidString):
        searchWeb = IncomeCalculator.objects.get(calcUID=uuid.UUID(uidString)).pk
        return super(WebManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self, uidString):
        return self.queryset_byUID(uidString).values()[0]

    # Custom data queries
    def queueCount(self):
        return IncomeCalculator.objects.filter(email__isnull=False, actioned=0).count()


class IncomeCalculator(models.Model):
    calcUID = models.UUIDField(default=uuid.uuid4, editable=False)

    loanType = models.BooleanField(default=True, blank=False, null=False)
    name = models.CharField(max_length=30,blank= True,null=True)
    email = models.EmailField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)

    #Client Data
    age_1 = models.IntegerField(blank=False, null=False)
    age_2 = models.IntegerField(blank=True, null=True)
    dwellingType = models.BooleanField(default=True, blank=False, null=False)
    valuation = models.IntegerField(blank=False, null=False)

    #Address Mappify
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
    errorText = models.CharField(max_length=40,blank= True,null=True)

    #Lump sum fields
    isTopUp = models.BooleanField(blank=True, null=True)
    isRefi = models.BooleanField(blank=True, null=True)
    isLive = models.BooleanField(blank=True, null=True)
    isGive = models.BooleanField(blank=True, null=True)
    isCare = models.BooleanField(blank=True, null=True)
    calcTopUp = models.IntegerField( blank=True, null=True)
    calcRefi = models.IntegerField(blank=True, null=True)
    calcLive = models.IntegerField( blank=True, null=True)
    calcGive = models.IntegerField(blank=True, null=True)
    calcCare = models.IntegerField( blank=True, null=True)
    calcTotal = models.IntegerField(blank=True, null=True)
    payIntAmount = models.IntegerField(blank=True, null=True)
    payIntPeriod = models.IntegerField(blank=True, null=True)

    #Income fields
    choiceOtherNeeds = models.BooleanField(blank=True, null=True)
    choiceMortgage = models.BooleanField(blank=True, null=True)

    #Workflow
    retrieved = models.IntegerField(default=0,blank=True, null=True)
    retrievedDate = models.DateTimeField(blank=True,null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = WebManager()

    def __str__(self):
        return smart_text(self.pk)

    def enumMaritalStatus(self):
        if self.loanType:
            return 'Couple'
        else:
            return 'Single'













class LowLVR(models.Model):
    #Model for LowLVR Income Application
    applicationUID = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.EmailField(null=False, blank=False)
    surname_1 = models.CharField(max_length=30, null=True, blank=True)
    firstname_1 = models.CharField(max_length=30, null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)


    def __str__(self):
        return smart_text(self.email)

    def __unicode__(self):
        return smart_text(self.email)

