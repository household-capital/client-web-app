# Django Imports
from django.core.exceptions import ValidationError
from django import forms

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML

# Local Application Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum
from .models import WebCalculator, WebContact

class CalcInputForm(forms.ModelForm):
    # A model form with some overriding using form fields to enable choice field enumeration
    # and to enable valuation to be initially validated as a text field

    class Meta:
        model = WebCalculator
        fields = ['loanType', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode',
                  'referrer', 'isRefi', 'isTopUp', 'isLive', 'isGive', 'isCare']

    relationship = ((loanTypesEnum.JOINT_BORROWER.value, 'Couple'), (loanTypesEnum.SINGLE_BORROWER.value, 'Single'))
    dwelling = ((dwellingTypesEnum.HOUSE.value, 'House'), (dwellingTypesEnum.APARTMENT.value, 'Apartment'))
    dwellingType = forms.TypedChoiceField(choices=dwelling, coerce=int, initial=dwellingTypesEnum.HOUSE.value)
    loanType = forms.TypedChoiceField(choices=relationship, coerce=int, initial=loanTypesEnum.SINGLE_BORROWER.value)
    valuation = forms.CharField(required=True, localize=True, label='Estimated Value')

    isRefi = forms.BooleanField(required=False)
    isTopUp = forms.BooleanField(required=False)
    isLive = forms.BooleanField(required=False)
    isGive = forms.BooleanField(required=False)
    isCare = forms.BooleanField(required=False)

    def clean_valuation(self):
        valuation = self.cleaned_data['valuation']
        valuation = valuation.replace('$', "").replace(',', "")
        try:
            valuation = int(valuation)
            if valuation < 100000 or valuation > 3000000:
                raise forms.ValidationError('Please check estimated home value')
            return valuation
        except:
            raise forms.ValidationError('Please check estimated home value')

    def clean_age_1(self):
        age_1 = self.cleaned_data['age_1']
        try:
            age_1 = int(age_1)
            if age_1 < 50 or age_1 > 99:
                raise forms.ValidationError('Please check')
            return age_1
        except:
            raise forms.ValidationError('Please check')

    def clean_age_2(self):
        age_2 = self.cleaned_data['age_2']
        if age_2:
            try:
                age_2 = int(age_2)
                if age_2 < 50 or age_2 > 99:
                    raise forms.ValidationError('Please check')
                return age_2
            except:
                raise forms.ValidationError('Please check')

    def clean_postcode(self):
        postcode = self.cleaned_data['postcode']
        try:
            postcode = int(postcode)
            if postcode < 0 or postcode > 9999:
                raise forms.ValidationError('Please enter a valid postcode')
            return postcode
        except:
            raise forms.ValidationError('Please enter a valid postcode')

    def clean(self):
        if self.cleaned_data['isTopUp'] or self.cleaned_data['isRefi'] or self.cleaned_data['isLive'] or \
                self.cleaned_data['isGive'] or self.cleaned_data['isCare']:
            return self.cleaned_data
        else:
            raise forms.ValidationError('Please select at least one purpose')


class CalcOutputForm(forms.ModelForm):
    class Meta:
        model = WebCalculator
        fields = ['calcTopUp', 'calcRefi', 'calcLive', 'calcGive', 'calcCare', 'calcTotal', 'email', 'name']

    calcTopUp = forms.CharField(required=False, localize=True)
    calcRefi = forms.CharField(required=False, localize=True)
    calcLive = forms.CharField(required=False, localize=True)
    calcGive = forms.CharField(required=False, localize=True)
    calcCare = forms.CharField(required=False, localize=True)
    calcTotal = forms.CharField(required=False, localize=True)
    name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)

    def clean_calcTopUp(self):
        return self.__checkCurrencyField(self.cleaned_data['calcTopUp'])

    def clean_calcRefi(self):
        return self.__checkCurrencyField(self.cleaned_data['calcRefi'])

    def clean_calcLive(self):
        return self.__checkCurrencyField(self.cleaned_data['calcLive'])

    def clean_calcGive(self):
        return self.__checkCurrencyField(self.cleaned_data['calcGive'])

    def clean_calcCare(self):
        return self.__checkCurrencyField(self.cleaned_data['calcCare'])

    def clean_calcTotal(self):
        return self.__checkCurrencyField(self.cleaned_data['calcTotal'])

    def __checkCurrencyField(self, fieldValue):
        if fieldValue:
            parseField = fieldValue.replace('$', "").replace(',', "")
            try:
                field = int(parseField)
                if field < 0 or field > 1000000:
                    raise forms.ValidationError('Please check')
                return field
            except:
                raise forms.ValidationError('Please check')
        return


class WebContactForm(forms.ModelForm):
    class Meta:
        model = WebContact
        fields = ['name', 'email', 'phone', 'message']

        widgets = {'message': forms.Textarea(attrs={'rows': 6, 'cols': 50}), }

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(Field('name', placeholder='Your name'), css_class="pb-1"),
                Div(Field('email', placeholder='Your email'), css_class=" pb-1"),
                Div(Field('phone', placeholder='Your phone number'), css_class=""),
                css_class='col-lg-5'),
            Div(
                Div(Field('message', placeholder='How can we assist you?'), css_class="form-group"),
                css_class='col-lg-7'),
        css_class="row")
    )


class WebContactDetail(forms.ModelForm):
    class Meta:
        model = WebContact
        fields = ['name', 'email', 'phone', 'message','actionNotes']

        widgets = {'message': forms.Textarea(attrs={'rows': 9, 'cols': 50}),'actionNotes': forms.Textarea(attrs={'rows': 8, 'cols': 50}) }

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Client Information</small>")),
                Div(Field('name', placeholder='Enter your name'), css_class="form-group"),
                Div(Field('email', placeholder='Enter your email'), css_class="form-group"),
                Div(Field('phone', placeholder='Enter your phone number'), css_class="form-group"),
                Div(Field('message', placeholder='Tell us how me might be able to assist you'),
                    css_class="form-group"),
                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='fas fa-pencil-alt'></i>&nbsp;&nbsp;<small>Notes</small>")),
                Div(Field('actionNotes', placeholder='Enter action notes'),
                    css_class="form-group"),
                Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')),
                css_class='col-lg-6'),
        css_class="row"))


# FORMS OLD
class WebInputForm(forms.ModelForm):
    # A model form with some overriding using form fields to enable choice field enumeration
    # and to enable valuation to be initially validated as a text field

    class Meta:
        model = WebCalculator
        fields = ['loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode', 'referrer']

    relationship = ((loanTypesEnum.JOINT_BORROWER.value, 'Couple'), (loanTypesEnum.SINGLE_BORROWER.value, 'Single'))
    dwelling = ((dwellingTypesEnum.HOUSE.value, 'House'), (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    dwellingType = forms.TypedChoiceField(choices=dwelling, coerce=int, initial=dwellingTypesEnum.HOUSE.value)
    loanType = forms.TypedChoiceField(choices=relationship, coerce=int, initial=loanTypesEnum.SINGLE_BORROWER.value)
    name = forms.CharField(max_length=30, required=False)
    valuation = forms.CharField(required=True, localize=True, label='Estimated Value')

    def clean_valuation(self):
        try:
            valuation = self.cleaned_data['valuation']
            valuation = valuation.replace('$', "")
            valuation = valuation.replace(',', "")
            valuation = int(valuation)
            return valuation
        except:
            raise ValidationError("Please enter home value estimate")


class WebOutputForm(forms.ModelForm):
    class Meta:
        model = WebCalculator
        fields = ['email', 'isRefi', 'isTopUp', 'isLive', 'isGive', 'isCare']

    isRefi = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isTopUp = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isLive = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isGive = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isCare = forms.BooleanField(widget=forms.CheckboxInput(), required=False)


