# Django Imports
from django import forms
from django.forms import ValidationError
from datetime import datetime
from django.contrib.auth.models import User

from django.forms import widgets

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML

# Local Application Imports
from apps.enquiry.models import Enquiry
from apps.lib.site_Enums import loanTypesEnum, caseStagesEnum
from apps.case.models import Case


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'postcode',
                  'email', 'phoneNumber', 'enquiryNotes']

    enquiryNotes = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 9, 'cols': 50}))
    name = forms.CharField(required=True)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False  # Hide default error messages
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Client Details"), css_class='form-header'),
                Div(
                    Div(HTML("Client Name"), css_class='form-label'),
                    Div(Field('name'))),
                Div(
                    Div(HTML("Client Phone Number"), css_class='form-label'),
                    Div(Field('phoneNumber'))),
                Div(
                    Div(HTML("Client Email"), css_class='form-label'),
                    Div(Field('email'))),
                Div(
                    Div(HTML("Enquiry Notes"), css_class='form-label'),
                    Div(Field('enquiryNotes'))),
                css_class='col-lg-6'),

            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header'),
                Div(
                    Div(HTML("Single or Joint Home Owners"), css_class='form-label'),
                    Div(Field('loanType'))),
                Div(
                    Div(HTML("Age - Home Owner 1"), css_class='form-label'),
                    Div(Field('age_1'))),
                Div(
                    Div(HTML("Age - Home Owner 2"), css_class='form-label'),
                    Div(Field('age_2'))),

                Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;Home Details"), css_class='form-header'),
                Div(
                    Div(HTML("Dwelling Type"), css_class='form-label'),
                    Div(Field('dwellingType'))),
                Div(
                    Div(HTML("Postcode"), css_class='form-label'),
                    Div(Field('postcode'))),

                Div(css_class="row"),
                Div(Div(Submit('submit', 'Update', css_class='btn btn-warning')), css_class='text-right'),
                Div(HTML("<br>")),
                css_class='col-lg-6'),
            css_class="row ")
    )

    def clean(self):
        if self.cleaned_data['loanType'] == loanTypesEnum.SINGLE_BORROWER.value and self.cleaned_data['age_2']:
            raise ValidationError("Please check - is this a single or Joint Loan? ")

        if self.cleaned_data['loanType'] == loanTypesEnum.JOINT_BORROWER.value and not self.cleaned_data['age_2']:
            raise ValidationError("Please add second borrower age ")

        return self.cleaned_data



class CaseDetailsForm(forms.ModelForm):

    valuation = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    mortgageDebt = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    superAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    pensionAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())

    class Meta:
        model = Case
        fields = ['caseDescription', 'adviser', 'caseNotes', 'loanType',
                  'clientType1', 'surname_1', 'firstname_1', 'preferredName_1','birthdate_1', 'age_1', 'sex_1',
                  'salutation_1','middlename_1','maritalStatus_1',
                  'clientType2', 'surname_2', 'firstname_2', 'preferredName_2','birthdate_2', 'age_2', 'sex_2',
                  'salutation_2', 'middlename_2', 'maritalStatus_2',
                  'street', 'suburb', 'postcode', 'valuation', 'dwellingType', 'mortgageDebt',
                  'superFund', 'state',
                  'superAmount', 'pensionType', 'pensionAmount', 'phoneNumber', 'email']
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
                    Div(Div(HTML("Birthdate*"), css_class='form-label'),
                        Div(Field('birthdate_1'))),
                    Div(Div(HTML("Age"), css_class='form-label'),
                        Div(Field('age_1'))),
                    Div(Div(HTML("Surname*"), css_class='form-label'),
                        Div(Field('surname_1'))),
                    Div(Div(HTML("Preferred Name"), css_class='form-label'),
                        Div(Field('preferredName_1'))),
                    Div(Div(HTML("Firstname*"), css_class='form-label'),
                        Div(Field('firstname_1'))),
                    Div(Div(HTML("Middlename"), css_class='form-label'),
                        Div(Field('middlename_1'))),
                    Div(Div(HTML("Salutation*"), css_class='form-label'),
                        Div(Field('salutation_1'))),
                    Div(Div(HTML("Gender*"), css_class='form-label'),
                        Div(Field('sex_1'))),
                    Div(Div(HTML("Borrower Role*"), css_class='form-label'),
                        Div(Field('clientType1'))),
                    Div(Div(HTML("Marital Status*"), css_class='form-label'),
                        Div(Field('maritalStatus_1'))),
                    HTML("<i class='far fa-user'></i>&nbsp;&nbsp;<small>Borrower 2</small>"),
                    Div(Div(HTML("Birthdate*"), css_class='form-label'),
                        Div(Field('birthdate_2'))),
                    Div(Div(HTML("Age"), css_class='form-label'),
                        Div(Field('age_2'))),
                    Div(Div(HTML("Surname*"), css_class='form-label'),
                        Div(Field('surname_2'))),
                    Div(Div(HTML("Preferred Name"), css_class='form-label'),
                        Div(Field('preferredName_2'))),
                    Div(Div(HTML("Firstname*"), css_class='form-label'),
                        Div(Field('firstname_2'))),
                    Div(Div(HTML("Middlename"), css_class='form-label'),
                        Div(Field('middlename_2'))),
                    Div(Div(HTML("Salutation*"), css_class='form-label'),
                        Div(Field('salutation_2'))),
                    Div(Div(HTML("Gender*"), css_class='form-label'),
                        Div(Field('sex_2'))),
                    Div(Div(HTML("Borrower Role*"), css_class='form-label'),
                        Div(Field('clientType2'))),
                    Div(Div(HTML("Marital Status*"), css_class='form-label'),
                        Div(Field('maritalStatus_2'))),
                    css_class="col-lg-6"),

                Div(
                    Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;Property"), css_class='form-header'),
                    Div(Div(HTML("Postcode*"), css_class='form-label'),
                        Div(Field('postcode'))),
                    Div(Div(HTML("Dwelling Type*"), css_class='form-label'),
                        Div(Field('dwellingType'))),
                    Div(Div(HTML("Street Address*"), css_class='form-label'),
                        Div(Field('street'))),
                    Div(Div(HTML("Suburb*"), css_class='form-label'),
                        Div(Field('suburb'))),
                    Div(Div(HTML("State*"), css_class='form-label'),
                        Div(Field('state'))),
                    Div(Div(HTML("Valuation*"), css_class='form-label'),
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


