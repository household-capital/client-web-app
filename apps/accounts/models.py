from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import smart_text


class Referer(models.Model):
    companyName=models.CharField(max_length=30,null=False,blank=False)
    companyImage=models.ImageField(null=True, blank=True, upload_to='referrerImages')

    def __str__(self):
        return smart_text(self.companyName)

    def __unicode__(self):
        return smart_text(self.companyName)

    class Meta:
        ordering = ('companyName',)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=30, null=True, blank=True)
    picture=models.ImageField(null=True, blank=True, upload_to='profileImages')
    calendlyUrl=models.URLField(null=True,blank=True)
    isHousehold=models.BooleanField(null=True,blank=True,default=False)
    isCreditRep=models.BooleanField(null=True,blank=True,default=False)
    isCapital=models.BooleanField(null=True,blank=True,default=False)
    referrer=models.ForeignKey(Referer ,null=True, blank=True, on_delete=models.SET_NULL)
