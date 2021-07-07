
from django.conf import settings
from django.urls import reverse_lazy
from django.db import models
from django.db.models import Q

from apps.lib.singleton import SingletonModel
from apps.enquiry.models import MarketingCampaign


class GlobalSettings(SingletonModel):

    class Meta:
        verbose_name_plural = "Global Settings"

    autoassignees_calculators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_calculators',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) &
            Q(profile__isCreditRep=True) &
            Q(profile__calendlyUrl__isnull=False) &
            ~Q(profile__calendlyUrl='')
        )
    )

    autoassignees_calculators_index = models.IntegerField(default=0)

    autoassignees_pre_qual = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_pre_qual',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) &
            Q(profile__isCreditRep=True) &
            Q(profile__calendlyUrl__isnull=False) &
            ~Q(profile__calendlyUrl='')
        )
    )
    autoassignees_pre_qual_index = models.IntegerField(default=0)

    autoassignees_STARTS_AT_60 = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_STARTS_AT_60',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )
    autoassignees_STARTS_AT_60_index = models.IntegerField(default=0)

    autoassignees_CARE_ABOUT = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_CARE_ABOUT',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )
    autoassignees_CARE_ABOUT_index = models.IntegerField(default=0)

    autoassignees_NATIONAL_SENIORS = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_NATIONAL_SENIORS',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )
    autoassignees_NATIONAL_SENIORS_index = models.IntegerField(default=0)

    autoassignees_YOUR_LIFE_CHOICES = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_YOUR_LIFE_CHOICES',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )
    autoassignees_YOUR_LIFE_CHOICES_index = models.IntegerField(default=0)
    

    autoassignees_FACEBOOK = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_FACEBOOK',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )

    autoassignees_FACEBOOK_INTERACTIVE = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_FACEBOOK_INTERACTIVE',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )

    autoassignees_FACEBOOK_CALCULATOR = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_FACEBOOK_CALCULATOR',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )

    autoassignees_LINKEDIN = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_LINKEDIN',
        blank=True,
        limit_choices_to=Q(
            Q(is_active=True) #&
            #Q(profile__isCreditRep=True)
        )
    )

    autocampaigns_STARTS_AT_60 = models.ForeignKey(MarketingCampaign, related_name='autocampaigns_STARTS_AT_60', null=True, blank=True, on_delete=models.SET_NULL)
    autocampaigns_CARE_ABOUT = models.ForeignKey(MarketingCampaign, related_name='autocampaigns_CARE_ABOUT', null=True, blank=True, on_delete=models.SET_NULL)
    autocampaigns_NATIONAL_SENIORS = models.ForeignKey(MarketingCampaign, related_name='autocampaigns_NATIONAL_SENIORS', null=True, blank=True, on_delete=models.SET_NULL)
    autocampaigns_YOUR_LIFE_CHOICES = models.ForeignKey(MarketingCampaign, related_name='autocampaigns_YOUR_LIFE_CHOICES', null=True, blank=True, on_delete=models.SET_NULL)
    autocampaigns_FACEBOOK = models.ForeignKey(MarketingCampaign, related_name='autocampaigns_FACEBOOK', null=True, blank=True, on_delete=models.SET_NULL)
    autocampaigns_LINKEDIN = models.ForeignKey(MarketingCampaign, related_name='autocampaigns_LINKEDIN', null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def get_absolute_url(self):
        return reverse_lazy("settings:globalSettings")
