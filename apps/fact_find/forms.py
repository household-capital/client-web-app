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
    def __init__(self, *args, **kwargs): 
        super(FactFindForm, self).__init__(*args, **kwargs)
        self.fields['planned_length_of_stay'].label = False
        self.fields['planned_method_of_discharge'].label = False
        self.fields['protected_equity'].label = False

    class Meta:
        model = FactFind
        fields = [
            'backgroundNotes', 
            'requirementsNotes', 
            'topUpNotes', 
            'refiNotes', 
            'liveNotes', 
            'giveNotes', 
            'careNotes',
            'futureNotes', 
            'clientNotes', 
            'additionalNotes',
            # meeting data
            'all_applications_are_engaged',
            'applicants_disengagement_reason',
            'is_third_party_engaged',
            'reason_for_thirdparty_engagement',
            'applicant_poa_signing',
            'planned_length_of_stay',
            'planned_method_of_discharge',
            # customer data 
            'is_vulnerable_customer',
            'vulnerability_description',
            'considered_alt_downsizing_opts',
            'is_protected_equity',
            'protected_equity',
            'plan_for_future_giving',
            'plan_for_aged_care',
            #purposes
            'additional_info_credit'
        ]
