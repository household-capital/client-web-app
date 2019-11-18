# Django Imports
from django.core.exceptions import ValidationError
from django import forms

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML

# Local Application Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum
from apps.case.models import FactFind

class FactFindForm(forms.ModelForm):
    # A model form with some overriding using form fields to enable choice field enumeration
    # and to enable valuation to be initially validated as a text field

    class Meta:
        model = FactFind
        fields = ['backgroundNotes', 'requirementsNotes', 'topUpNotes', 'refiNotes', 'liveNotes', 'giveNotes', 'careNotes',
                  'futureNotes', 'clientNotes', 'additionalNotes']
