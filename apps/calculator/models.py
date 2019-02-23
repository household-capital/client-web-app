
import uuid

from django.db import models
from django.utils.encoding import smart_text
from django.urls import reverse_lazy

class WebManager(models.Manager):
    #Custom model manager to return related querysets (using UID)
    def queryset_byUID(self,uidString):
        searchWeb = WebCalculator.objects.get(calcUID=uuid.UUID(uidString)).pk
        return super(WebManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]


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
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    objects = WebManager()

    def __str__(self):
        return smart_text(self.pk)

    def get_absolute_url(self):
        return reverse_lazy("calculator:calcInput")#, kwargs={"uid": str(self.calcUID)})


