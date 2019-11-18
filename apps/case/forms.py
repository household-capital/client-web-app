# Python Imports
from datetime import datetime

# Django Imports
from django import forms
from django.forms import widgets

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML

# Local Application Imports
from apps.lib.site_Enums import loanTypesEnum, caseTypesEnum
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
                  'salutation_1','middlename_1','maritalStatus_1',
                  'clientType2', 'surname_2', 'firstname_2', 'birthdate_2', 'age_2', 'sex_2',
                  'salutation_2', 'middlename_2', 'maritalStatus_2',
                  'street', 'suburb', 'postcode', 'valuation', 'dwellingType', 'propertyImage', 'mortgageDebt',
                  'superFund', 'valuationDocument', 'state', 'titleDocument',
                  'superAmount', 'pensionType', 'pensionAmount', 'salesChannel', 'phoneNumber', 'email']
        widgets = {
            'caseNotes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
        }

    caseTypes=(
                  (caseTypesEnum.DISCOVERY.value,"Discovery"),
                  (caseTypesEnum.MEETING_HELD.value, "Meeting Held"),
                  (caseTypesEnum.APPLICATION.value, "Application"),
                  (caseTypesEnum.DOCUMENTATION.value, "Documentation"),
                  (caseTypesEnum.FUNDED.value, "Funded"),
                  (caseTypesEnum.CLOSED.value, "Closed"),

    )


    caseType = forms.TypedChoiceField(choices=caseTypes, coerce=int, initial=caseTypesEnum.DISCOVERY.value)


    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;Case Notes"), css_class='form-header'),
            Div(
                Div(
                    Div(HTML("Case Description"), css_class='form-label'),
                    Div(Field('caseDescription')), css_class="col-lg-6"),
                Div(
                    Div(Submit('submit', 'Update Case ', css_class='btn btn-outline-secondary')),
                    css_class="col-lg-4 text-left"),
                Div(css_class="col-lg-6"),
                css_class="row align-items-center"),
            Div(
                Div(
                    Div(HTML("Channel"), css_class='form-label'),
                    Div(Field('salesChannel')), css_class="col-lg-6"),
                Div(
                    Div(HTML("Current Status"), css_class='form-label'),
                    Div(Field('caseType')), css_class="col-lg-6"),
                css_class="row"),

            Div(
                Div(HTML("Case Notes"), css_class='form-label'),
                Div(Field('caseNotes'))),
            Div(
                Div(Div(HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;Contact Details"),
                        css_class='form-header'),
                    Div(Div(HTML("Client Phone Number"), css_class='form-label'),
                        Div(Field('phoneNumber'))),
                    Div(Div(HTML("Client Email"), css_class='form-label'),
                        Div(Field('email'))),
                    Div(Div(HTML("Introducer or Advisor"), css_class='form-label'),
                        Div(Field('adviser'))),
                    HTML("<br>"),
                    Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header'),
                    Div(Div(HTML("Single or Joint Borrowers"), css_class='form-label'),
                        Div(Field('loanType'))),
                    HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Borrower 1</small>"),
                    Div(Div(HTML("Birthdate"), css_class='form-label'),
                        Div(Field('birthdate_1'))),
                    Div(Div(HTML("Age"), css_class='form-label'),
                        Div(Field('age_1'))),
                    Div(Div(HTML("Surname"), css_class='form-label'),
                        Div(Field('surname_1'))),
                    Div(Div(HTML("Firstname"), css_class='form-label'),
                        Div(Field('firstname_1'))),
                    Div(Div(HTML("Middlename"), css_class='form-label'),
                        Div(Field('middlename_1'))),
                    Div(Div(HTML("Salutation"), css_class='form-label'),
                        Div(Field('salutation_1'))),
                    Div(Div(HTML("Gender"), css_class='form-label'),
                        Div(Field('sex_1'))),
                    Div(Div(HTML("Borrower Role"), css_class='form-label'),
                        Div(Field('clientType1'))),
                    Div(Div(HTML("Marital Status"), css_class='form-label'),
                        Div(Field('maritalStatus_1'))),
                    HTML("<i class='far fa-user'></i>&nbsp;&nbsp;<small>Borrower 2</small>"),
                    Div(Div(HTML("Birthdate"), css_class='form-label'),
                        Div(Field('birthdate_2'))),
                    Div(Div(HTML("Age"), css_class='form-label'),
                        Div(Field('age_2'))),
                    Div(Div(HTML("Surname"), css_class='form-label'),
                        Div(Field('surname_2'))),
                    Div(Div(HTML("Firstname"), css_class='form-label'),
                        Div(Field('firstname_2'))),
                    Div(Div(HTML("Middlename"), css_class='form-label'),
                        Div(Field('middlename_2'))),
                    Div(Div(HTML("Salutation"), css_class='form-label'),
                        Div(Field('salutation_2'))),
                    Div(Div(HTML("Gender"), css_class='form-label'),
                        Div(Field('sex_2'))),
                    Div(Div(HTML("Borrower Role"), css_class='form-label'),
                        Div(Field('clientType2'))),
                    Div(Div(HTML("Marital Status"), css_class='form-label'),
                        Div(Field('maritalStatus_2'))),
                    css_class="col-lg-6"),

                Div(
                    Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;Property"), css_class='form-header'),
                    Div(Div(HTML("Postcode"), css_class='form-label'),
                        Div(Field('postcode'))),
                    Div(Div(HTML("Dwelling Type"), css_class='form-label'),
                        Div(Field('dwellingType'))),
                    Div(Div(HTML("Street Address"), css_class='form-label'),
                        Div(Field('street'))),
                    Div(Div(HTML("Suburb"), css_class='form-label'),
                        Div(Field('suburb'))),
                    Div(Div(HTML("State"), css_class='form-label'),
                        Div(Field('state'))),
                    Div(Div(HTML("Valuation"), css_class='form-label'),
                        Div(Field('valuation'))),
                    Div(Div(HTML("Mortgage Debt"), css_class='form-label'),
                        Div(Field('mortgageDebt'))),

                    Div(HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;Super/Investments"),
                        css_class='form-header'),
                    Div(Div(HTML("Super or Investment Fund"), css_class='form-label'),
                        Div(Field('superFund'))),
                    Div(Div(HTML("Super Fund Assets"), css_class='form-label'),
                        Div(Field('superAmount'))),
                    Div(HTML("<i class='fas fa-hand-holding-usd'></i>&nbsp;&nbsp;Pension"), css_class='form-header'),
                    Div(Div(HTML("Pension Amount"), css_class='form-label'),
                        Div(Field('pensionAmount'))),
                    Div(Div(HTML("Pension Status"), css_class='form-label'),
                        Div(Field('pensionType'))),
                    Div(HTML("<p class='small pt-2'><i class='fa fa-camera fa-fw'>&nbsp;&nbsp;</i>Property Image</p>"),
                        Field('propertyImage')),
                    Div(HTML("<p class='small pt-2'><i class='far fa-file-pdf'></i>&nbsp;&nbsp;</i>Auto Valuation</p>"),
                        Field('valuationDocument')),
                    Div(HTML("<p class='small pt-2'><i class='far fa-file-pdf'></i>&nbsp;&nbsp;</i>TitleDocument</p>"),
                        Field('titleDocument')),
                    css_class="col-lg-6"),
                css_class="row")
        ))

    def clean(self):
        loanType = self.cleaned_data['loanType']

        if not self.errors:
            if loanType == loanTypesEnum.SINGLE_BORROWER.value:
                if self.cleaned_data['birthdate_1'] == None and self.cleaned_data['age_1'] == None:
                    raise forms.ValidationError("Please enter age or birthdate for Borrower")

            if loanType == loanTypesEnum.JOINT_BORROWER.value:
                if self.cleaned_data['birthdate_1'] == None and self.cleaned_data['age_1'] == None:
                    raise forms.ValidationError("Please nter age or birthdate for Borrower 1")
                if self.cleaned_data['birthdate_2'] == None and self.cleaned_data['age_2'] == None:
                    raise forms.ValidationError("Please enter age or birthdate for Borrower 2")

            if self.cleaned_data['postcode'] != None:
                if self.cleaned_data['dwellingType'] == None:
                    raise forms.ValidationError("Enter property type")
                if self.cleaned_data['valuation'] == None:
                    raise forms.ValidationError("Please enter property valuation estimate")

            if self.cleaned_data['salesChannel'] == None:
                raise forms.ValidationError("Please enter a sales channel")


class LossDetailsForm(forms.ModelForm):
    # Form Data

    class Meta:
        model = LossData
        fields = ['closeReason',
                  'followUpDate', 'followUpNotes',
                  'doNotMarket'
                  ]

        widgets = {
            'lossNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
            'followUpNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),

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
            Div(
                HTML("<i class='fas fa-user-times'></i>&nbsp;&nbsp;<small>Loss Notes</small>"),
                Div(
                    Div(Div(HTML("Close Reason"), css_class='form-label'),
                        Div(Field('closeReason'))),
                    Div(Div(HTML("<br>"))),
                    Div(HTML("<i class='far fa-envelope pb-2'></i></i>&nbsp;&nbsp;<small>Marketing</small>")),
                    Div(
                        Div(Field('doNotMarket'), css_class="col-lg-2"),
                        Div(HTML("<p>Do Not Market</p>"), css_class="col-lg-5 pt-1 pl-0 "),
                        css_class="row "),
                ),
                css_class="col-lg-4"),

            Div(
                HTML("<i class='fas fa-user-tag'></i>&nbsp;&nbsp;<small>Follow-up Required</small>"),
                Div(
                    Div(Div(HTML("Follow-up Date"), css_class='form-label'),
                        Div(Field('followUpDate'))),
                    Div(Div(HTML("Follow-up Notes"), css_class='form-label'),
                        Div(Field('followUpNotes'))),
                ),
                css_class="col-lg-4"),

            css_class='row'),
        Div(

            Div(Div(Div(Submit('submit', 'Update', css_class='btn btn-warning')), css_class='col-lg-8 text-right'),css_class='row'),
        ))


class SFPasswordForm(forms.Form):
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
                Div(Submit('submit', 'Create ', css_class='btn btn-warning')),
            ),
        ))


class SolicitorForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['specialConditions']

    # Form Data
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
                Field('specialConditions', placeholder='Enter any special conditions')),
            Div(
                Div(Submit('submit', 'Create ', css_class='btn btn-warning')),
            ),
        ))


class ValuerForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['valuerFirm', 'valuerEmail', 'valuerContact']

    # Form Data
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
                Field('valuerContact', placeholder='Specific Client Contact Details')),

            Div(
                Div(Submit('submit', 'Create ', css_class='btn btn-warning')),
            ),
        ))

    def clean(self):
        if self.cleaned_data['valuerFirm'] and self.cleaned_data['valuerEmail']:
            return
        else:
            raise forms.ValidationError("Please choose a valuer and corresponding email")
