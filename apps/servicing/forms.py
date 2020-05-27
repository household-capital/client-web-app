# Django Imports
from django.core.exceptions import ValidationError
from django import forms

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML

# Local Application Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum
from .models import FacilityEnquiry, FacilityRoles


class FacilityEnquiryForm(forms.ModelForm):

    facility_instance = None

    def __init__(self, *args, **kwargs):
        if kwargs['facility_instance']:
            facility_instance = kwargs['facility_instance']
            kwargs.pop('facility_instance')

        super(FacilityEnquiryForm, self).__init__(*args, **kwargs)

        if facility_instance:
            self.fields['identifiedEnquirer'].queryset = FacilityRoles.objects.filter(facility=facility_instance)

    class Meta:
        model = FacilityEnquiry
        fields = ['identifiedEnquirer', 'otherEnquirerName', 'contactEmail', 'contactPhone','enquiryNotes', 'actioned','actionNotes']

        widgets = {'enquiryNotes': forms.Textarea(attrs={'rows': 9, 'cols': 50}),
                   'actionNotes': forms.Textarea(attrs={'rows': 8, 'cols': 50}) }

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Enquiry Details</small>")),
                Div(Div(HTML("Identified Enquirer"), css_class='form-label'),
                    Div(Field('identifiedEnquirer'))),
                Div(Div(HTML("-or- name of non-identified enquirer "), css_class='form-label'),
                    Div(Field('otherEnquirerName'))),
                Div(Div(HTML("Contact Email"), css_class='form-label'),
                    Div(Field('contactEmail'))),
                Div(Div(HTML("Contact Phone"), css_class='form-label'),
                    Div(Field('contactPhone'))),
                Div(Div(HTML("Enquiry Notes"), css_class='form-label'),
                    Div(Field('enquiryNotes'))),
                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='fas fa-pencil-alt'></i>&nbsp;&nbsp;<small>Actions</small>")),
                Div(Div(HTML("Action Notes"), css_class='form-label'),
                    Div(Field('actionNotes'))),
                Div(Div(HTML("Status"), css_class='form-label'),
                    Div(Field('actioned'))),
                Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')),
                css_class='col-lg-6'),
            css_class="row"))

    def clean(self):
        if not self.cleaned_data['contactEmail'] and not self.cleaned_data['contactPhone'] :
            raise ValidationError("Phone number of email required")