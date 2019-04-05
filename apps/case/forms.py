# Python Imports
from datetime import datetime

# Django Imports
from django import forms
from django.forms import widgets

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML

# Local Application Imports
from apps.lib.enums import loanTypesEnum, ragTypesEnum
from .models import Case, LossData


class CaseDetailsForm(forms.ModelForm):
    # A model form with some overriding using form fields for rendering purposes
    # Additional HTML rendering in the form

    valuation = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    mortgageDebt = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    superAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    pensionAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    propertyImage = forms.ImageField(required=False, widget=forms.FileInput)
    valuationDocument = forms.FileField(required=False, widget=forms.FileInput)
    titleDocument = forms.FileField(required=False, widget=forms.FileInput)

    class Meta:
        model = Case
        fields = ['caseDescription', 'adviser', 'caseNotes', 'loanType', 'caseType',
                  'clientType1', 'surname_1', 'firstname_1', 'birthdate_1', 'age_1', 'sex_1',
                  'clientType2', 'surname_2', 'firstname_2', 'birthdate_2', 'age_2', 'sex_2',
                  'street', 'suburb', 'postcode', 'valuation', 'dwellingType', 'propertyImage', 'mortgageDebt',
                  'superFund', 'valuationDocument', 'state', 'titleDocument',
                  'superAmount', 'pensionType', 'pensionAmount', 'salesChannel', 'phoneNumber', 'email']
        widgets = {
            'caseNotes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
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
            HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;<small>Case Notes</small>"),
            Div(
                Div(Field('caseDescription', placeholder='Description'), css_class="col-lg-6"),
                Div(
                    Div(Submit('submit', 'Update Case ', css_class='btn btn-warning')),
                    css_class="col-lg-4 text-left"),
                Div(css_class="col-lg-6"),
                css_class="row "),
            Div(
                Div(Field('adviser', placeholder='Introducer or Advisor'), css_class="col-lg-6"),
                Div(Field('caseType', placeholder='Case Status'), css_class="col-lg-6"),
                css_class="row"),
            Div(Field('caseNotes', placeholder='Case Notes')),
            Div(
                Div(HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;<small>Contact Details</small>"),
                    Field('phoneNumber', placeholder='Phone'),
                    Field('email', placeholder='Email'),
                    HTML("<br>"),
                    HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Borrower(s)</small>"),
                    Field('loanType', placeholder='Loan Type'),
                    HTML("<br>"),
                    HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Client Details</small>"),
                    Field('birthdate_1', placeholder='Birthdate'),
                    Field('age_1', placeholder='Age'),
                    Field('surname_1', placeholder='Surname'),
                    Field('firstname_1', placeholder='Firstname'),
                    Field('sex_1', placeholder='Gender'),
                    Field('clientType1', placeholder='Client Type'),
                    HTML("<br>"),
                    HTML("<i class='far fa-user'></i>&nbsp;&nbsp;<small>Client Details</small>"),
                    Field('birthdate_2', placeholder='Birthdate'),
                    Field('age_2', placeholder='Age'),
                    Field('surname_2', placeholder='Surname'),
                    Field('firstname_2', placeholder='Firstname'),
                    Field('sex_2', placeholder='Gender'),
                    Field('clientType2', placeholder='Client Type'),
                    css_class="col-lg-6"),
                Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;<small>Property</small>"),
                    Field('postcode', placeholder='Postcode'),
                    Field('dwellingType', placeholder='Dwelling Type'),
                    Field('street', placeholder='Street Address'),
                    Field('suburb', placeholder='Suburb'),
                    Field('state', placeholder='State'),
                    Field('valuation', placeholder='Valuation'),
                    Field('mortgageDebt', placeholder='Existing Mortgage'),
                    HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;<small>Super/Investments</small>"),
                    Field('superFund', placeholder='Super Fund'),
                    Field('superAmount', placeholder='Super Amount'),
                    HTML("<i class='fas fa-hand-holding-usd'></i>&nbsp;&nbsp;<small>Pension</small>"),
                    Field('pensionAmount', placeholder='Pension Amount (per fortnight)'),
                    Field('pensionType', placeholder='Pension Type'),
                    Div(HTML("<p class='small pt-2'><i class='fa fa-camera fa-fw'>&nbsp;&nbsp;</i>Property Image</p>"),
                        Field('propertyImage')),
                    Div(HTML("<p class='small pt-2'><i class='far fa-file-pdf'></i>&nbsp;&nbsp;</i>Auto Valuation</p>"),
                        Field('valuationDocument')),
                    Div(HTML("<p class='small pt-2'><i class='far fa-file-pdf'></i>&nbsp;&nbsp;</i>TitleDocument</p>"),
                        Field('titleDocument')),
                    Div(HTML("<p class='small pt-2'><i class='fas fa-funnel-dollar'></i>&nbsp;</i>Sales Channel</p>"),
                        Field('salesChannel')),
                    css_class="col-lg-6"),
                css_class="row")
        ))

    def clean(self):
        loanType = self.cleaned_data['loanType']

        if not self.errors:
            if loanType == loanTypesEnum.SINGLE_BORROWER.value:
                if self.cleaned_data['birthdate_1'] == None and self.cleaned_data['age_1'] == None:
                    raise forms.ValidationError("Enter age or birthdate for Borrower")

            if loanType == loanTypesEnum.JOINT_BORROWER.value:
                if self.cleaned_data['birthdate_1'] == None and self.cleaned_data['age_1'] == None:
                    raise forms.ValidationError("Enter age or birthdate for Borrower 1")
                if self.cleaned_data['birthdate_2'] == None and self.cleaned_data['age_2'] == None:
                    raise forms.ValidationError("Enter age or birthdate for Borrower 2")

            if self.cleaned_data['postcode'] != None:
                if self.cleaned_data['dwellingType'] == None:
                    raise forms.ValidationError("Enter property type")
                if self.cleaned_data['valuation'] == None:
                    raise forms.ValidationError("Enter property valuation estimate")


class LossDetailsForm(forms.ModelForm):
    # Form Data

    class Meta:
        model = LossData
        fields = ['lossNotes', 'lossDate', 'ragStatus', 'purposeTopUp',
                  'followUp','followUpDate','followUpNotes',
                  'purposeRefi', 'purposeLive', 'purposeGive', 'purposeCare']

        widgets = {
            'lossNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
            'followUpNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),

        }

    ragTypes = (
        (ragTypesEnum.GREEN.value, 'GREEN'),
        (ragTypesEnum.AMBER.value, 'AMBER'),
        (ragTypesEnum.RED.value, 'RED'),
    )

    ragStatus = forms.TypedChoiceField(choices=ragTypes, coerce=int)

    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                HTML("<i class='fas fa-user-times'></i>&nbsp;&nbsp;<small>Loss Notes</small>"),
                Div(
                    Div(Field('ragStatus', placeholder='RAG')),
                    Div(Field('lossDate', placeholder='Loss Date')),
                    Div(Field('lossNotes', placeholder='Loss Notes'))),
                css_class="col-lg-4"),

            Div(
                HTML("<i class='fas fa-user-tag'></i>&nbsp;&nbsp;<small>Follow-up Required</small>"),
                Div(
                    Div(Field('followUp', placeholder='Follow Up?')),
                    Div(Field('followUpDate', placeholder='Follow Up Date')),
                    Div(Field('followUpNotes', placeholder='Follow Up Notes')),
                ),
                css_class="col-lg-4"),
            Div(
                HTML("<i class='fas fa-user-edit'></i>&nbsp;&nbsp;<small>Intended Purposes</small>"),
                Div(
                    Div(Field('purposeTopUp'), css_class="col-lg-2"),
                    Div(HTML("<p>Top-up</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Field('purposeRefi'), css_class="col-lg-2"),
                    Div(HTML("<p>Refinance</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Field('purposeLive'), css_class="col-lg-2"),
                    Div(HTML("<p>Live</p>"), css_class="col-lg-4 pt-1 pl-0 "),
                    css_class='row'),
                Div(
                    Div(Field('purposeGive'), css_class="col-lg-2"),
                    Div(HTML("<p>Give</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Field('purposeCare'), css_class="col-lg-2"),
                    Div(HTML("<p>Care</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Submit('submit', 'Update ', css_class='btn btn-warning')),
                    css_class="col-lg-4 text-left"),
                css_class="col-lg-4"),
            css_class='row')
    )


class SFPasswordForm(forms.Form):
    # Form Data

    password = forms.CharField(required=True, widget=forms.PasswordInput)

    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-8'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Field('password', placeholder='Salesforce API Password')),
            Div(
                Div(Submit('submit', 'Create ', css_class='btn btn-warning')),
            ),
        ))


class SolicitorForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['specialConditions']

    # Form Data
    password = forms.CharField(required=True, widget=forms.PasswordInput)
    specialConditions = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 6, 'cols': 100}))

    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-10'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Field('specialConditions', placeholder='Enter any special conditions'),
                Field('password', placeholder='Salesforce API Password')),
            Div(
                Div(Submit('submit', 'Create ', css_class='btn btn-warning')),
            ),
        ))


class ValuerForm(forms.ModelForm):
    class Meta:
        model = Case
        fields =['valuerFirm', 'valuerEmail', 'valuerContact']

    # Form Data
    password = forms.CharField(required=True, widget=forms.PasswordInput)
    valuerContact = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 6, 'cols': 100}))

    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-10'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Field('valuerFirm', placeholder='Firm Name'),
                Field('valuerEmail', placeholder='Valuer Email'),
                Field('valuerContact', placeholder='Specific Client Contact Details'),

                Field('password', placeholder='Salesforce API Password')),
            Div(
                Div(Submit('submit', 'Create ', css_class='btn btn-warning')),
            ),
        ))
