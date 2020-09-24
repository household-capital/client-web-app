#Python Imports
import uuid
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db import models
from django.utils.encoding import smart_text
from django.utils import timezone

class CalendlyManager(models.Manager):

    #Custom model manager to return related querysets (using UID)
    def queryset_byUID(self,uidString):
        return Calendly.objects.filter(meetingUID=uuid.UUID(uidString))


class Calendly(models.Model):

    meetingUID = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    meetingName = models.CharField(max_length=50, blank=True, null=True)
    calendlyID = models.CharField(max_length=16, blank=False, null=False)
    startTime = models.DateTimeField(blank=True, null=True)
    timeZone = models.CharField(max_length=50, blank=True, null=True)
    zoomID = models.CharField(max_length=11, blank=True, null=True)
    customerName = models.CharField(max_length=50, blank=True, null=True)
    customerEmail = models.EmailField(null=True, blank=True)
    customerPhone = models.CharField(max_length=16, blank=True, null=True)
    enqUID = models.UUIDField(null = True, blank=True)
    caseUID = models.UUIDField(null = True, blank=True)
    isCalendlyLive = models.BooleanField(default=True)
    isZoomLive = models.BooleanField(default=False)

    def __str__(self):
        return smart_text(self.customerEmail)