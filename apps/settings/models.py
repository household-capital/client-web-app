
from django.conf import settings
from django.urls import reverse_lazy
from django.db import models
from django.db.models import Q

from apps.lib.site_Utilities import SingletonModel


class GlobalSettings(SingletonModel):

    class Meta:
        verbose_name_plural = "Global Settings"

    autoassignees_calculators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_calculators',
        blank=True,
        limit_choices_to=Q(
            Q(profile__isCreditRep=True) &
            Q(profile__calendlyUrl__isnull=False) &
            ~Q(profile__calendlyUrl='')
        )
    )

    autoassignees_STARTS_AT_60 = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_STARTS_AT_60',
        blank=True,
        limit_choices_to=Q(profile__isCreditRep=True)
    )

    autoassignees_CARE_ABOUT = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_CARE_ABOUT',
        blank=True,
        limit_choices_to=Q(profile__isCreditRep=True)
    )

    autoassignees_NATIONAL_SENIORS = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_NATIONAL_SENIORS',
        blank=True,
        limit_choices_to=Q(profile__isCreditRep=True)
    )

    autoassignees_YOUR_LIFE_CHOICES = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_YOUR_LIFE_CHOICES',
        blank=True,
        limit_choices_to=Q(profile__isCreditRep=True)
    )

    autoassignees_FACEBOOK = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_FACEBOOK',
        blank=True,
        limit_choices_to=Q(profile__isCreditRep=True)
    )

    autoassignees_LINKEDIN = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='autoassignees_LINKEDIN',
        blank=True,
        limit_choices_to=Q(profile__isCreditRep=True)
    )

    @property
    def get_absolute_url(self):
        return reverse_lazy("settings:globalSettings")
