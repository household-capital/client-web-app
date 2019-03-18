#Python Imports
import uuid

#Django Imports
from django.db import models
from django.utils.encoding import smart_text
from django.forms import ValidationError


class WebManager(models.Manager):
    #Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self,uidString):
        searchWeb = WebCalculator.objects.get(calcUID=uuid.UUID(uidString)).pk
        return super(WebManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

    def queueCount(self):
        return WebCalculator.objects.filter(email__isnull=False, actioned=0).count()


class WebCalculator(models.Model):
    calcUID = models.UUIDField(default=uuid.uuid4, editable=False)
    loanType=models.BooleanField(default=True, blank=False, null=False)
    name=models.CharField(max_length=30,blank= True,null=True)
    age_1=models.IntegerField(blank=False, null=False)
    age_2 = models.IntegerField(blank=True, null=True)
    dwellingType=models.BooleanField(default=True, blank=False, null=False)
    valuation=models.IntegerField(blank=False, null=False)
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
    referrer=models.URLField(blank=True,null=True)
    actioned=models.IntegerField(default=0,blank=True, null=True)
    actionedBy=models.CharField(max_length=40,blank= True,null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    summaryDocument = models.FileField(null=True, blank=True)

    objects = WebManager()

    def __str__(self):
        return smart_text(self.pk)

class WebContact(models.Model):
    name=models.CharField(max_length=50,null=False, blank=False)
    email=models.EmailField(null=True,blank=True)
    phone=models.CharField(max_length=15,null=True,blank=True)
    message=models.CharField(max_length=1000,null=False,blank=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

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