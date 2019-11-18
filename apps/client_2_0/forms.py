# Django Imports
from django import forms
from django.forms import widgets

# Third-party Imports
from crispy_forms.bootstrap import (PrependedText, InlineRadios)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML

# Local Application Imports
from apps.case.models import Case, Loan, ModelSetting
from apps.lib.site_Enums import incomeFrequencyEnum


# FORMS
class ClientDetailsForm(forms.ModelForm):
    valuation = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    mortgageDebt = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    superAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    pensionAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())

    resetConsents = forms.BooleanField(required=False)

    class Meta:
        model = Case
        fields = ['loanType',
                  'clientType1', 'surname_1', 'firstname_1', 'birthdate_1', 'age_1', 'sex_1',
                  'clientType2', 'surname_2', 'firstname_2', 'birthdate_2', 'age_2', 'sex_2',
                  'street', 'suburb', 'postcode', 'state', 'valuation', 'dwellingType', 'mortgageDebt', 'superFund',
                  'superAmount', 'pensionType', 'pensionAmount']
        widgets = {
            'caseNotes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
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

                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header'),
                Div(Div(HTML("Single or Joint Borrowers"), css_class='form-label'),
                    Div(Field('loanType'))),
                HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Borrower 1</small>"),
                Div(Div(HTML("Birthdate"), css_class='form-label'),
                    Div(Field('birthdate_1'))),
                Div(Div(HTML("Age"), css_class='form-label'),
                    Div(Field('age_1'))),
                Div(Div(HTML("Surname"), css_class='form-label'),
                    Div(Field('surname_1'))),
                Div(Div(HTML("Firstname"), css_class='form-label'),
                    Div(Field('firstname_1'))),
                Div(Div(HTML("Gender"), css_class='form-label'),
                    Div(Field('sex_1'))),
                Div(Div(HTML("Borrower Role"), css_class='form-label'),
                    Div(Field('clientType1'))),
                HTML("<i class='far fa-user'></i>&nbsp;&nbsp;<small>Borrower 2</small>"),
                Div(Div(HTML("Birthdate"), css_class='form-label'),
                    Div(Field('birthdate_2'))),
                Div(Div(HTML("Age"), css_class='form-label'),
                    Div(Field('age_2'))),
                Div(Div(HTML("Surname"), css_class='form-label'),
                    Div(Field('surname_2'))),
                Div(Div(HTML("Firstname"), css_class='form-label'),
                    Div(Field('firstname_2'))),
                Div(Div(HTML("Gender"), css_class='form-label'),
                    Div(Field('sex_2'))),
                Div(Div(HTML("Borrower Role"), css_class='form-label'),
                    Div(Field('clientType2'))),
                css_class="col-lg-4"),

            Div(Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;Property"), css_class='form-header'),
                Div(Div(HTML("Postcode"), css_class='form-label'),
                    Div(Field('postcode'))),
                Div(Div(HTML("Dwelling Type"), css_class='form-label'),
                    Div(Field('dwellingType'))),
                Div(Div(HTML("Street Address"), css_class='form-label'),
                    Div(Field('street'))),
                Div(Div(HTML("Suburb"), css_class='form-label'),
                    Div(Field('suburb'))),
                Div(Div(HTML("State"), css_class='form-label'),
                    Div(Field('state'))),
                Div(Div(HTML("Valuation"), css_class='form-label'),
                    Div(Field('valuation'))),
                Div(Div(HTML("Mortgage Debt"), css_class='form-label'),
                    Div(Field('mortgageDebt'))),
                css_class="col-lg-4"),

            Div(Div(HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;Super/Investments"), css_class='form-header'),
                Div(Div(HTML("Super or Investment Fund"), css_class='form-label'),
                    Div(Field('superFund'))),
                Div(Div(HTML("Super Fund Assets"), css_class='form-label'),
                    Div(Field('superAmount'))),

                Div(Div(HTML("<i class='fas fa-hand-holding-usd'></i>&nbsp;&nbsp;Pension"), css_class='form-header'),
                    Div(Div(HTML("Pension Amount"), css_class='form-label'),
                        Div(Field('pensionAmount'))),
                    Div(Div(HTML("Pension Status"), css_class='form-label'),
                        Div(Field('pensionType')))),
                Div(
                    Div(HTML("<i class='fas fa-users'></i>&nbsp;&nbsp;<small>Meeting</small>")),
                    Div(Div(Field('resetConsents'), css_class="col-lg-1 pl-0"),
                        Div(HTML("<p class='small'>Reset Data</p>"), css_class="col-lg-6 pt-1 pl-3"),
                        css_class="row pl-0")),
                Div(Div(Submit('submit', 'Update Information', css_class='btn btn-warning'),
                        HTML("<br>"),
                        HTML("<br>"))),

                css_class="col-lg-4"),

            css_class="row")
    )

    def clean(self):
        loanType = self.cleaned_data['loanType']

        if loanType == 0:
            if self.cleaned_data['birthdate_1'] == None and self.cleaned_data['age_1'] == None:
                raise forms.ValidationError("Enter age or birthdate for Borrower")

        if loanType == 1:
            if self.cleaned_data['birthdate_1'] == None and self.cleaned_data['age_1'] == None:
                raise forms.ValidationError("Enter age or birthdate for Borrower 1")
            if self.cleaned_data['birthdate_2'] == None and self.cleaned_data['age_2'] == None:
                raise forms.ValidationError("Enter age or birthdate for Borrower 2")

        if self.cleaned_data['postcode'] != None:
            if self.cleaned_data['dwellingType'] == None:
                raise forms.ValidationError("Enter property type")
            if self.cleaned_data['valuation'] == None:
                raise forms.ValidationError("Enter property valuation estimate")


class SettingsForm(forms.ModelForm):
    # Form Fields
    class Meta:
        model = ModelSetting
        fields = ['housePriceInflation', 'interestRate', 'investmentRate', 'inflationRate', 'projectionAge']

    # Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(
                    Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;<small>House Price Inflation</small>")),
                    Div(PrependedText('housePriceInflation', '%'), placeholder='House Price Inflation'),
                    Div(HTML("<i class='fas fa-chart-bar'></i>&nbsp;&nbsp;<small>Base (cash) Interest Rate </small>")),
                    Div(PrependedText('interestRate', '%'), placeholder='Interest Rate'),
                    Div(HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Income Projection Age</small>")),
                    Div(Field('projectionAge', placeholder='Projection Age')),
                    css_class="col-md-4"),

                Div(
                    Div(HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;<small>Investment Return)</small>")),
                    Div(PrependedText('investmentRate', '%'), placeholder='Investment Return'),
                    Div(HTML("<i class='fas fa-chart-line'></i>&nbsp;&nbsp;<small>Inflation</small>")),
                    Div(PrependedText('inflationRate', '%'), placeholder='inflation'),
                    css_class="col-md-4"),
                css_class='row justify-content-md-center'),
            Div(
                Div(
                    HTML("<br>"),
                    Div(Submit('submit', 'Update Settings', css_class='btn btn-warning')),
                    css_class="col-md-4 text-center"),
                css_class='row justify-content-md-center')

        ))


class IntroChkBoxForm(forms.ModelForm):
    # Form Fields
    choiceRetireAtHome = forms.BooleanField(label="Retire at home", required=True)
    choiceAvoidDownsizing = forms.BooleanField(label="Avoid downsizing", required=True)
    choiceAccessFunds = forms.BooleanField(label="Access additional retirement funds", required=True)

    class Meta:
        model = Loan
        fields = ['choiceRetireAtHome', 'choiceAvoidDownsizing', 'choiceAccessFunds']

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'  # Using a navigation button to submit, so form name has to be the same
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(Field('choiceRetireAtHome'), css_class='checkbox-inline col-3'),
                Div(Field('choiceAvoidDownsizing'), css_class='checkbox-inline col-3'),
                Div(Field('choiceAccessFunds', css_class='checkbox-inline col-6')),
                css_class='row justify-content-center'),
        )
    )



class debtRepayForm(forms.ModelForm):
    # Form Fields
    class Meta:
        model = Loan
        fields = ['refinanceAmount']

    refinanceAmount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())

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
            Div(Div(HTML("Refinance Amount"), css_class='form-label'),
                Div(PrependedText('refinanceAmount', '$'))),
            HTML("<br>"),
            Submit('submit', 'Save', css_class='btn btn-warning'),
        )
    )

    def clean_refinanceAmount(self):
        amount = self.cleaned_data['refinanceAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class giveAmountForm(forms.ModelForm):
    # Nb: Uses two helpers to creata single form

    # Form Fields
    class Meta:
        model = Loan
        fields = ['giveAmount', 'giveDescription']

    giveAmount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())
    giveDescription = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}))

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_tag = False
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(HTML("Amount"), css_class='form-label'),
                Div(PrependedText('giveAmount', '$'), css_class="col-lg-4")),
            Div(Div(HTML("Description"), css_class='form-label'),
                Div(Field('giveDescription'), css_class="col-lg-6")),

            Submit('submit', 'Save', css_class='btn btn-warning'),
        )
    )

    def clean_giveAmount(self):
        amount = self.cleaned_data['giveAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class renovateAmountForm(forms.ModelForm):
    # Form Fields
    class Meta:
        model = Loan
        fields = ['renovateAmount', 'renovateDescription']

    renovateAmount = forms.CharField(required=True, localize=True, label='Amount', widget=widgets.TextInput())
    renovateDescription = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}))

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(HTML("Amount"), css_class='form-label'),
                Div(PrependedText('renovateAmount', '$'), css_class="col-lg-4")),
            Div(Div(HTML("Description"), css_class='form-label'),
                Div(Field('renovateDescription'), css_class="col-lg-6")),

            Submit('submit', 'Save', css_class='btn btn-warning'),
        )
    )

    def clean_renovateAmount(self):
        amount = self.cleaned_data['renovateAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class travelAmountForm(forms.ModelForm):
    # Form Fields
    class Meta:
        model = Loan
        fields = ['travelAmount', 'travelDescription']

    travelAmount = forms.CharField(required=True, localize=True, label='Amount', widget=widgets.TextInput())
    travelDescription = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}))

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(HTML("Amount"), css_class='form-label'),
                Div(PrependedText('travelAmount', '$'), css_class="col-lg-4")),
            Div(Div(HTML("Description"), css_class='form-label'),
                Div(Field('travelDescription'), css_class="col-lg-6")),

            Submit('submit', 'Save', css_class='btn btn-warning'),
        )
    )

    def clean_travelAmount(self):
        amount = self.cleaned_data['travelAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class careAmountForm(forms.ModelForm):
    # Form Fields

    class Meta:
        model = Loan
        fields = ['careAmount', 'careDescription']

    careAmount = forms.CharField(required=True, localize=True, label='Amount', widget=widgets.TextInput())
    careDescription = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}))

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(HTML("Amount"), css_class='form-label'),
                Div(PrependedText('careAmount', '$'), css_class="col-lg-4")),
            Div(Div(HTML("Description"), css_class='form-label'),
                Div(Field('careDescription'), css_class="col-lg-6")),

            Submit('submit', 'Save', css_class='btn btn-warning'),

        )
    )

    def clean_careAmount(self):
        amount = self.cleaned_data['careAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class interestPaymentForm(forms.ModelForm):
    # Form Fields

    class Meta:
        model = Loan
        fields = ['interestPayAmount', 'interestPayPeriod']

    interestPayAmount = forms.CharField(required=True, localize=True, label='Amount', widget=widgets.TextInput())
    interestPayPeriod = forms.CharField(required=True, localize=True, label='Amount', widget=widgets.TextInput())

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
            Div(Div(HTML("Intended monthly payment?"), css_class='form-label'),
                Div(PrependedText('interestPayAmount', '$'))),
            Div(Div(HTML("For how long (years)?"), css_class='form-label'),
                Div(Field('interestPayPeriod'))),

            Submit('submit', 'Save', css_class='btn btn-warning'),

        )
    )

    def clean_interestPayAmount(self):
        amount = self.cleaned_data['interestPayAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class protectedEquityForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['protectedEquity']

    protectedEquity = forms.ChoiceField(
        choices=(
            (0, "0%"),
            (5, "5%"),
            (10, "10%"),
            (15, "15%"),
            (20, "20%"),
        ),
        widget=forms.RadioSelect,
        label=""
    )

    helper = FormHelper()
    helper.form_tag = False
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(InlineRadios('protectedEquity'))
        ),
        Submit('submit', 'Save', css_class='btn btn-warning'),
    )


class topUpLumpSumForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['topUpAmount', 'topUpDescription']

    # Form Fields
    topUpAmount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())
    topUpDescription = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}))

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(HTML("Amount"), css_class='form-label'),
                Div(PrependedText('topUpAmount', '$'), css_class="col-lg-4")),
            Div(Div(HTML("Planned use of top-up funds"), css_class='form-label'),
                Div(Field('topUpDescription'), css_class="col-lg-8")),

            Submit('submit', 'Save', css_class='btn btn-warning'),
        )
    )

    def clean_topUpAmount(self):
        amount = self.cleaned_data['topUpAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")

class topUpContingencyForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['topUpContingencyAmount', 'topUpContingencyDescription']

    # Form Fields
    topUpContingencyAmount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())
    topUpContingencyDescription = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}))

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(HTML("Amount"), css_class='form-label'),
                Div(PrependedText('topUpContingencyAmount', '$'), css_class="col-lg-4")),
            Div(Div(HTML("Your objective for contingency funding"), css_class='form-label'),
                Div(Field('topUpContingencyDescription'), css_class="col-lg-8")),

            Submit('submit', 'Save', css_class='btn btn-warning'),
        )
    )

    def clean_topUpContingencyAmount(self):
        amount = self.cleaned_data['topUpContingencyAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")



class topUpDrawdownForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['topUpIncomeAmount', 'topUpFrequency', 'topUpPeriod','topUpBuffer']

    # Form Fields
    topUpIncomeAmount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())
    topUpPeriod = forms.ChoiceField(
        choices=(
            (5, "5 Years"),
            (7, "7 Years"),
            (10, "10 Years"),
        ),
        widget=forms.RadioSelect,
        label="")
    topUpFrequency = forms.ChoiceField(
        choices=(
            (incomeFrequencyEnum.FORTNIGHTLY.value, "Fortnightly"),
            (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        ),
        widget=forms.RadioSelect,
        label="")

    topUpBuffer = forms.ChoiceField(
        choices=(
            (1, "Yes"),
            (0, "No"),
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
                Div(Div(HTML("Periodic Drawdown Amount"), css_class='form-label'),
                    Div(PrependedText('topUpIncomeAmount', '$'))),

                Div(Div(HTML("Drawdown Plan Period (years)*"), css_class='form-label'),
                    Div(InlineRadios('topUpPeriod'))),

                Div(Div(Submit('submit', 'Save', css_class='btn btn-warning'))),

                css_class="col-lg-5"),

            Div(
                Div(Div(HTML("Drawdown Frequency"), css_class='form-label'),
                    Div(InlineRadios('topUpFrequency'))),

                Div(Div(HTML("'Rainy Day' buffer ($5,000)?"), css_class='form-label pt-2'),
                    Div(InlineRadios('topUpBuffer'))),

                css_class="col-lg-5"),



        css_class='row')
    )

    def clean_topUpIncomeAmount(self):
        amount = self.cleaned_data['topUpIncomeAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")


class careDrawdownForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['careRegularAmount', 'careFrequency', 'carePeriod', 'careDrawdownDescription']

    # Form Fields
    careRegularAmount = forms.CharField(required=True, localize=True, widget=widgets.TextInput())
    carePeriod = forms.ChoiceField(
        choices=(
            (1, "1 Year"),
            (3, "3 Years"),
            (5, "5 Years"),
        ),
        widget=forms.RadioSelect,
        label="")
    careFrequency = forms.ChoiceField(
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
                Div(Div(HTML("Periodic Drawdown Amount"), css_class='form-label'),
                    Div(PrependedText('careRegularAmount', '$'))),

                Div(Div(HTML("Description"), css_class='form-label'),
                    Div(Field('careDrawdownDescription'))),

                Div(Div(Submit('submit', 'Save', css_class='btn btn-warning'))),

                css_class="col-lg-5"),

            Div(
                Div(Div(HTML("Drawdown Frequency"), css_class='form-label'),
                    Div(InlineRadios('careFrequency'))),

                Div(Div(HTML("Drawdown Plan Period (years)*"), css_class='form-label'),
                    Div(InlineRadios('carePeriod'))),

                css_class="col-lg-5"),



        css_class='row')
    )

    def clean_careRegularAmount(self):
        amount = self.cleaned_data['careRegularAmount'].replace("$", "").replace(',', "")
        try:
            return int(amount)
        except:
            raise forms.ValidationError("Please enter a valid number")













class DetailedChkBoxForm(forms.ModelForm):
    # Form Data
    class Meta:
        model = Loan
        fields = ['choiceTopUp', 'choiceRefinance', 'choiceGive', 'choiceReserve', 'choiceLive', 'choiceCare',
                  'choiceFuture',
                  'choiceCenterlink', 'choiceVariable']

    CHOICES = ((True, u'Yes'),
               (False, u'No'))

    # Form Fields
    choiceTopUp = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                    label='I would like to top-up my income or superannuation/investments', required=True)

    choiceRefinance = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                        label='I would like to refinance an existing mortgage', required=True)

    choiceGive = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                   label='I would like to give money to others', required=True)

    choiceReserve = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                      label='I would like to reserve some equity in my home', required=True)

    choiceLive = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                   label='I would like money for renovations, transport or travel', required=True)

    choiceCare = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                   label='I would like money to fund health or care requirements', required=True)

    choiceFuture = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                     label='* I understand that I will need to consider future age care', required=True)

    choiceCenterlink = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                         label='* I understand that I will need to consider impacts on my Centrelink benefits',
                                         required=True)

    choiceVariable = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                       label='* I  understand that a Household Loan has a variable interest rate',
                                       required=True)

    # Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.label_class = 'col-lg-9'
    helper.field_class = 'col-lg-3'
    helper.layout = Layout(
        Div(
            Div(
                InlineRadios('choiceTopUp')),
            Div(
                InlineRadios('choiceRefinance')),
            Div(
                InlineRadios('choiceGive')),
            Div(
                InlineRadios('choiceReserve')),
            Div(
                InlineRadios('choiceLive')),
            Div(
                InlineRadios('choiceCare')),
            Div(
                InlineRadios('choiceFuture')),
            Div(
                InlineRadios('choiceCenterlink')),
            Div(
                InlineRadios('choiceVariable')),
            css_class='narrow-row small'
        )
    )

    def clean_choiceVariable(self):
        if self.cleaned_data['choiceVariable'] != "True":
            raise forms.ValidationError("Please acknowledge Interest Rate notice")
        return self.cleaned_data['choiceVariable']

    def clean_choiceFuture(self):
        if self.cleaned_data['choiceFuture'] != "True":
            raise forms.ValidationError("Please acknowledge Future Care Needs notice")
        return self.cleaned_data['choiceFuture']

    def clean_choiceCenterlink(self):
        if self.cleaned_data['choiceCenterlink'] != "True":
            raise forms.ValidationError("Please acknowledge Centerlink Benefits notice")
        return self.cleaned_data['choiceCenterlink']
