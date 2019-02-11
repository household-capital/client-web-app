from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML
from crispy_forms.bootstrap import (
    PrependedText, PrependedAppendedText, FormActions)
from datetime import datetime

from django import forms
from django.forms import widgets

from .models import Case



class CaseDetailsForm(forms.ModelForm):
    #Form Data

    valuation = forms.IntegerField(required=True, localize=True, widget=widgets.TextInput())
    mortgageDebt = forms.IntegerField(required=True, localize=True, widget=widgets.TextInput())
    superAmount = forms.IntegerField(required=True, localize=True, widget=widgets.TextInput())
    pensionAmount = forms.IntegerField(required=True, localize=True, widget=widgets.TextInput())

    class Meta:
        model = Case
        fields = ['caseDescription', 'adviser', 'caseNotes', 'loanType','caseType',
                  'clientType1','surname_1','firstname_1','birthdate_1','age_1','sex_1',
                  'clientType2','surname_2','firstname_2','birthdate_2','age_2','sex_2',
                  'street','postcode','valuation','dwellingType','mortgageDebt','superName',
                  'superAmount','pensionType', 'pensionAmount']
        widgets = {
            'caseNotes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
        }

    #Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
                        Div (
                            HTML("<i class='far fa-address-card'></i>&nbsp;&nbsp;<small>Case Notes</small>"),
                            Div(
                                Div(Field('caseDescription', placeholder='Description'),css_class="col-lg-4"),
                                Div(
                                    Div(Submit('submit', 'Update Case', css_class='btn btn-warning')),
                                         css_class="col-lg-4 text-left"),
                                Div(css_class="col-lg-4"),
                                css_class="row "),
                            Div(
                                Div(Field('adviser', placeholder='Adviser'), css_class="col-lg-4"),
                                Div(Field('caseType', placeholder='Case Status'), css_class="col-lg-4"),
                                css_class="row"),
                            Div(Field('caseNotes', placeholder='Case Notes')),
                            Div(
                                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Loan Type</small>"),
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
                                    css_class="col-lg-4"),
                                Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;<small>Property</small>"),
                                    Field('postcode', placeholder='Postcode'),
                                    Field('dwellingType', placeholder='Dwelling Type'),
                                    Field('street', placeholder='Street Address'),
                                    Field('valuation', placeholder='Valuation'),
                                    Field('mortgageDebt', placeholder='Existing Mortgage'),
                                    css_class="col-lg-4"),
                                Div(HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;<small>Super/Investments</small>"),
                                    Field('superName', placeholder='Super Name'),
                                    Field('superAmount', placeholder='Super Amount'),
                                    HTML("<br>"),
                                    HTML("<i class='fas fa-hand-holding-usd'></i>&nbsp;&nbsp;<small>Pension</small>"),
                                    Field('pensionAmount', placeholder='Pension Amount (per fortnight)'),
                                    Field('pensionType', placeholder='Pension Type'),
                                    css_class="col-lg-4"),
                                css_class="row")
                            ))


    def clean(self):
        loanType=self.cleaned_data['loanType']

        if loanType==0:
            if self.cleaned_data['birthdate_1']==None and self.cleaned_data['age_1']==None:
                raise forms.ValidationError("Enter age or birthdate for Borrower")

        if loanType==1:
            if self.cleaned_data['birthdate_1']==None and self.cleaned_data['age_1']==None:
                raise forms.ValidationError("Enter age or birthdate for Borrower 1")
            if self.cleaned_data['birthdate_2']==None and self.cleaned_data['age_2']==None:
                raise forms.ValidationError("Enter age or birthdate for Borrower 2")

        if self.cleaned_data['postcode']!=None:
            if self.cleaned_data['dwellingType'] == None:
                raise forms.ValidationError("Enter property type")
            if self.cleaned_data['valuation'] == None:
                raise forms.ValidationError("Enter property valuation estimate")

