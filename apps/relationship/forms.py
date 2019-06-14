# Python Imports
from datetime import datetime

# Django Imports
from django.core.exceptions import ValidationError
from django import forms
from django.forms import widgets

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML

# Local Application Imports
from .models import Contact, Organisation


class ContactDetailsForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['firstName', 'surname', 'org', 'role', 'email',
                  'phone', 'location', 'classification', 'equityInterest', 'debtInterest', 'equityStatus',
                  'notes', 'relationshipNotes', 'relationshipOwners', 'inProfileUrl']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 8, 'cols': 100}),
            'relationshipNotes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
        }

    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(HTML("<i class='fas fa-edit'></i>&nbsp;&nbsp;<small>Contact Notes</small>"),
                Field('notes', placeholder='Contact Notes'), css_class="col-lg-6"),
            Div(HTML("<i class='far fa-edit'></i>&nbsp;&nbsp;<small>Relationship Notes</small>"),
                Field('relationshipOwners', placeholder='Owner(s) - Initials'),
                Field('relationshipNotes', placeholder='Relationship Notes'), css_class="col-lg-6"),

            css_class="row "),

        Div(
            Div(HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;<small>Contact Details</small>"),
                Field('firstName', placeholder='Firstname'),
                Field('surname', placeholder='Surname'),
                Field('org', placeholder='Organisation'),
                Field('role', placeholder='Role'),
                Field('email', placeholder='Email'),
                Field('phone', placeholder='Phone'),
                Field('location', placeholder='location'),
                Field('inProfileUrl', placeholder='LinkedIn URL'),
                css_class="col-lg-6"),

            Div(
                Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;<small>Classification</small>"),
                    Field('classification', placeholder='classification'),
                    HTML("<i class='fas fa-search-dollar''></i>&nbsp;&nbsp;<small>Financial Interest</small>"),
                    Div(
                        Div(Field('debtInterest'), css_class='checkbox-inline'),
                        Div(HTML("&nbsp;&nbsp;Debt&nbsp;&nbsp;"), css_class='checkbox-inline'),
                        Div(Field('equityInterest'), css_class='checkbox-inline'),
                        Div(HTML("&nbsp;&nbsp;Equity"), css_class='checkbox-inline'),
                        css_class='row justify-content-left pt-2'),
                    HTML("<i class='fas fa-user-clock'></i>&nbsp;&nbsp;<small>Equity Status</small>"),
                    Div(Field('equityStatus', placeholder='equityStatus'), css_class="pt-2")),
                Div(
                    Div(Submit('submit', 'Update ', css_class='btn btn-outline-secondary'))),
                css_class="col-lg-6")
            , css_class="row"))

    def clean_org(self):
        if self.cleaned_data['org']:
            return self.cleaned_data['org']
        else:
            raise ValidationError("Please add an organisation")

    def clean_classification(self):
        if self.cleaned_data['classification']:
            return self.cleaned_data['classification']
        else:
            raise ValidationError("Please add a classification")


class OrganisationDetailsForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['orgName', 'orgType']

    # Form Layout

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(

        Div(
            Div(HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;<small>Organisation Details</small>"),
                Field('orgName', placeholder='Organisation Name'),
                Field('orgType', placeholder='Organisation Type'),
                Submit('submit', 'Update ', css_class='btn btn-outline-secondary'),
                css_class="col-lg-6")))

    def clean_orgType(self):
        if self.cleaned_data['orgType']:
            return self.cleaned_data['orgType']
        else:
            raise ValidationError("Please add an Organisation Type")
