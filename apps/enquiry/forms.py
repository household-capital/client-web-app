# Django Imports
from django import forms
from django.contrib.auth.models import User
from django.forms import ValidationError

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Row, Column

# Local Application Imports
from apps.lib.site_Enums import loanTypesEnum, marketingTypesEnum
from apps.lib.site_Utilities import cleanPhoneNumber
from apps.base.model_utils import address_model_fields
from apps.base.form_utils import AddressFormMixin
from apps.enquiry.models import MarketingCampaign
from .models import Enquiry


# FORMS

class EnquiryForm(AddressFormMixin, forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['loanType', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode',
                  'streetAddress', 'suburb', 'state', 'mortgageDebt',
                  'referrer', 'email', 'phoneNumber',
                  'marketingSource', 'propensityCategory', 'marketing_campaign',
                  'firstname', 'lastname',
                ] + address_model_fields

        widgets = {}

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
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
                    Div(HTML("Propensity Score"), css_class='form-label'),
                    Div(Field('propensityCategory'))),
                Div(
                    Div(HTML("Marketing Campaign"), css_class='form-label'),
                    Div(Field('marketing_campaign'))),
                Div(
                    Div(HTML("Enquiry Source"), css_class='form-label'),
                    Div(Field('referrer'))),
                Div(
                    Div(HTML("How did you hear about us?"), css_class='form-label'),
                    Div(Field('marketingSource'))),

                css_class='col-lg-6'),

            Div(
                Div(Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')),
                    css_class='text-right pt-4'),
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header pt-2'),
                Div(
                    Div(HTML("Single or Joint Borrowers*"), css_class='form-label'),
                    Div(Field('loanType'))),
                Div(
                    Div(HTML("Age Borrower 1*"), css_class='form-label'),
                    Div(Field('age_1'))),
                Div(
                    Div(HTML("Age Borrower 2"), css_class='form-label'),
                    Div(Field('age_2'))),

                Row(
                    Column(Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;Property")), css_class='col-6'),
                    Column(Div(Div(HTML(
                        "<button id='lookup_dialogue' type='button' class='btn btn-sm btn-light'><i class='fas fa-search'></i> Find</button> ")),
                               css_class='text-right'), css_class='col-6')),
                Div(Div(HTML("Street Address"), css_class='form-label'),
                    Div(Field('streetAddress', readonly=True))),
                Div(Div(HTML("Unit / Apartment / Lot"), css_class='form-label'),
                    Div(Field('base_specificity', readonly=True))),
                Div(Div(HTML("Street Number"), css_class='form-label'),
                    Div(Field('street_number', readonly=True))),
                Div(Div(HTML("Street Name"), css_class='form-label'),
                    Div(Field('street_name', readonly=True))),
                Div(Div(HTML("Street Type e.g Avenue, Lane, etc"), css_class='form-label'),
                    Div(Field('street_type', readonly=True))),
                Div(Div(Field('gnaf_id'))),
                Div(Div(HTML("Suburb"), css_class='form-label'),
                    Div(Field('suburb'))),
                Div(Div(HTML("Unit / Apartment / Lot"), css_class='form-label'),
                    Div(Field('base_specificity'))),
                Div(Div(HTML("Street Number"), css_class='form-label'),
                    Div(Field('street_number'))),
                Div(Div(HTML("Street Name"), css_class='form-label'),
                    Div(Field('street_name'))),
                Div(Div(HTML("Street Type e.g Avenue, Lane, etc"), css_class='form-label'),
                    Div(Field('street_type'))),
                Row(
                    Column(Div(Div(HTML("State"), css_class='form-label'),
                               Div(Field('state'))), css_class='col-6'),
                    Column(Div(Div(HTML("Postcode*"), css_class='form-label'),
                               Div(Field('postcode'))), css_class='col-6')),
                Div(Div(HTML("Dwelling Type*"), css_class='form-label'),
                    Div(Field('dwellingType'))),

                Div(Div(HTML("Valuation*"), css_class='form-label'),
                    Div(Field('valuation'))),

                Div(Div(HTML("Existing Mortgage Debt"), css_class='form-label'),
                    Div(Field('mortgageDebt'))),

                Div(css_class="row"),

                css_class='col-lg-6'),

            css_class="row ")
    )

    def clean(self):
        if self.cleaned_data['loanType'] == loanTypesEnum.SINGLE_BORROWER.value and self.cleaned_data['age_2']:
            raise ValidationError("Please check - is this a single or Joint Loan? ")

        if self.cleaned_data['loanType'] == loanTypesEnum.JOINT_BORROWER.value and not self.cleaned_data['age_2']:
            raise ValidationError("Please add second borrower age ")

        return self.cleaned_data

    def clean_firstname(self):
        if self.cleaned_data['firstname']:
            return self.cleaned_data['firstname']

    def clean_lastname(self):
        if self.cleaned_data['lastname']:
            return self.cleaned_data['lastname']

    def clean_phoneNumber(self):
        if self.cleaned_data['phoneNumber']:
            number = cleanPhoneNumber(self.cleaned_data['phoneNumber'])
            if len(number) > 10:
                raise ValidationError("Invalid phone number")
            else:
                return number


class EnquiryDetailForm(AddressFormMixin, forms.ModelForm):

    class Meta:
        model = Enquiry

        fields = [
            'loanType', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode',
            'streetAddress', 'suburb', 'state', 'mortgageDebt',
            'email', 'phoneNumber', 'calcLumpSum', 'calcIncome',
            'productType', 'enquiryStage', 'valuationDocument', 'propensityCategory',
            'referrer', 'marketing_campaign', 'marketingSource',
            'firstname', 'lastname',
        ] + address_model_fields

        widgets = {}

        valuationDocument = forms.FileField(required=False, widget=forms.FileInput)


    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(

            Div(
                Div(
                    Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')),
                    css_class='text-right pt-4'
                ),
                css_class='col-lg-12'
            ),

            Div(
                Div(
                    Div(
                        Div(HTML("Propensity Score"), css_class='form-label'),
                        Div(Field('propensityCategory')),
                    )
                ),

                Div(HTML("<br>")),

                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Contact Details"), css_class='form-header'),
                Div(
                    Div(HTML("First Name"), css_class='form-label'),
                    Div(Field('firstname'))
                ),
                Div(
                    Div(HTML("Last Name"), css_class='form-label'),
                    Div(Field('lastname'))
                ),
                Div(
                    Div(HTML("Phone Number"), css_class='form-label'),
                    Div(Field('phoneNumber'))
                ),
                Div(
                    Div(HTML("Email"), css_class='form-label'),
                    Div(Field('email'))
                ),


                Div(HTML("<br>")),
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Enquiry Source"), css_class='form-header'),
                Div(
                    Div(HTML("Lead Source"), css_class='form-label'),
                    Div(Field('referrer'))
                ),
                Div(
                    Div(HTML("Marketing Source"), css_class='form-label'),
                    Div(Field('marketingSource'))
                ),
                Div(
                    Div(HTML("Marketing Campaign"), css_class='form-label'),
                    Div(Field('marketing_campaign')),
                ),

                HTML('<div class="jumbotron">'),
                Div(
                    Div(HTML("Submission Origin"), css_class='form-label'),
                    Div(HTML("{{ obj.submissionOrigin }}"), css_class='pl-2'),
                ),
                Div(
                    Div(HTML("Origin Timestamp"), css_class='form-label'),
                    Div(HTML("{% if obj.origin_timestamp %}{{ obj.origin_timestamp|date }} - {{ obj.origin_timestamp|time }}{% else %}None{% endif %}"), css_class='pl-2'),
                    css_class='pt-2'
                ),
                Div(
                    Div(HTML("Origin ID"), css_class='form-label'),
                    Div(HTML("{{ obj.origin_id }}"), css_class='pl-2'),
                    css_class='pt-2'
                ),
                HTML('</div>'),

                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header pt-2'),
                Div(
                    Div(HTML("Single or Joint Borrowers"), css_class='form-label'),
                    Div(Field('loanType'))),
                Div(
                    Div(HTML("Age Borrower 1"), css_class='form-label'),
                    Div(Field('age_1'))),
                Div(
                    Div(HTML("Age Borrower 2"), css_class='form-label'),
                    Div(Field('age_2'))),

                Div(HTML("<br>")),

                Row(
                    Column(Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;Property")), css_class='col-6'),
                    Column(Div(Div(HTML(
                        "<button id='lookup_dialogue' type='button' class='btn btn-sm btn-light'><i class='fas fa-search'></i> Find</button> ")),
                        css_class='text-right'), css_class='col-6')),
                Div(Div(HTML("Dwelling Type*"), css_class='form-label'),
                    Div(Field('dwellingType'))),
                Div(Div(HTML("Street Address"), css_class='form-label'),
                    Div(Field('streetAddress', readonly=True))),
                Div(Div(HTML("Unit / Apartment / Lot"), css_class='form-label'),
                    Div(Field('base_specificity', readonly=True))),
                Div(Div(HTML("Street Number"), css_class='form-label'),
                    Div(Field('street_number', readonly=True))),
                Div(Div(HTML("Street Name"), css_class='form-label'),
                    Div(Field('street_name', readonly=True))),
                Div(Div(HTML("Street Type e.g Avenue, Lane, etc"), css_class='form-label'),
                    Div(Field('street_type', readonly=True))),
                Div(Div(Field('gnaf_id'))),
                Div(Div(HTML("Suburb"), css_class='form-label'),
                    Div(Field('suburb'))),
                Row(
                    Column(Div(Div(HTML("State"), css_class='form-label'),
                               Div(Field('state'))), css_class='col-6'),
                    Column(Div(Div(HTML("Postcode*"), css_class='form-label'),
                               Div(Field('postcode'))), css_class='col-6')),

                Div(Div(HTML("Valuation*"), css_class='form-label'),
                    Div(Field('valuation'))),

                Div(Div(HTML("Existing Mortgage Debt"), css_class='form-label'),
                    Div(Field('mortgageDebt'))),

                Div(HTML("<br>")),

                Div(HTML(
                    "<i class='fas fa-search-dollar'></i>&nbsp;&nbsp;Requirements <span>&nbsp;<button type='button' class='btn btn-sm infoBtn' data-toggle='modal' data-target='#productModal'><i class='fas fa-info'></i></button></span></p>"),
                    css_class='form-header'),
                Div(
                    Div(HTML("Funding Amount (lump sum)"), css_class='form-label'),
                    Div(Field('calcLumpSum'))),
                Div(
                    Div(HTML("Funding Amount ($ per month)"), css_class='form-label'),
                    Div(Field('calcIncome'))),
                Div(
                    Div(HTML("Product Type"), css_class='form-label'),
                    Div(Field('productType'))),
                Div(css_class="row"),

                css_class='col-lg-6'),

            css_class="row ")
    )

    def clean(self):
        if self.cleaned_data['loanType'] == loanTypesEnum.SINGLE_BORROWER.value and self.cleaned_data['age_2']:
            raise ValidationError("Please check - is this a single or Joint Loan? ")

        if self.cleaned_data['loanType'] == loanTypesEnum.JOINT_BORROWER.value and not self.cleaned_data['age_2']:
            raise ValidationError("Please add second borrower age ")

        return self.cleaned_data

    def clean_firstname(self):
        if self.cleaned_data['firstname']:
            return self.cleaned_data['firstname']

    def clean_lastname(self):
        if self.cleaned_data['lastname']:
            return self.cleaned_data['lastname']

    def clean_phoneNumber(self):
        if self.cleaned_data['phoneNumber']:
            number = cleanPhoneNumber(self.cleaned_data['phoneNumber'])
            if len(number) > 10:
                raise ValidationError("Invalid phone number")
            else:
                return number


class EnquiryCallForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['firstname', 'lastname', 'postcode', 'phoneNumber', 'marketingSource', 'enquiryNotes', 'propensityCategory', 'marketing_campaign']

        widgets = {
            'enquiryNotes': forms.Textarea(attrs={'rows': 9, 'cols': 50}),
        }

    helper = FormHelper()
    helper.form_id = "clientForm"
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
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
                    Div(HTML("Phone Number"), css_class='form-label'),
                    Div(Field('phoneNumber'))),
                Div(
                    Div(HTML("Enquiry Notes"), css_class='form-label'),
                    Div(Field('enquiryNotes'))),
                Div(
                    Div(HTML("Propensity Score"), css_class='form-label'),
                    Div(Field('propensityCategory'))),
                Div(
                    Div(HTML("Marketing Campaign"), css_class='form-label'),
                    Div(Field('marketing_campaign'))),
                css_class='col-lg-6'),

            Div(
                Div(HTML("<i class='fas fa-headset'></i>&nbsp;&nbsp;Call details"), css_class='form-header'),
                Div(
                    Div(HTML("How did you hear about us?"), css_class='form-label'),
                    Div(Field('marketingSource'))),
                Div(
                    Div(HTML("Postcode"), css_class='form-label'),
                    Div(Field('postcode'))),

                Div(css_class="row"),
                Div(Div(Submit('close', 'End call', css_class='btn btn-outline-secondary'),
                        Submit('submit', 'Continue', css_class='btn btn-warning')), css_class='text-right'),
                Div(HTML("<br>")),

                css_class='col-lg-6'),

            css_class="row ")
    )

    def clean(self):
        if 'close' in self.data:
            if not self.cleaned_data['marketingSource']:
                raise ValidationError('Please select a marketing source')

        return self.cleaned_data

    def clean_firstname(self):
        if self.cleaned_data['firstname']:
            return self.cleaned_data['firstname']

    def clean_lastname(self):
        if self.cleaned_data['lastname']:
            return self.cleaned_data['lastname']

    def clean_phoneNumber(self):
        if self.cleaned_data['phoneNumber']:
            number = cleanPhoneNumber(self.cleaned_data['phoneNumber'])
            if len(number) > 10:
                raise ValidationError("Invalid phone number")
            else:
                return number


class AddressForm(forms.Form):
    lookup_address = forms.CharField(max_length=60, required=True)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False


class PartnerForm(forms.Form):
    """Upload partner file form"""

    partnerTypes = (
        (marketingTypesEnum.YOUR_LIFE_CHOICES.value, "Your Life Choices"),
        (marketingTypesEnum.STARTS_AT_60.value, "Starts at 60"),
        (marketingTypesEnum.CARE_ABOUT.value, "Care About"),
        (marketingTypesEnum.FACEBOOK.value, "Facebook"),
        (-1, "Facebook Interactive"),
        (marketingTypesEnum.NATIONAL_SENIORS.value, "National Seniors"),
        (marketingTypesEnum.LINKEDIN.value, "LinkedIn")        
    )

    partner = forms.ChoiceField(choices=partnerTypes, required=True)
    marketing_campaign = forms.ModelChoiceField(queryset=MarketingCampaign.objects.all(), empty_label=" ---- No Campaign ----", required=False)
    uploadFile = forms.FileField(required=True, widget=forms.FileInput)

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(Div(HTML("Partner*"), css_class='form-label'),
                    Div(Field('partner'))),
                Div(Div(HTML("Marketing Campaign*"), css_class='form-label'),
                    Div(Field('marketing_campaign'))),
                Div(Div(HTML("Upload File"), css_class='form-label'),
                    Div(Field('uploadFile'))),
            )
        ))
