#Python Imports
from datetime import datetime

#Django Imports
from django import forms
from django.forms import widgets

#Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML


#Local Application Imports
from apps.lib.enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum, pensionTypesEnum, \
    loanTypesEnum, ragTypesEnum
from .models import Case, LossData


class CaseDetailsForm(forms.ModelForm):
    #A model form with some overriding using form fields for rendering purposes
    #Additional HTML rendering in the form

    valuation = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    mortgageDebt = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    superAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    pensionAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    propertyImage = forms.ImageField(required=False, widget=forms.FileInput)

    class Meta:
        model = Case
        fields = ['caseDescription', 'adviser', 'caseNotes', 'loanType', 'caseType',
                  'clientType1', 'surname_1', 'firstname_1', 'birthdate_1', 'age_1', 'sex_1',
                  'clientType2', 'surname_2', 'firstname_2', 'birthdate_2', 'age_2', 'sex_2',
                  'street', 'postcode', 'valuation', 'dwellingType', 'propertyImage', 'mortgageDebt', 'superFund',
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
                    Field('valuation', placeholder='Valuation'),
                    Field('mortgageDebt', placeholder='Existing Mortgage'),
                    HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;<small>Super/Investments</small>"),
                    Field('superFund', placeholder='Super Fund'),
                    Field('superAmount', placeholder='Super Amount'),
                    HTML("<i class='fas fa-hand-holding-usd'></i>&nbsp;&nbsp;<small>Pension</small>"),
                    Field('pensionAmount', placeholder='Pension Amount (per fortnight)'),
                    Field('pensionType', placeholder='Pension Type'),
                    Div(HTML("<p class='small'><i class='fa fa-camera fa-fw'>&nbsp;&nbsp;</i>Property Image</p>"),
                        Field('propertyImage')),
                    Div(HTML("<p class='small'><i class='fas fa-funnel-dollar'></i>&nbsp;</i>Sales Channel</p>"),
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
        fields = ['lossNotes', 'lossDate', 'ragStatus', 'clientNeed', 'purposeTopUp',
                  'purposeRefi', 'purposeLive', 'purposeGive', 'purposeCare']

        widgets = {
            'lossNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
            'clientNeed': forms.Textarea(attrs={'rows': 5, 'cols': 100})

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
                HTML("<i class='fas fa-user-tag'></i>&nbsp;&nbsp;<small>Additional Client Notes</small>"),
                Div(
                    Div(Field('clientNeed', placeholder='Client need (own words)'))),
                css_class="col-lg-4"),
            Div(
                HTML("<i class='fas fa-user-edit'></i>&nbsp;&nbsp;<small>Intended Purposes</small>"),
                Div(
                    Div(Field('purposeTopUp'), css_class="col-lg-2"),
                    Div(HTML("<p class='small'>Top-up</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Field('purposeRefi'), css_class="col-lg-2"),
                    Div(HTML("<p class='small'>Refinance</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Field('purposeLive'), css_class="col-lg-2"),
                    Div(HTML("<p class='small'>Live</p>"), css_class="col-lg-4 pt-1 pl-0 "),
                    css_class='row'),
                Div(
                    Div(Field('purposeGive'), css_class="col-lg-2"),
                    Div(HTML("<p class='small'>Give</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Field('purposeCare'), css_class="col-lg-2"),
                    Div(HTML("<p class='small'>Care</p>"), css_class="col-lg-4 pt-1 pl-0"),
                    css_class='row'),
                Div(
                    Div(Submit('submit', 'Close Case ', css_class='btn btn-warning')),
                    css_class="col-lg-4 text-left"),
                css_class="col-lg-4"),
            css_class='row')
    )
