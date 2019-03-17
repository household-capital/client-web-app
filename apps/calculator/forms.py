# Django Imports
from django.core.exceptions import ValidationError
from django import forms

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML

# Local Application Imports
from apps.lib.enums import dwellingTypesEnum, loanTypesEnum
from .models import WebCalculator, WebContact


class WebInputForm(forms.ModelForm):
    # A model form with some overriding using form fields to enable choice field enumeration
    # and to enable valuation to be initially validated as a text field

    class Meta:
        model = WebCalculator
        fields = ['loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode', 'referrer']

    relationship = ((loanTypesEnum.JOINT_BORROWER.value, 'Couple'), (loanTypesEnum.SINGLE_BORROWER.value, 'Single'))
    dwelling = ((dwellingTypesEnum.HOUSE.value, 'House'), (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    dwellingType = forms.TypedChoiceField(choices=dwelling, coerce=int, initial=dwellingTypesEnum.HOUSE.value)
    loanType = forms.TypedChoiceField(choices=relationship, coerce=int, initial=loanTypesEnum.JOINT_BORROWER.value)
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
            raise ValidationError("Please enter valuation amount")


class WebOutputForm(forms.ModelForm):
    class Meta:
        model = WebCalculator
        fields = ['email', 'isRefi', 'isTopUp', 'isLive', 'isGive', 'isCare']

    isRefi = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isTopUp = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isLive = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isGive = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    isCare = forms.BooleanField(widget=forms.CheckboxInput(), required=False)


class WebContactForm(forms.ModelForm):
    class Meta:
        model = WebContact
        fields = ['name', 'email', 'phone', 'message']

        widgets = {'message': forms.Textarea(attrs={'rows': 9, 'cols': 50}), }

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
                Div(HTML("<p class='larger'>Contact us</p>"),css_class='pt-3 pb-3'),
                Div(Field('name', placeholder='Enter your name'), css_class="form-group"),
                Div(Field('email', placeholder='Enter your email'), css_class="form-group"),
                Div(Field('phone', placeholder='Enter your phone number'), css_class="form-group"),
                Div(Field('message', placeholder='Tell us how me might be able to assist you'), css_class="form-group"),
                css_class='col-lg-12'),
            ))