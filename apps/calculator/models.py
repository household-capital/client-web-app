#Python Imports
import uuid

#Django Imports
from django.db import models
from django.db.models import Count
from django.db.models.functions import TruncDate,TruncDay, Cast
from django.db.models.fields import DateField
from django.forms import ValidationError
from django.utils.encoding import smart_text
from django.utils.timezone import get_current_timezone



class WebManager(models.Manager):
    #Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self,uidString):
        searchWeb = WebCalculator.objects.get(calcUID=uuid.UUID(uidString)).pk
        return super(WebManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

    def queueCount(self):
        return WebCalculator.objects.filter(email__isnull=False, actioned=0).count()

    def timeSeries(self,seriesType,length,search=None):
        tz=get_current_timezone()
        if seriesType=='Interactions':
            return WebCalculator.objects\
                .annotate(date=Cast(TruncDay('timestamp',tzinfo=tz),DateField()))\
                .values_list('date')\
                .annotate(interactions=Count('calcUID'))\
                .values_list('date','interactions').order_by('-date')[:length]
        if seriesType=='Email':
            return WebCalculator.objects\
                .filter(email__isnull=False).annotate(date=Cast(TruncDay('timestamp',tzinfo=tz),DateField()))\
                .values_list('date')\
                .annotate(interactions=Count('calcUID'))\
                .values_list('date','interactions').order_by('-date')[:length]
        if seriesType=='InteractionsByState':
            return WebCalculator.objects.filter(postcode__startswith=search).annotate(date=Cast(TruncDay('timestamp',tzinfo=tz),DateField()))\
                .values_list('date')\
                .annotate(interactions=Count('calcUID'))\
                .values_list('date','interactions').order_by('-date')[:length]
        if seriesType=='InteractionsBySource' and search==True:
            return WebCalculator.objects.filter(referrer__icontains='calculator').annotate(date=Cast(TruncDay('timestamp',tzinfo=tz),DateField()))\
                .values_list('date')\
                .annotate(interactions=Count('calcUID'))\
                .values_list('date','interactions').order_by('-date')[:length]
        if seriesType == 'InteractionsBySource' and search == False:
            return WebCalculator.objects.exclude(referrer__icontains='calculator').annotate(date=Cast(TruncDay('timestamp', tzinfo=tz), DateField())) \
                       .values_list('date') \
                       .annotate(interactions=Count('calcUID')) \
                       .values_list('date', 'interactions').order_by('-date')[:length]


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