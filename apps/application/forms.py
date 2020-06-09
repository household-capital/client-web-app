# Python Imports
from datetime import datetime

# Django Imports
from django import forms
from django.contrib.auth.models import User
from django.forms import ValidationError

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Row, Column
from crispy_forms.bootstrap import InlineRadios

# Local Imports
from apps.lib.site_Enums import incomeFrequencyEnum, clientTypesEnum

from .models import Application, ApplicationPurposes, ApplicationDocuments


def validate_string_int(value):
    val = value.replace('$', "").replace(',', '')
    try:
        val = int(val)
    except:
        raise ValidationError('Must be a number')
    if val < 0:
        raise ValidationError('Must be a positive number')


def parseCurrencyToInt(str):
    val = str.replace('$', "").replace(',', '')
    try:
        val = int(val)
    except:
        val = 0
    return val


class InitiateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['surname_1', 'firstname_1', 'email', 'mobile']

    surname_1 = forms.CharField(max_length=60, required=True)
    firstname_1 = forms.CharField(max_length=60, required=True)
    email = forms.CharField(max_length=60, required=True)
    mobile = forms.CharField(max_length=60, required=True)

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(Div(HTML("Firstname*"), css_class='form-label'),
                    Div(Field('firstname_1'))),
                Div(Div(HTML("Surname*"), css_class='form-label'),
                    Div(Field('surname_1'))),
                Div(Div(HTML("Your Email*"), css_class='form-label'),
                    Div(Field('email'))),
                Div(Div(HTML("Your Mobile*"), css_class='form-label'),
                    Div(Field('mobile'))),

                css_class='col-lg-10'),
            css_class="row ")

    )


class TwoFactorForm(forms.Form):
    pin = forms.IntegerField(required=True)

    helper = FormHelper()
    helper.form_id =" clientForm"
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(Div(HTML("Enter pin from SMS text message*"), css_class='form-label'),
                    Div(Field('pin'))),

                css_class='col-lg-10'),
            css_class="row ")
    )

    def clean_pin(self):
        if (int(self.cleaned_data['pin']) > 9999) or (int(self.cleaned_data['pin']) < 1000):
            raise forms.ValidationError("Please enter a four digit pin")
        return self.cleaned_data['pin']


class PrimaryBorrowerForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['surname_1', 'firstname_1', 'email', 'mobile']

    surname_1 = forms.CharField(max_length=60, required=True)
    firstname_1 = forms.CharField(max_length=60, required=True)
    email = forms.CharField(max_length=60, required=True)
    mobile = forms.CharField(max_length=60, required=False)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(Div(HTML("Firstname*"), css_class='form-label'),
                    Div(Field('firstname_1'))),
                Div(Div(HTML("Surname*"), css_class='form-label'),
                    Div(Field('surname_1'))),
                Div(Div(HTML("Your Email*"), css_class='form-label'),
                    Div(Field('email'))),
                Div(Div(HTML("Your Mobile"), css_class='form-label'),
                    Div(Field('mobile'))),

                Div(Div(Submit('submit', 'Start', css_class='btn btn-warning')), css_class='text-right'),
                Div(HTML("<br>")),

                css_class='col-lg-10'),
            css_class="row ")

    )


class ObjectivesForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['choiceProduct', 'choiceMortgage', 'choiceOtherNeeds', 'choiceOwnership', 'choiceOccupants']

    id = 'clientForm'
    booleanChoices = {(True, 'Yes'), (False, 'No')}
    choiceProduct = forms.ChoiceField(choices=booleanChoices, widget=forms.RadioSelect(), required=True)
    choiceMortgage = forms.ChoiceField(choices=booleanChoices, widget=forms.RadioSelect(), required=True)
    choiceOtherNeeds = forms.ChoiceField(choices=booleanChoices, widget=forms.RadioSelect(), required=True)
    choiceOwnership = forms.ChoiceField(choices=booleanChoices, widget=forms.RadioSelect(), required=True)
    choiceOccupants = forms.ChoiceField(choices=booleanChoices, widget=forms.RadioSelect(), required=True)



class ApplicantForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.Meta.fields:
            self.fields[field].required = True

    class Meta:
        model = Application
        fields = ['salutation_1', 'surname_1', 'firstname_1', 'birthdate_1', 'sex_1',
                  'streetAddress', 'suburb', 'state', 'postcode',
                  'valuation', 'dwellingType']

    valuation = forms.CharField(max_length=10, required=True)

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
                Div(HTML("<p class='pb-2'><i class='fas fa-user'></i><b>&nbsp;&nbsp;Applicant</b></p>")),
                Row(
                    Column(
                        Div(Div(HTML("Salutation*"), css_class='form-label'),
                            Div(Field('salutation_1'))),
                        css_class='col-4'),
                    Column(

                        Div(Div(HTML("Firstname*"), css_class='form-label'),
                            Div(Field('firstname_1'))),
                        css_class='col-8')

                ),
                Div(Div(HTML("Surname*"), css_class='form-label'),
                    Div(Field('surname_1'))),

                Row(
                    Column(Div(Div(HTML("Birthdate* (dd/mm/yyyy)"), css_class='form-label'),
                               Div(Field('birthdate_1'))), css_class='form-group col-6'),
                    Column(Div(Div(HTML("Gender*"), css_class='form-label'),
                               Div(Field('sex_1'))), css_class='form-group col-6')),

                css_class='col-lg-5 pb-4'),

            Div(
                Div(HTML("<p class='pb-2'><i class='fas fa-house-user'></i><b>&nbsp;&nbsp;Your home</b></p>")),
                Div(Div(HTML("Street Address*"), css_class='form-label'),
                    Div(Field('streetAddress'))),
                Row(
                    Column(Div(Div(HTML("Suburb*"), css_class='form-label'),
                               Div(Field('suburb'))), css_class=' col-6'),
                    Column(Div(HTML("State*"), css_class='form-label'),
                           Div(Field('state')), css_class=' col-3 pl-2'),
                    Column(Div(HTML("Postcode*"), css_class='form-label'),
                           Div(Field('postcode')), css_class=' col-3 pl-2'),
                    css_class='no-gutters'),

                Row(
                    Column(Div(HTML("Home Type*"), css_class='form-label'),
                           Div(Field('dwellingType')), css_class='form-group col-6'),
                    Column(Div(HTML("Estimated Valuation*"), css_class='form-label'),
                           Div(Field('valuation', css_class='text-right pr-3')), css_class='form-group col-6 pl-2'),
                    css_class='no-gutters'),
                css_class='col-lg-5 pb-4'),
            css_class="row justify-content-center")
    )

    def clean_sex_1(self):
        if self.cleaned_data['sex_1'] == None:
            raise ValidationError('Please select')
        else:
            return self.cleaned_data['sex_1']

    def clean_dwellingType(self):
        if self.cleaned_data['dwellingType'] == None:
            raise ValidationError('Please select')
        else:
            return self.cleaned_data['dwellingType']

    def clean_valuation(self):
        val = parseCurrencyToInt(self.cleaned_data['valuation'])
        if val < 100000:
            raise ValidationError('Please check valuation')
        return val


class ApplicantTwoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.Meta.fields:
            self.fields[field].required = True

    class Meta:
        model = Application
        fields = ['surname_2', 'firstname_2', 'birthdate_2', 'sex_2', 'clientType2', 'salutation_2']

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
                Div(HTML("<p class='pb-2'><i class='far fa-user''></i><b>&nbsp;&nbsp;Second Applicant</b></p>")),
                Row(
                    Column(
                        Div(Div(HTML("Salutation*"), css_class='form-label'),
                            Div(Field('salutation_2'))),
                        css_class='col-4'),
                    Column(

                        Div(Div(HTML("Firstname*"), css_class='form-label'),
                            Div(Field('firstname_2'))),
                        css_class='col-8')

                ),
                Div(Div(HTML("Surname*"), css_class='form-label'),
                    Div(Field('surname_2'))),
                Row(
                    Column(Div(Div(HTML("Birthdate* (dd/mm/yyyy)"), css_class='form-label'),
                               Div(Field('birthdate_2'))), css_class='col-6'),
                    Column(Div(Div(HTML("Gender*"), css_class='form-label'),
                               Div(Field('sex_2'))), css_class='col-6')),
                Div(Div(HTML("Role*"), css_class='form-label'),
                    Div(Field('clientType2'))),

                css_class='col-lg-12 pb-4'),

            css_class="row justify-content-center")
    )

    def clean_sex_2(self):
        if self.cleaned_data['sex_2'] == None:
            raise ValidationError('Please select')
        else:
            return self.cleaned_data['sex_2']


class LoanObjectivesForm(forms.ModelForm):
    class Meta:
        model = ApplicationPurposes
        fields = ['drawdownAmount', 'drawdownFrequency', 'planPeriod']

    drawdownPeriods = (
        (5, '5 years'),
        (6, '6 years'),
        (7, '7 years'),
        (8, '8 years'),
        (9, '9 years'),
        (10, '10 years')
    )

    drawdownAmount = forms.IntegerField(widget=forms.HiddenInput(), required=True)

    planPeriod = forms.TypedChoiceField(choices=drawdownPeriods, coerce=int)

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(Field('drawdownFrequency')),
        Row(
            Column(HTML("<p class='pt-2'>for</p>"), css_class='col-3'),
            Column(Field('planPeriod'), css_class='col-9')),
        Div(Field('drawdownAmount'))
    )

    def clean_drawdownAmount(self):
        if self.cleaned_data['drawdownAmount'] == 0:
            raise ValidationError("Please select a drawdown amount")
        else:
            return self.cleaned_data['drawdownAmount']


class AssetsForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['assetSaving', 'assetVehicles', 'assetOther', 'liabLoans',
                  'liabCards', 'liabOther', 'limitCards']

    assetSaving = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    assetVehicles = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    assetOther = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    liabLoans = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    liabCards = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    liabOther = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    limitCards = forms.CharField(max_length=12, required=True, validators=[validate_string_int])

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
                Div(HTML("<p class='pb-2'><i class='fas fa-user-plus'></i><b>&nbsp;&nbsp;Assets</b></p>")),
                Div(Div(HTML("Savings/Investments*"), css_class='form-label'),
                    Div(Field('assetSaving', css_class='text-right'))),
                Div(Div(HTML("Motor Vehicles*"), css_class='form-label'),
                    Div(Field('assetVehicles', css_class='text-right'))),
                Div(Div(HTML("Other*"), css_class='form-label'),
                    Div(Field('assetOther', css_class='text-right'))),

                css_class='col-lg-6 pb-4'),

            Div(
                Div(HTML("<p class='pb-2'><i class='fas fa-user-minus'></i><b>&nbsp;&nbsp;Liabilities</b></p>")),
                Div(Div(HTML("Home Loans*"), css_class='form-label'),
                    Div(Field('liabLoans', css_class='text-right'))),
                Div(Div(HTML("Credit Cards*"), css_class='form-label'),
                    Div(Field('liabCards', css_class='text-right'))),
                Div(Div(HTML("Other*"), css_class='form-label'),
                    Div(Field('liabOther', css_class='text-right'))),
                HTML('<hr>'),
                Div(Div(HTML("Total Credit Card <b>Limits</b>*"), css_class='form-label'),
                    Div(Field('limitCards', css_class='text-right'))),

                css_class='col-lg-6 pb-4'),

            css_class="row justify-content-center")
    )

    def clean(self):
        super(forms.ModelForm, self).clean()
        for field in self.fields:
            if field in self.cleaned_data:
                self.cleaned_data[field] = parseCurrencyToInt(self.cleaned_data[field])
        return self.cleaned_data


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['incomePension', 'incomePensionFreq',
                  'incomeSavings', 'incomeSavingsFreq',
                  'incomeOther', 'incomeOtherFreq',
                  'expenseHomeIns', 'expenseHomeInsFreq',
                  'expenseRates', 'expenseRatesFreq',
                  'expenseGroceries', 'expenseGroceriesFreq',
                  'expenseUtilities', 'expenseUtilitiesFreq',
                  'expenseMedical', 'expenseMedicalFreq',
                  'expenseTransport', 'expenseTransportFreq',
                  'expenseRepay', 'expenseRepayFreq',
                  'expenseOther', 'expenseOtherFreq',
                  'totalAnnualIncome', 'totalAnnualExpenses'
                  ]

    incomeFrequencyTypes = (
        (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
        (incomeFrequencyEnum.FORTNIGHTLY.value, "Fortnightly"),
        (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        (incomeFrequencyEnum.ANNUALLY.value, "Annually")
    )

    expenseFrequencyTypes = (
        (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
        (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        (incomeFrequencyEnum.QUARTERLY.value, "Quarterly"),
        (incomeFrequencyEnum.ANNUALLY.value, "Annually")
    )

    totalAnnualIncome = forms.CharField(max_length=12, required=True, widget=forms.HiddenInput(),
                                        validators=[validate_string_int])
    totalAnnualExpenses = forms.CharField(max_length=12, required=True, widget=forms.HiddenInput(),
                                          validators=[validate_string_int])
    incomeSavings = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    incomePension = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    incomeOther = forms.CharField(max_length=12, required=True, validators=[validate_string_int])

    expenseHomeIns = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseRates = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseGroceries = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseUtilities = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseMedical = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseTransport = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseRepay = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseOther = forms.CharField(max_length=12, required=True, validators=[validate_string_int])

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(Div(
            Row(
                Column(
                    Div(HTML("<p class='pb-2'><i class='fas fa-user-plus'></i><b>&nbsp;&nbsp;Income</b></p>"))
                    , css_class='col-6')),
            Row(
                Column(
                    Div(Div(HTML("Pension Income"), css_class='form-label'),
                        Div(Field('incomePension', css_class='text-right'))), css_class='col-6'),
                Column(
                    Div(Div(HTML("&nbsp;"), css_class='form-label'),
                        Div(Field('incomePensionFreq', css_class='form-label')),
                        ), css_class='col-4')),
            Row(
                Column(
                    Div(Div(HTML("Super / Savings Income"), css_class='form-label'),
                        Div(Field('incomeSavings', css_class='text-right'))), css_class='col-6'),
                Column(
                    Div(Div(HTML("&nbsp;"), css_class='form-label'),
                        Div(Field('incomeSavingsFreq', css_class='form-label'))), css_class='col-4')),
            Row(
                Column(
                    Div(Div(HTML("Other Income"), css_class='form-label'),
                        Div(Field('incomeOther', css_class='text-right '))), css_class='col-6'),
                Column(
                    Div(Div(HTML("&nbsp;"), css_class='form-label'),
                        Div(Field('incomeOtherFreq', css_class='form-label'))), css_class='col-4')),
            css_class='col-lg-6 pb-4'),

            Div(
                Row(
                    Column(
                        Div(HTML("<p class='pb-2'><i class='fas fa-user-minus'></i><b>&nbsp;&nbsp;Expenses</b></p>"))
                        , css_class='col-6')),
                Row(
                    Column(
                        Div(Div(HTML("Home insurance"), css_class='form-label'),
                            Div(Field('expenseHomeIns', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseHomeInsFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Rates/body corporate fees etc"), css_class='form-label'),
                            Div(Field('expenseRates', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseRatesFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Groceries and food"), css_class='form-label'),
                            Div(Field('expenseGroceries', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseGroceriesFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Utilities / regular bills"), css_class='form-label'),
                            Div(Field('expenseUtilities', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseUtilitiesFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Medical and health"), css_class='form-label'),
                            Div(Field('expenseMedical', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseMedicalFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Transport"), css_class='form-label'),
                            Div(Field('expenseTransport', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseTransportFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Loan repayments"), css_class='form-label'),
                            Div(Field('expenseRepay', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseRepayFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Other living expenses"), css_class='form-label'),
                            Div(Field('expenseOther', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseOtherFreq', css_class='form-label'))), css_class='col-4')),

                css_class='col-lg-6 pb-4'),
            css_class='row'),

        Field('totalAnnualIncome'), Field('totalAnnualExpenses'))

    def clean(self):
        for field in self.cleaned_data:
            if 'Freq' not in field:
                self.cleaned_data[field] = parseCurrencyToInt(self.cleaned_data[field])

        if self.cleaned_data['totalAnnualExpenses'] <= 0:
            raise ValidationError('Please enter expenses')

        return self.cleaned_data


class HomeExpensesForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['expenseHomeIns', 'expenseHomeInsFreq',
                  'expenseRates', 'expenseRatesFreq',
                  ]

    expenseFrequencyTypes = (
        (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
        (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        (incomeFrequencyEnum.QUARTERLY.value, "Quarterly"),
        (incomeFrequencyEnum.ANNUALLY.value, "Annually")
    )

    expenseHomeIns = forms.CharField(max_length=12, required=True, validators=[validate_string_int])
    expenseRates = forms.CharField(max_length=12, required=True, validators=[validate_string_int])

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(Div(
                Row(
                    Column(
                        Div(Div(HTML("Home insurance"), css_class='form-label'),
                            Div(Field('expenseHomeIns', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseHomeInsFreq', css_class='form-label'))), css_class='col-4')),
                Row(
                    Column(
                        Div(Div(HTML("Rates / body corporate fees"), css_class='form-label'),
                            Div(Field('expenseRates', css_class='text-right'))), css_class='col-6'),
                    Column(
                        Div(Div(HTML("&nbsp;"), css_class='form-label'),
                            Div(Field('expenseRatesFreq', css_class='form-label'))), css_class='col-4')),
                css_class='col-lg-6 pb-4'),
            css_class='row')
    )

    def clean(self):
        for field in self.cleaned_data:
            if 'Freq' not in field:
                self.cleaned_data[field] = parseCurrencyToInt(self.cleaned_data[field])

        return self.cleaned_data


class ConsentsForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['consentPrivacy', 'consentElectronic']

    consentPrivacy = forms.BooleanField(required=True,
                                       label='I consent to the use and disclosure of my personal information and credit-related information')
    consentElectronic = forms.BooleanField(required=True,
                                          label='I consent to receiving notices and other documents electronically')

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = True
    helper.form_show_errors = True


class BankForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.Meta.fields:
            self.fields[field].required = True

    class Meta:
        model = Application
        fields = ['bankBsbNumber', 'bankAccountName', 'bankAccountNumber']

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
                Div(Div(HTML("Account Name*"), css_class='form-label'),
                    Div(Field('bankAccountName'))),
                Div(Div(HTML("BSB*"), css_class='form-label'),
                    Div(Field('bankBsbNumber'))),
                Div(Div(HTML("Account Number*"), css_class='form-label'),
                    Div(Field('bankAccountNumber'))))
        )
    )


class SigningForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        self.helper = FormHelper()
        self.helper.form_id = 'clientForm'
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = False
        self.helper.form_show_errors = True

        customerName_1 = None
        customerName_2 = None

        if kwargs['jointSigning']:
            customerName_1 = kwargs['customerName_1']
            customerName_2 = kwargs['customerName_2']
            for field in ['customerName_1', 'customerName_2', 'jointSigning']:
                kwargs.pop(field)
            super().__init__(*args, **kwargs)
            self.fields['signingName_1'].required = True
            self.fields['signingName_2'].required = True

            self.helper.layout = Layout(
                    Div(
                        Div(Div(HTML(customerName_1 + " *"), css_class='form-label'),
                            Div(Field('signingName_1')),

                            Div(HTML("Signing Pin*"), css_class='form-label pt-4'),
                            Div(Field('pin')),

                            css_class="col-md-5"),
                        Div(Div(HTML(customerName_2 + " *"), css_class='form-label'),
                            Div(Field('signingName_2')),
                            css_class="col-md-5"),
                    css_class="row")
            )

        else:
            customerName_1 = kwargs['customerName_1']
            for field in ['customerName_1', 'jointSigning']:
                kwargs.pop(field)

            super().__init__(*args, **kwargs)
            self.fields['signingName_1'].required = True
            self.fields.pop('signingName_2')

            self.helper.layout = Layout(
                Div(
                    Div(
                        Div(Div(HTML(customerName_1 + " *"), css_class='form-label'),
                            Div(Field('signingName_1')),
                            Div(HTML("Signing Pin*"), css_class='form-label pt-4'),
                            Div(Field('pin')),
                            css_class="col-md-5"),
                        css_class="row")
                ))

    pin = forms.IntegerField(required=True)

    class Meta:
        model = Application
        fields = ['signingName_1', 'signingName_2']

    def clean_pin(self):
        if (int(self.cleaned_data['pin']) > 9999) or (int(self.cleaned_data['pin']) < 1000):
            raise forms.ValidationError("Please enter a four digit pin")
        return self.cleaned_data['pin']


class DocumentForm(forms.ModelForm):

    class Meta:
        model = ApplicationDocuments
        fields = ['documentType', 'document']

    document = forms.FileField(required=True, widget=forms.FileInput)

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
                Div(Div(HTML("Document Type*"), css_class='form-label'),
                    Div(Field('documentType'))),
                Div(Div(HTML("Document"), css_class='form-label'),
                    Div(Field('document'))),
        )
    ))
