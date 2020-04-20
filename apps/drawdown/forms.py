# Django Imports
from django import forms

# Local Application Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum
from apps.application.models import IncomeCalculator



class CalcInputCleanerMixin:

    def clean_valuation(self):
        valuation = self.cleaned_data['valuation']
        valuation = valuation.replace('$', "").replace(',', "")
        try:
            valuation = int(valuation)
        except Exception as ex:
            raise forms.ValidationError('Please check estimated home value')
        if valuation < 100000:
            raise forms.ValidationError('Estimated home value must be at least $100,000')
        if valuation > 5000000:
            raise forms.ValidationError('Please contact us directly if your home value is greater than $5M')
        return valuation

    def clean_age_1(self):
        age_1 = self.cleaned_data['age_1']
        try:
            age_1 = int(age_1)
        except Exception as ex:
            raise forms.ValidationError('Please check age')
        if age_1 < 50 or age_1 > 99:
            raise forms.ValidationError('Age must be between 50 and 99')
        return age_1

    def clean_age_2(self):
        age_2 = self.cleaned_data['age_2']
        if age_2:
            try:
                age_2 = int(age_2)
            except Exception as ex:
                raise forms.ValidationError('Please check age')

            if age_2 < 50 or age_2 > 99:
                raise forms.ValidationError('Age must be between 50 and 99')
            return age_2

    def clean_postcode(self):
        postcode = self.cleaned_data['postcode']
        try:
            postcode = int(postcode)
        except Exception as ex:
             raise forms.ValidationError('Please enter a valid postcode')
        if postcode < 0 or postcode > 9999:
             raise forms.ValidationError('Please enter a valid postcode')
        return postcode



class CalcInputIncomeForm(forms.ModelForm, CalcInputCleanerMixin):

    class Meta:
        model = IncomeCalculator
        fields = ['loanType', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode',
                  'referrer', 'streetAddress', 'suburb', 'state',
                  'choiceOtherNeeds', 'choiceMortgage']

    booleanChoices = ((True, u'Yes'),(False, u'No'))
    relationship = ((loanTypesEnum.JOINT_BORROWER.value, 'Couple'), (loanTypesEnum.SINGLE_BORROWER.value, 'Single'))
    dwelling = ((dwellingTypesEnum.HOUSE.value, 'House'), (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    dwellingType = forms.TypedChoiceField(choices=dwelling, coerce=int, initial=dwellingTypesEnum.HOUSE.value)
    loanType = forms.TypedChoiceField(choices=relationship, coerce=int, initial=loanTypesEnum.SINGLE_BORROWER.value)
    choiceOtherNeeds = forms.ChoiceField(choices=booleanChoices, initial=False, widget=forms.RadioSelect())
    choiceMortgage = forms.ChoiceField(choices=booleanChoices, initial=False, widget=forms.RadioSelect())

    valuation = forms.CharField(required=True, localize=True, label='Estimated Value')

    # Form Fields


    formName = forms.CharField(max_length=30, required=False)
    # Form name field used to identify form on multi-form pages


class CalcOutputIncomeForm(forms.ModelForm):
    class Meta:
        model = IncomeCalculator
        fields = ['email', 'name']

    name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

