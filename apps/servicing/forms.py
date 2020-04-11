# Django Imports
from django.core.exceptions import ValidationError
from django import forms

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML
from crispy_forms.bootstrap import PrependedText

# Local Application Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum
from .models import FacilityEnquiry, FacilityRoles, FacilityAdditional


class FacilityEnquiryForm(forms.ModelForm):


    def __init__(self, *args, **kwargs):
        if 'facility_instance' in kwargs:
            facility_instance = kwargs['facility_instance']
            kwargs.pop('facility_instance')

        super(FacilityEnquiryForm, self).__init__(*args, **kwargs)

        if facility_instance:
            self.fields['identifiedEnquirer'].queryset = FacilityRoles.objects.filter(facility=facility_instance)

    class Meta:
        model = FacilityEnquiry
        fields = ['identifiedEnquirer', 'otherEnquirerName', 'contactEmail', 'contactPhone', 'actioned','actionNotes']

        widgets = {'enquiryNotes': forms.Textarea(attrs={'rows': 9, 'cols': 50}),
                   'actionNotes': forms.Textarea(attrs={'rows': 8, 'cols': 50}) }

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
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Enquiry Details</small>")),
                Div(Div(HTML("Identified Enquirer"), css_class='form-label'),
                    Div(Field('identifiedEnquirer'))),
                Div(Div(HTML("-or- name of non-identified enquirer "), css_class='form-label'),
                    Div(Field('otherEnquirerName'))),
                Div(Div(HTML("Contact Email"), css_class='form-label'),
                    Div(Field('contactEmail'))),
                Div(Div(HTML("Contact Phone"), css_class='form-label'),
                    Div(Field('contactPhone'))),
                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='fas fa-pencil-alt'></i>&nbsp;&nbsp;<small>Notes</small>")),
                Div(Div(HTML("Enquiry and actions"), css_class='form-label'),
                    Div(Field('actionNotes'))),
                Div(Div(HTML("Status"), css_class='form-label'),
                    Div(Field('actioned'))),
                Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')),
                css_class='col-lg-6'),
            css_class="row"))

    def clean(self):
        if not self.cleaned_data['contactEmail'] and not self.cleaned_data['contactPhone'] :
            raise ValidationError("Phone number of email required")


class FacilityBorrowerForm(forms.Form):

    def __init__(self, *args, **kwargs):
        if 'facility_instance' in kwargs:
            facility_instance = kwargs['facility_instance']
            kwargs.pop('facility_instance')

        super(FacilityBorrowerForm, self).__init__(*args, **kwargs)

        if facility_instance:
            self.fields['identifiedEnquirer'] = forms.ModelChoiceField(queryset=FacilityRoles.objects.filter(facility=facility_instance))


    contactEmail=forms.EmailField(required=False)

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
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Enquiry Details</small>")),
                Div(Div(HTML("Identified Enquirer"), css_class='form-label'),
                    Div(Field('identifiedEnquirer'))),
                Div(Div(HTML("Contact Email"), css_class='form-label'),
                    Div(Field('contactEmail'))),
                Div(Submit('submit', 'Select', css_class='btn btn-outline-secondary')),
                css_class='col-lg-6'),
            css_class="row"))

    def clean(self):
        if not self.cleaned_data['contactEmail'] :
            raise ValidationError("Email required")


class FacilityAdditionalRequest(forms.ModelForm):

    maxDrawdownAmount = 0
    amountRequested = forms.CharField(max_length=10, required=True, initial='')

    class Meta:
        model = FacilityAdditional
        fields = ['amountRequested']

    def __init__(self, *args, **kwargs):
        self.maxDrawdownAmount = kwargs['maxDrawdownAmount']
        kwargs.pop('maxDrawdownAmount')
        super(FacilityAdditionalRequest, self).__init__(*args, **kwargs)
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
                Div(
                    Div(PrependedText('amountRequested','$'))),
                Div(Submit('submit', 'Next', css_class='btn btn-warning')),
                css_class='col-lg-12'),
            css_class="row"))

    def clean_amountRequested(self):
        amount = self.cleaned_data['amountRequested'].replace('$','').replace(',','')
        try:
            intAmount=round(float(amount),0)
            intAmount=int(intAmount)
        except:
            raise ValidationError("Please enter a number only")

        if intAmount >  self.maxDrawdownAmount:
            raise ValidationError("Drawdown request exceeds available amount")

        if intAmount <=  0:
            raise ValidationError("Please enter an amount")

        return intAmount


class FacilityAdditionalConfirm(forms.ModelForm):

    choicePurposes = forms.BooleanField(label="I confirm that this drawdown is for one of the approved purposes detailed in my Loan Contract", required=True)
    choiceNoMaterialChange = forms.BooleanField(label="I confirm that there has been no material change in my circumstances", required=True)

    class Meta:
        model = FacilityAdditional
        fields = ['choicePurposes','choiceNoMaterialChange']

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(
                    Div(Field('choicePurposes')),
                    Div(Field('choiceNoMaterialChange')),
                css_class='col-lg-12'),
                css_class="row pl-5 pb-2"),
            Div(

                Div(Submit('submit', 'Submit', css_class='btn btn-warning'),
                HTML('<a href="{% url "servicing:loanAdditionalRequest" %}"><button type="button" class="btn btn-outline-secondary ml-2">Back</button></a>')),
                css_class='col-lg-12'),
            css_class="row"),

            )

