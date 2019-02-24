from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML
from crispy_forms.bootstrap import (PrependedText, InlineCheckboxes,PrependedAppendedText, FormActions, InlineRadios)

from apps.lib.enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,pensionTypesEnum, loanTypesEnum

from django.core.exceptions import ValidationError
from django import forms
from django.forms import widgets

from .models import WebCalculator


class WebInputForm(forms.ModelForm):

    class Meta:
        model = WebCalculator
        fields = ['loanType', 'name','age_1', 'age_2', 'dwellingType','valuation', 'postcode']

    relationship=((loanTypesEnum.JOINT_BORROWER.value,'Couple'),(loanTypesEnum.SINGLE_BORROWER.value,'Single'))
    dwelling=((dwellingTypesEnum.HOUSE.value,'House'),(dwellingTypesEnum.APARTMENT.value,'Apartment'))

    loanType = forms.TypedChoiceField(choices=relationship, coerce=int, initial=loanTypesEnum.JOINT_BORROWER.value)
    dwellingType = forms.TypedChoiceField(choices=dwelling, coerce=int, initial=dwellingTypesEnum.HOUSE.value)
    name=forms.CharField(max_length=30, required=False)

    valuation = forms.CharField(required=True, localize=True,label='Estimated Value')

    def clean_valuation(self):
        try:
            valuation=self.cleaned_data['valuation']
            valuation=valuation.replace('$',"")
            valuation = valuation.replace(',', "")
            valuation=int(valuation)
            return valuation
        except:
            raise ValidationError("Please enter valuation amount")


class WebOutputForm(forms.ModelForm):

    class Meta:
        model = WebCalculator
        fields = ['email', 'isRefi','isTopUp', 'isLive', 'isGive','isCare']

    isRefi=forms.BooleanField(widget=forms.CheckboxInput(),required=False)
    isTopUp=forms.BooleanField(widget=forms.CheckboxInput(),required=False)
    isLive=forms.BooleanField(widget=forms.CheckboxInput(),required=False)
    isGive=forms.BooleanField(widget=forms.CheckboxInput(),required=False)
    isCare=forms.BooleanField(widget=forms.CheckboxInput(),required=False)



