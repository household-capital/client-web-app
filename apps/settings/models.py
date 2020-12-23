
from django.conf import settings
from django.urls import reverse_lazy
from django.db import models

from apps.lib.site_Utilities import SingletonModel


class GlobalSettings(SingletonModel):

    class Meta:
        verbose_name_plural = "Global Settings"

    autoassignees_calculators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        limit_choices_to={'profile__isCreditRep': True}
    )

    @property
    def get_absolute_url(self):
        return reverse_lazy("settings:globalSettings")
