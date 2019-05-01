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
from apps.lib.enums import dwellingTypesEnum, loanTypesEnum, directTypesEnum


class EnquiryManager(models.Manager):
    #Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self,uidString):
        searchWeb = Enquiry.objects.get(enqUID=uuid.UUID(uidString)).pk
        return super(EnquiryManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

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
    email=models.EmailField(blank=True, null=True)
    referrer=models.IntegerField(blank=False,null=False,choices=referrerTypes)
    referrerID=models.CharField(max_length=200,blank= True,null=True)
    actioned=models.IntegerField(default=0,blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    followUp = models.DateTimeField(null=True, blank=True, auto_now_add=False, auto_now=False)
    followUpDate=models.DateField(blank=True, null=True)
    summaryDocument = models.FileField(null=True, blank=True)

    phoneNumber=models.CharField(max_length=15,blank=True,null=True)
    enquiryNotes=models.TextField(null=True,blank=True)

    objects = EnquiryManager()

    def get_absolute_url(self):
        return reverse_lazy("enquiry:enquiryDetail", kwargs={"uid":self.enqUID})

    def enumReferrerType(self):
            return dict(self.referrerTypes)[self.referrer]

    def __str__(self):
        return smart_text(self.email)

    class Meta:
        ordering = ('-updated',)
