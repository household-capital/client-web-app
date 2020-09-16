#Django Imports
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.utils.encoding import smart_text

class Referer(models.Model):
    """
    Referrer model with basic information including flag to determine whether Referrer can create cases
    (as opposed to enquiries)
    """
    companyName = models.CharField(max_length=30,null=False,blank=False)
    companyImage = models.ImageField(null=True, blank=True, upload_to='referrerImages')
    isCaseReferrer = models.BooleanField(default = False)

    def __str__(self):
        return smart_text(self.companyName)

    def __unicode__(self):
        return smart_text(self.companyName)

    class Meta:
        ordering = ('companyName',)


class Profile(models.Model):
    """Extended user model with additional user information and identifiers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=30, null=True, blank=True)
    picture=models.ImageField(null=True, blank=True, upload_to='profileImages')
    calendlyUrl=models.URLField(null=True,blank=True)
    calendlyInterviewUrl=models.URLField(null=True,blank=True)
    isHousehold=models.BooleanField(null=True,blank=True,default=False)
    isCreditRep=models.BooleanField(null=True,blank=True,default=False)
    isCapital=models.BooleanField(null=True,blank=True,default=False)
    referrer=models.ForeignKey(Referer ,null=True, blank=True, on_delete=models.SET_NULL)
    salesforceID=models.CharField(max_length=18, null=True, blank=True)
    zoomID = models.CharField(max_length=30, null=True, blank=True)


class SessionLog(models.Model):
    """Basic session log for all user authentication"""
    description  = models.CharField(max_length=60, null=True, blank=True)
    referenceUID = models.UUIDField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)


def user_logged_in_handler(sender, request, user, **kwargs):
    """User log-in signal used to create entry in Session Log"""
    SessionLog.objects.create(
        description = "User login: "+" ".join(filter(None, [str(user.username)])),
    )

user_logged_in.connect(user_logged_in_handler)