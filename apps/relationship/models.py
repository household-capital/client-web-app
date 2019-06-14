# Python Imports
import uuid
from datetime import datetime, timedelta

# Django Imports
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import smart_text
from django.urls import reverse_lazy


# Local Imports


class OrganisationType(models.Model):
    orgTypeId = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    orgType = models.CharField(max_length=40, blank=False, null=False)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return smart_text(self.orgType)

    def __unicode__(self):
        return smart_text(self.orgType)

    class Meta:
        ordering = ('orgType',)


class Organisation(models.Model):
    ordId = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    orgName = models.CharField(max_length=40, blank=False, null=False, unique=True)
    orgType = models.ForeignKey(OrganisationType, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return smart_text(self.orgName)

    def __unicode__(self):
        return smart_text(self.orgName)

    class Meta:
        ordering = ('orgName',)


class Contact(models.Model):
    locationValues = (
        (2, 'VIC'),
        (4, 'NSW'),
        (6, 'QLD'),
        (8, 'SA'),
        (10, 'WA'),
        (12, 'TAS'),
        (14, 'ACT'),
        (16, 'NT'),
        (20, 'FR'),
        (25, 'GE'),
        (30, 'HK'),
        (35, 'IR'),
        (40, 'JP'),
        (45, 'NZ'),
        (50, 'SG'),
        (55, 'UK'),
        (60, 'US'),
    )

    classificationTypes = (
        (2, 'Capital'),
        (4, 'Distribution'),
        (6, 'Investor'),
        (8, 'Product'),
        (10, 'Platform'),
        (12, 'Other'),
    )

    statusTypes = (
        (2, 'Active'),
        (4, 'Inactive'),
        (6, 'Declined'),
    )

    contId = models.AutoField(primary_key=True)
    firstName = models.CharField(max_length=40, blank=False, null=False)
    surname = models.CharField(max_length=40, blank=False, null=False)
    org = models.ForeignKey(Organisation, null=True, blank=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.IntegerField(choices=locationValues, blank=True, null=True)
    classification = models.IntegerField(choices=classificationTypes, blank=True, null=True)
    equityInterest = models.BooleanField(default=False)
    debtInterest = models.BooleanField(default=False)
    equityStatus = models.IntegerField(choices=statusTypes, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    relationshipNotes = models.TextField(blank=True, null=True)
    relationshipOwners = models.CharField(max_length=40, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    inProfileUrl = models.URLField(null=True, blank=True)
    inName = models.CharField(max_length=40, null=True, blank=True)
    inDescription = models.CharField(max_length=200, null=True, blank=True)
    inPic = models.ImageField(null=True, blank=True, upload_to='relationshipImages')
    inDate = models.DateField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return smart_text(self.firstName + " " + self.surname + " - " + self.org.orgName)

    def __unicode__(self):
        return smart_text(self.firstName + " " + self.surname + " - " + self.org.orgName)

    def get_absolute_url(self):
        return reverse_lazy("relationship:contactDetail", kwargs={"contId": self.contId})

    class Meta:
        ordering = ('surname',)

    @property
    def enumClassification(self):
        if self.classification:
            return dict(self.classificationTypes)[self.classification]
        else:
            return None

    @property
    def enumLocation(self):
        if self.location:
            return dict(self.locationValues)[self.location]
        else:
            return None

    @property
    def enumEquityStatus(self):
        if self.equityStatus:
            return dict(self.statusTypes)[self.equityStatus]
        else:
            return None

    @property
    def ownerList(self):
        if self.relationshipOwners:
            return self.relationshipOwners.split("/")
        else:
            return []
