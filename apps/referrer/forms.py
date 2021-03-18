# Django Imports
from django import forms
from django.forms import ValidationError
from datetime import datetime
from django.contrib.auth.models import User

from django.forms import widgets

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Row, Column

# Local Application Imports
from apps.enquiry.models import Enquiry
from apps.lib.site_Enums import loanTypesEnum, caseStagesEnum
from apps.case.models import Case


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['loanType', 'firstname', 'lastname', 'age_1', 'age_2', 'dwellingType', 'postcode',
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
                    Div(HTML("First Name"), css_class='form-label'),
                    Div(Field('firstname'))
                ),
                Div(
                    Div(HTML("Last Name"), css_class='form-label'),
                    Div(Field('lastname'))
                ),
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
                  'salutation_1','middlename_1','maritalStatus_1', 'referralRepNo',
                  'clientType2', 'surname_2', 'firstname_2', 'preferredName_2','birthdate_2', 'age_2', 'sex_2',
                  'salutation_2', 'middlename_2', 'maritalStatus_2',
                  'street', 'suburb', 'postcode', 'valuation', 'dwellingType', 'mortgageDebt',
                   'state',
                   'phoneNumber', 'email']
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
            Div(HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;Lead Notes"), css_class='form-header'),
            Div(
                Div(
                    Div(HTML("Lead Description"), css_class='form-label'),
                    Div(Field('caseDescription')), css_class="col-lg-6"),
                Div(
                    Div(Submit('submit', 'Update Lead ', css_class='btn btn-outline-secondary')),
                    css_class="col-lg-4 text-left"),
                Div(css_class="col-lg-6"),
                css_class="row align-items-center"),
            Div(
                Div(HTML("Lead Notes"), css_class='form-label'),
                Div(Field('caseNotes'))),
            Div(
                Div(Div(HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;Contact Details"),
                        css_class='form-header'),
                    Div(Div(HTML("Client Phone Number"), css_class='form-label'),
                        Div(Field('phoneNumber'))),
                    Div(Div(HTML("Client Email"), css_class='form-label'),
                        Div(Field('email'))),
                    HTML("<br>"),
                    Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header'),
                    Div(Div(HTML("Single or Joint Borrowers"), css_class='form-label'),
                        Div(Field('loanType'))),
                    HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Borrower 1</small>"),
                    Row(
                        Column(Div(Div(HTML("Birthdate*"), css_class='form-label'),
                                   Div(Field('birthdate_1'))), css_class='col-6'),
                        Column(Div(Div(HTML("Age"), css_class='form-label'),
                                   Div(Field('age_1'))), css_class='col-6')),
                    Div(Div(HTML("Firstname*"), css_class='form-label'),
                        Div(Field('firstname_1'))),
                    Row(
                        Column(Div(Div(HTML("Preferred Name*"), css_class='form-label pt-1'),
                                   Div(Field('preferredName_1'))), css_class='col-6'),
                        Column(Div(Div(HTML("Middlename"), css_class='form-label pt-1'),
                                   Div(Field('middlename_1'))), css_class='col-6')),
                    Div(Div(HTML("Surname*"), css_class='form-label'),
                        Div(Field('surname_1'))),
                    Row(
                        Column(Div(Div(HTML("Salutation*"), css_class='form-label pt-1'),
                                   Div(Field('salutation_1'))), css_class='col-6'),
                        Column(Div(Div(HTML("Gender"), css_class='form-label pt-1'),
                                   Div(Field('sex_1'))), css_class='col-6')),
                    Div(Div(HTML("Borrower Role*"), css_class='form-label'),
                        Div(Field('clientType1'))),
                    Div(Div(HTML("Marital Status*"), css_class='form-label'),
                        Div(Field('maritalStatus_1'))),
                    HTML("<i class='far fa-user'></i>&nbsp;&nbsp;<small>Borrower 2</small>"),
                    Row(
                        Column(Div(Div(HTML("Birthdate*"), css_class='form-label pt-1'),
                                   Div(Field('birthdate_2'))), css_class='col-6'),
                        Column(Div(Div(HTML("Age"), css_class='form-label pt-1'),
                                   Div(Field('age_2'))), css_class='col-6')),
                    Div(Div(HTML("Firstname*"), css_class='form-label'),
                        Div(Field('firstname_2'))),
                    Row(
                        Column(Div(Div(HTML("Preferred Name*"), css_class='form-label pt-1'),
                                   Div(Field('preferredName_2'))), css_class='col-6'),
                        Column(Div(Div(HTML("Middlename"), css_class='form-label pt-1'),
                                   Div(Field('middlename_2'))), css_class='col-6')),
                    Div(Div(HTML("Surname*"), css_class='form-label'),
                        Div(Field('surname_2'))),
                    Row(
                        Column(Div(Div(HTML("Salutation*"), css_class='form-label'),
                                   Div(Field('salutation_2'))), css_class='col-6'),
                        Column(Div(Div(HTML("Gender"), css_class='form-label'),
                                   Div(Field('sex_2'))), css_class='col-6')),
                    Div(Div(HTML("Borrower Role*"), css_class='form-label'),
                        Div(Field('clientType2'))),
                    Div(Div(HTML("Marital Status*"), css_class='form-label'),
                        Div(Field('maritalStatus_2'))),
                    css_class="col-lg-6"),



                Div(
                    Div(HTML("<i class='far fa-handshake'></i>&nbsp;&nbsp;Broker"), css_class='form-header'),
                    Div(Div(HTML("Broker Name*"), css_class='form-label'),
                        Div(Field('adviser'))),
                    Div(Div(HTML("Credit Rep Number*"), css_class='form-label'),
                        Div(Field('referralRepNo'))),
                    HTML("<br>"),
                    Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;Property"), css_class='form-header pt-2'),
                    Div(Div(HTML("Dwelling Type*"), css_class='form-label'),
                        Div(Field('dwellingType'))),
                    Div(Div(HTML("Street Address*"), css_class='form-label'),
                        Div(Field('street', readonly=True))),
                    Div(Div(HTML("Unit / Apartment / Lot"), css_class='form-label'),
                        Div(Field('base_specificity', readonly=True))),
                    Div(Div(HTML("Street Number"), css_class='form-label'),
                        Div(Field('street_number', readonly=True))),
                    Div(Div(HTML("Street Name"), css_class='form-label'),
                        Div(Field('street_name', readonly=True))),
                    Div(Div(HTML("Street Type e.g Avenue, Lane, etc"), css_class='form-label'),
                        Div(Field('street_type', readonly=True))),
                    Div(Div(HTML("Suburb*"), css_class='form-label'),
                        Div(Field('suburb'))),
                    Row(
                        Column(Div(Div(HTML("State*"), css_class='form-label'),
                                   Div(Field('state'))), css_class='col-6'),
                        Column(Div(Div(HTML("Postcode"), css_class='form-label'),
                                   Div(Field('postcode'))), css_class='col-6')),
                    Div(Div(HTML("Valuation*"), css_class='form-label'),
                        Div(Field('valuation'))),
                    Div(Div(HTML("Mortgage Debt"), css_class='form-label'),
                        Div(Field('mortgageDebt'))),
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

            if self.cleaned_data['adviser'] == None:
                raise forms.ValidationError("Enter broker name")

            if not self.cleaned_data['referralRepNo']:
                raise forms.ValidationError("Enter broker Credit Rep  Number")



