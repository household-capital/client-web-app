# Python Imports
from datetime import datetime

# Django Imports
from django import forms
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.forms import widgets

# Third-party Imports
from crispy_forms.bootstrap import PrependedText, InlineRadios
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Row, Column

# Local Application Imports
from apps.lib.site_Enums import loanTypesEnum, caseStagesEnum, incomeFrequencyEnum, purposeCategoryEnum, \
    purposeIntentionEnum, clientTypesEnum
from apps.base.model_utils import address_model_fields
from .models import Case, LossData, LoanPurposes



class CaseDetailsForm(forms.ModelForm):
    # A model form with some overriding using form fields for rendering purposes
    # Additional HTML rendering in the form

    valuation = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    mortgageDebt = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    superAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    pensionAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    propertyImage = forms.ImageField(required=False, widget=forms.FileInput)
    valuationDocument = forms.FileField(required=False, widget=forms.FileInput)

    class Meta:
        model = Case
        fields = ['caseDescription', 'adviser', 'referralCompany', 'caseNotes', 'loanType', 'caseStage',
                  'clientType1', 'surname_1', 'firstname_1', 'preferredName_1', 'birthdate_1', 'age_1', 'sex_1',
                  'salutation_1', 'middlename_1', 'maritalStatus_1',
                  'clientType2', 'surname_2', 'firstname_2', 'preferredName_2', 'birthdate_2', 'age_2', 'sex_2',
                  'salutation_2', 'middlename_2', 'maritalStatus_2',
                  'street', 'suburb', 'postcode', 'valuation', 'dwellingType', 'propertyImage', 'mortgageDebt',
                  'superFund', 'valuationDocument', 'state', 'investmentLabel',
                  'superAmount', 'pensionAmount', 'salesChannel', 'phoneNumber', 'email', 'productType', 'channelDetail'] + address_model_fields
        widgets = {
            'caseNotes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
        }

    caseStages = (
        (caseStagesEnum.DISCOVERY.value, "Discovery"),
        (caseStagesEnum.MEETING_HELD.value, "Meeting Held"),
        (caseStagesEnum.APPLICATION.value, "Application"),
    )

    caseStage = forms.TypedChoiceField(choices=caseStages, coerce=int, initial=caseStagesEnum.DISCOVERY.value)

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
                Div(
                    Div(HTML("Channel"), css_class='form-label'),
                    Div(Field('salesChannel')), css_class="col-lg-6"),
                Div(
                    Div(HTML("Current Status"), css_class='form-label'),
                    Div(Field('caseStage')), css_class="col-lg-6"),
                css_class="row"),

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
                    Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header pt-2'),
                    Div(Div(HTML("Single or Joint Calculation (inc: Nominated Occupant)"), css_class='form-label'),
                        Div(Field('loanType'))),
                    HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Borrower 1</small>"),
                    Row(
                        Column(Div(Div(HTML("Birthdate*"), css_class='form-label'),
                            Div(Field('birthdate_1'))),css_class='col-6'),
                        Column(Div(Div(HTML("Age"), css_class='form-label'),
                            Div(Field('age_1'))),css_class='col-6')),
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

                Div(Div(HTML("&nbsp;"), css_class='form-header'),
                    Div(Div(HTML("Specific Broker / Adviser"), css_class='form-label'),
                        Div(Field('referralCompany'))),
                    Div(Div(HTML("Introducer or Advisor"), css_class='form-label'),
                        Div(Field('adviser'))),

                    Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;Property"), css_class='form-header pt-2'),
                    Div(Div(HTML("Dwelling Type*"), css_class='form-label'),
                        Div(Field('dwellingType'))),
                    Div(Div(HTML("Street Address*"), css_class='form-label'),
                        Div(Field('street'))),
                    Div(Div(HTML("Suburb*"), css_class='form-label'),
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
                        Column(Div(Div(HTML("State*"), css_class='form-label'),
                                   Div(Field('state'))), css_class='col-6'),
                        Column(Div(Div(HTML("Postcode"), css_class='form-label'),
                                   Div(Field('postcode'))), css_class='col-6')),
                    Div(Div(HTML("Valuation*"), css_class='form-label'),
                        Div(Field('valuation'))),
                    Div(Div(HTML("Mortgage Debt"), css_class='form-label'),
                        Div(Field('mortgageDebt'))),

                    Div(HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;Super/Investments"),
                        css_class='form-header'),
                    Div(Div(HTML("Investment Description"), css_class='form-label'),
                        Div(Field('investmentLabel'))),
                    Div(Div(HTML("Super or Investment Fund (if applicable)"), css_class='form-label'),
                        Div(Field('superFund'))),
                    Div(Div(HTML("Amount"), css_class='form-label'),
                        Div(Field('superAmount'))),

                    Div(HTML("<i class='fas fa-hand-holding-usd'></i>&nbsp;&nbsp;Pension"), css_class='form-header'),
                    Div(Div(HTML("Pension Amount"), css_class='form-label'),
                        Div(Field('pensionAmount'))),

                    Div(HTML("<i class='fas fa-barcode'></i>&nbsp;&nbsp;Product Type"), css_class='form-header'),
                    Div(Div(HTML("Product Type"), css_class='form-label'),
                        Div(Field('productType'))),

                    Div(HTML("<i class='fas fa-filter'></i>&nbsp;&nbsp;Channel Detail"), css_class='form-header'),
                    Div(Div(HTML("Channel Detail"), css_class='form-label'),
                        Div(Field('channelDetail'))),

                    Div(HTML("<p class='small pt-2'><i class='fa fa-camera fa-fw'>&nbsp;&nbsp;</i>Property Image</p>"),
                        Field('propertyImage')),
                    Div(HTML("<p class='small pt-2'><i class='far fa-file-pdf'></i>&nbsp;&nbsp;</i>Auto Valuation</p>"),
                        Field('valuationDocument')),
                    css_class="col-lg-6"),
                css_class="row")
        ))

    def clean(self):
        loanType = self.cleaned_data['loanType']
        clientType_2 = self.cleaned_data['clientType2']

        if not self.errors:

            if self.cleaned_data['birthdate_1'] == None and self.cleaned_data['age_1'] == None:
                raise forms.ValidationError("Please enter age or birthdate for Borrower 1")

            if clientType_2 != None:

                if self.cleaned_data['birthdate_2'] == None and self.cleaned_data['age_2'] == None:
                    raise forms.ValidationError("Please enter age or birthdate for Borrower/Role 2")

            if self.cleaned_data['postcode'] != None:
                if self.cleaned_data['dwellingType'] == None:
                    raise forms.ValidationError("Enter property type")
                if self.cleaned_data['valuation'] == None:
                    raise forms.ValidationError("Please enter property valuation estimate")

            if self.cleaned_data['salesChannel'] == None:
                raise forms.ValidationError("Please enter a sales channel")


class LossDetailsForm(forms.ModelForm):
    # Form Data

    class Meta:
        model = LossData
        fields = ['closeReason',
                  'followUpDate', 'followUpNotes',
                  'doNotMarket'
                  ]

        widgets = {
            'lossNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
            'followUpNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),

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
            Div(
                HTML("<i class='fas fa-user-times'></i>&nbsp;&nbsp;<small>Loss Notes</small>"),
                Div(
                    Div(Div(HTML("Close Reason"), css_class='form-label'),
                        Div(Field('closeReason'))),
                    Div(Div(HTML("<br>"))),
                    Div(HTML("<i class='far fa-envelope pb-2'></i></i>&nbsp;&nbsp;<small>Marketing</small>")),
                    Div(
                        Div(Field('doNotMarket'), css_class="col-lg-2"),
                        Div(HTML("<p>Do Not Market</p>"), css_class="col-lg-5 pt-1 pl-0 "),
                        css_class="row "),
                ),
                css_class="col-lg-4"),

            Div(
                HTML("<i class='fas fa-user-tag'></i>&nbsp;&nbsp;<small>Follow-up Required</small>"),
                Div(
                    Div(Div(HTML("Follow-up Date"), css_class='form-label'),
                        Div(Field('followUpDate'))),
                    Div(Div(HTML("Follow-up Notes"), css_class='form-label'),
                        Div(Field('followUpNotes'))),
                ),
                css_class="col-lg-4"),

            css_class='row'),
        Div(

            Div(Div(Div(Submit('submit', 'Update', css_class='btn btn-warning')), css_class='col-lg-8 text-right'),
                css_class='row'),
        ))


class SFPasswordForm(forms.Form):
    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-8'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(Submit('submit', 'Create ', css_class='btn btn-warning')),
            ),
        ))


class CaseAssignForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['owner']

    def __init__(self, *args, **kwargs):
        super(CaseAssignForm, self).__init__(*args, **kwargs)
        self.fields['owner'].queryset = User.objects.filter(profile__isCreditRep=True)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Assign case"), css_class='form-header'),
                Div(
                    Div(HTML("Credit Representative"), css_class='form-label'),
                    Div(Field('owner'))),
                Div(Div(Submit('submit', 'Assign', css_class='btn btn-outline-secondary')), css_class='text-right'),
                Div(HTML("<br>")),

                css_class='col-lg-6'),
            css_class="row ")
    )

    def clean(self):
        if not self.cleaned_data['owner']:
            raise ValidationError("Please select Credit Representative")


class lumpSumPurposeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        if 'amountLabel' in kwargs:
            amountLabel = kwargs['amountLabel']
            kwargs.pop('amountLabel')
        else:
            amountLabel = "Amount"

        if 'descriptionLabel' in kwargs:
            descriptionLabel = kwargs['descriptionLabel']
            kwargs.pop('descriptionLabel')
        else:
            descriptionLabel = "Description"

        super(lumpSumPurposeForm, self).__init__(*args, **kwargs)

        # Form Layout
        self.helper = FormHelper()
        self.helper.form_id = 'clientForm'
        self.helper.form_method = 'POST'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_labels = False
        self.helper.form_show_errors = True
        self.helper.layout = Layout(
            Div(
                Div(Div(HTML(amountLabel), css_class='form-label'),
                    Div(PrependedText('amount', '$'), css_class="col-lg-4")),
                Div(Div(HTML(descriptionLabel), css_class='form-label'),
                    Div(Field('description'), css_class="col-lg-8")),
                Div(Div(HTML("Notes"), css_class='form-label'),
                    Div(Field('notes'), css_class="col-lg-8")),

                Submit('submit', 'Save', css_class='btn btn-warning'),
            )
        )

    class Meta:
        model = LoanPurposes
        fields = ['amount', 'description', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
        }

    # Form Fields
    amount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}))

    def clean_amount(self):
        amount = self.cleaned_data['amount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class drawdownPurposeForm(forms.ModelForm):
    class Meta:
        model = LoanPurposes
        fields = ['description', 'drawdownAmount', 'drawdownFrequency', 'planDrawdowns', 'contractDrawdowns',
                  'notes', 'drawdownStartDate', 'drawdownEndDate', 'active']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
        }

    # Form Fields
    drawdownAmount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())

    drawdownFrequency = forms.ChoiceField(
        choices=(
            (incomeFrequencyEnum.FORTNIGHTLY.value, "Fortnightly"),
            (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        ),
        widget=forms.RadioSelect,
        label="")

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal sub-container'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(Div(HTML("Periodic Drawdown Amount"), css_class='form-label pb-2'),
                    Div(Field('drawdownAmount'))),

                Div(Div(HTML("Drawdown Frequency"), css_class='form-label pb-2'),
                    Div(InlineRadios('drawdownFrequency'))),

                Div(Div(HTML("Description"), css_class='form-label pb-2'),
                    Div(Field('description'))),

                Div(Div(HTML("Active"), css_class='form-label pb-2'),
                    Div(Field('active'))),

                Div(Div(Submit('submit', 'Update', css_class='btn btn-warning'), css_class='pt-4')),

                css_class="col-lg-4"),

            Div(
                Div(Div(HTML("Contracted Drawdowns* (note not years)"), css_class='form-label pb-2'),
                    Div(Field('contractDrawdowns'))),
                Div(Div(HTML("Plan Drawdowns* (note not years)"), css_class='form-label pb-2'),
                    Div(Field('planDrawdowns'))),
                Div(Div(HTML("Start Date (info only)"), css_class='form-label pb-2'),
                    Div(Field('drawdownStartDate'))),
                Div(Div(HTML("End Date (info only)"), css_class='form-label pb-2'),
                    Div(Field('drawdownEndDate'))),

                css_class="col-lg-4"),

            Div(
                Div(Div(HTML("Notes"), css_class='form-label pb-2'),
                    Div(Field('notes'))),

                css_class="col-lg-4"),

            css_class='row')
    )

    def clean_drawdownAmount(self):
        amount = self.cleaned_data['drawdownAmount'].replace("$", "").replace(',', "")
        try:
            amount = int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")
        if amount < 1:
            raise forms.ValidationError("Please enter a positive number")
        return amount

    def clean_planDrawdowns(self):
        if self.cleaned_data['planDrawdowns'] < 0:
            raise forms.ValidationError("Please enter a positive number")
        return self.cleaned_data['planDrawdowns']

    def clean_contractDrawdowns(self):
        if self.cleaned_data['contractDrawdowns'] < 0:
            raise forms.ValidationError("Please enter a positive number")
        return self.cleaned_data['contractDrawdowns']

    def clean(self):
        if self.cleaned_data['planDrawdowns'] < self.cleaned_data['contractDrawdowns']:
            raise forms.ValidationError("Plan drawdowns cannot be shorter than contracted drawdowns")


class purposeAddForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(purposeAddForm, self).__init__(*args, **kwargs)

        # Form Layout
        self.helper = FormHelper()
        self.helper.form_id = 'clientForm'
        self.helper.form_method = 'POST'
        self.helper.form_class = 'form-horizontal'
        self.helper.field_class = 'col-lg-12'
        self.helper.form_show_labels = False
        self.helper.form_show_errors = True
        self.helper.layout = Layout(

            Div(
                Div(
                    Div(Div(HTML("Category"), css_class='form-label'),
                        Div(Field('category'))),
                    Div(Div(HTML("Intention"), css_class='form-label'),
                        Div(Field('intention'))),

                    Div(Submit('submit', 'Save', css_class='btn btn-warning')),
                    css_class="col-lg-12"),
                css_class='row')
        )

    class Meta:
        model = LoanPurposes
        fields = ['category', 'intention']

    def clean(self):
        permitted = [
            (purposeCategoryEnum.TOP_UP.value, purposeIntentionEnum.INVESTMENT.value),
            (purposeCategoryEnum.TOP_UP.value, purposeIntentionEnum.REGULAR_DRAWDOWN.value),
            (purposeCategoryEnum.TOP_UP.value, purposeIntentionEnum.CONTINGENCY.value),
            (purposeCategoryEnum.REFINANCE.value, purposeIntentionEnum.MORTGAGE.value),
            (purposeCategoryEnum.LIVE.value, purposeIntentionEnum.RENOVATIONS.value),
            (purposeCategoryEnum.LIVE.value, purposeIntentionEnum.TRANSPORT_AND_TRAVEL.value),
            (purposeCategoryEnum.GIVE.value, purposeIntentionEnum.GIVE_TO_FAMILY.value),
            (purposeCategoryEnum.CARE.value, purposeIntentionEnum.LUMP_SUM.value),
            (purposeCategoryEnum.CARE.value, purposeIntentionEnum.REGULAR_DRAWDOWN.value),
        ]
        combination = (self.cleaned_data['category'], self.cleaned_data['intention'])
        if combination not in permitted:
            raise ValidationError("This is not a permitted combination")


class smsForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 6, 'cols': 100}))

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True

    helper.layout = Layout(
        Div(
            Div(
                Div(Div(HTML("Text Message"), css_class='form-label'),
                    Div(Field('message'))),

                Div(Submit('submit', 'Send text', css_class='btn btn-warning')),
                css_class="col-lg-12"),
            css_class='row')
    )
