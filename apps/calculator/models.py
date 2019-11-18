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

    def __timeSeriesQry(self, qs, length):
        #utility function appended to base time series query
        tz = get_current_timezone()
        qryDate=datetime.today()-timedelta(days=length)

        return qs.filter(timestamp__gte=qryDate).annotate(date=Cast(TruncDay('timestamp', tzinfo=tz), DateField())) \
                   .values_list('date') \
                   .annotate(interactions=Count('postcode',distinct=True)) \
                   .values_list('date', 'interactions').order_by('-date')

    def timeSeries(self, seriesType, length, search=None):
        tz = get_current_timezone()

        if seriesType == 'Interactions':
            return self.__timeSeriesQry(WebCalculator.objects.all(),length)

        if seriesType == 'Email':
            return self.__timeSeriesQry(WebCalculator.objects.filter(email__isnull=False),length)

        if seriesType == 'InteractionsByState':
            return self.__timeSeriesQry(WebCalculator.objects.filter(postcode__startswith=search),length)

        if seriesType == 'InteractionsBySource' and search == True:
            return self.__timeSeriesQry(WebCalculator.objects.filter(referrer__icontains='calculator'), length)

        if seriesType == 'InteractionsBySource' and search == False:
            return self.__timeSeriesQry(WebCalculator.objects.exclude(referrer__icontains='calculator'), length)

        if seriesType == 'EmailBySource' and search == True:
            return self.__timeSeriesQry(WebCalculator.objects.filter(referrer__icontains='calculator').filter(
                email__isnull=False), length)

        if seriesType == 'EmailBySource' and search == False:
            return self.__timeSeriesQry(WebCalculator.objects.filter(email__isnull=False).exclude(
                referrer__icontains='calculator'), length)


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
    isTopUp = models.BooleanField(blank=True, null=True)
    isRefi = models.BooleanField(blank=True, null=True)
    isLive = models.BooleanField(blank=True, null=True)
    isGive = models.BooleanField(blank=True, null=True)
    isCare = models.BooleanField(blank=True, null=True)
    calcTopUp=models.IntegerField( blank=True, null=True)
    calcRefi=models.IntegerField(blank=True, null=True)
    calcLive=models.IntegerField( blank=True, null=True)
    calcGive=models.IntegerField(blank=True, null=True)
    calcCare = models.IntegerField( blank=True, null=True)
    calcTotal=models.IntegerField(blank=True, null=True)
    payIntAmount=models.IntegerField(blank=True, null=True)
    payIntPeriod = models.IntegerField(blank=True, null=True)
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




# WebCalculator

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
    message=models.CharField(max_length=1000,null=False,blank=False)
    actioned = models.IntegerField(default=0, blank=True, null=True)
    actionNotes=models.CharField(max_length=1000,null=True,blank=True)
    actionedBy=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    actionDate=models.DateField(blank=True, null=True)
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