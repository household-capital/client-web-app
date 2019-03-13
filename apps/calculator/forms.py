#Django Imports
from django.core.exceptions import ValidationError
from django import forms

#Local Application Imports
from apps.lib.enums import dwellingTypesEnum , loanTypesEnum
from .models import WebCalculator



class WebInputForm(forms.ModelForm):
    #A model form with some overriding using form fields to enable choice field enumeration
    #and to enable valuation to be initially validated as a text field

    class Meta:
        model = WebCalculator
        fields = ['loanType', 'name','age_1', 'age_2', 'dwellingType','valuation', 'postcode','referrer']

    relationship=((loanTypesEnum.JOINT_BORROWER.value,'Couple'),(loanTypesEnum.SINGLE_BORROWER.value,'Single'))
    dwelling=((dwellingTypesEnum.HOUSE.value,'House'),(dwellingTypesEnum.APARTMENT.value,'Apartment'))

    dwellingType = forms.TypedChoiceField(choices=dwelling, coerce=int, initial=dwellingTypesEnum.HOUSE.value)
    loanType = forms.TypedChoiceField(choices=relationship, coerce=int, initial=loanTypesEnum.JOINT_BORROWER.value)
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



