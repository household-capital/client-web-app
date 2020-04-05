#Python imports
import uuid
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db.models.signals import post_save
from django.db import models
from django.utils.encoding import smart_text
from django.utils import timezone
from django.urls import reverse_lazy


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

