#Django Imports
from django import forms
from django.forms import widgets

#Third-party Imports
from crispy_forms.bootstrap import (PrependedText, InlineCheckboxes,PrependedAppendedText, FormActions, InlineRadios)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML

from apps.case.models import Case, Loan, ModelSetting

# FORMS

class ClientDetailsForm(forms.ModelForm):
    #Form Data

    valuation = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    mortgageDebt = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    superAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())
    pensionAmount = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())

    class Meta:
        model = Case
        fields = ['loanType',
                  'clientType1','surname_1','firstname_1','birthdate_1','age_1','sex_1',
                  'clientType2','surname_2','firstname_2','birthdate_2','age_2','sex_2',
                  'street','postcode','valuation','dwellingType','mortgageDebt','superName',
                  'superAmount','pensionType', 'pensionAmount']
        widgets = {
            'caseNotes': forms.Textarea(attrs={'rows': 6, 'cols': 100}),
        }

    #Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal col-lg-12'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
                        Div (
                            Div(Div(Submit('submit', 'Update Information', css_class='btn btn-warning'),
                                HTML("<br>"),
                                HTML("<br>"),css_class="col-lg-4")
                            ,css_class="row"),

                            Div(
                                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Loan Type</small>"),
                                    Field('loanType', placeholder='Loan Type'),
                                    HTML("<br>"),
                                    HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Client Details</small>"),
                                    Field('birthdate_1', placeholder='Birthdate'),
                                    Field('age_1', placeholder='Age'),
                                    Field('surname_1', placeholder='Surname'),
                                    Field('firstname_1', placeholder='Firstname'),
                                    Field('sex_1', placeholder='Gender'),
                                    Field('clientType1', placeholder='Client Type'),
                                    HTML("<br>"),
                                    HTML("<i class='far fa-user'></i>&nbsp;&nbsp;<small>Client Details</small>"),
                                    Field('birthdate_2', placeholder='Birthdate'),
                                    Field('age_2', placeholder='Age'),
                                    Field('surname_2', placeholder='Surname'),
                                    Field('firstname_2', placeholder='Firstname'),
                                    Field('sex_2', placeholder='Gender'),
                                    Field('clientType2', placeholder='Client Type'),
                                    css_class="col-lg-4"),
                                Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;<small>Property</small>"),
                                    Field('postcode', placeholder='Postcode'),
                                    Field('dwellingType', placeholder='Dwelling Type'),
                                    Field('street', placeholder='Street Address'),
                                    Field('valuation', placeholder='Valuation'),
                                    Field('mortgageDebt', placeholder='Existing Mortgage'),
                                    css_class="col-lg-4"),
                                Div(HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;<small>Super/Investments</small>"),
                                    Field('superName', placeholder='Super Name'),
                                    Field('superAmount', placeholder='Super Amount'),
                                    HTML("<br>"),
                                    HTML("<i class='fas fa-hand-holding-usd'></i>&nbsp;&nbsp;<small>Pension</small>"),
                                    Field('pensionAmount', placeholder='Pension Amount (per fortnight)'),
                                    Field('pensionType', placeholder='Pension Type'),
                                    css_class="col-lg-4"),
                                css_class="row")
                            ))


    def clean(self):
        loanType=self.cleaned_data['loanType']

        if loanType==0:
            if self.cleaned_data['birthdate_1']==None and self.cleaned_data['age_1']==None:
                raise forms.ValidationError("Enter age or birthdate for Borrower")

        if loanType==1:
            if self.cleaned_data['birthdate_1']==None and self.cleaned_data['age_1']==None:
                raise forms.ValidationError("Enter age or birthdate for Borrower 1")
            if self.cleaned_data['birthdate_2']==None and self.cleaned_data['age_2']==None:
                raise forms.ValidationError("Enter age or birthdate for Borrower 2")

        if self.cleaned_data['postcode']!=None:
            if self.cleaned_data['dwellingType'] == None:
                raise forms.ValidationError("Enter property type")
            if self.cleaned_data['valuation'] == None:
                raise forms.ValidationError("Enter property valuation estimate")





class SettingsForm(forms.ModelForm):
    #Form Fields
    class Meta:
        model = ModelSetting
        fields = ['housePriceInflation', 'interestRate', 'investmentRate', 'inflationRate', 'projectionAge' ]

    #Form Layout
    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
                        Div (
                            Div(
                                Div(
                                    Div(HTML("<i class='fas fa-home'></i>&nbsp;&nbsp;<small>House Price Inflation</small>")),
                                    Div(PrependedText('housePriceInflation','%'),placeholder='House Price Inflation'),
                                    Div(HTML("<i class='fas fa-chart-bar'></i>&nbsp;&nbsp;<small>Interest Rate</small>")),
                                    Div(PrependedText('interestRate','%') ,placeholder='Interest Rate'),
                                    Div(HTML("<i class='fas fa-user'></i>&nbsp;&nbsp;<small>Projection Age</small>")),
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
    #Form Fields
    choiceRetireAtHome=forms.BooleanField(label="Retire at home",required=True)
    choiceAvoidDownsizing=forms.BooleanField(label="Avoid downsizing",required=True)
    choiceAccessFunds=forms.BooleanField(label="Access additional retirement funds",required=True)

    class Meta:
        model = Loan
        fields = ['choiceRetireAtHome', 'choiceAvoidDownsizing', 'choiceAccessFunds']

    #Form Layout
    helper = FormHelper()
    helper.form_id='clientForm'  # Using a navigation button to submit, so form name has to be the same
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(Div(Field('choiceRetireAtHome'), css_class='checkbox-inline col-lg-3'),
                Div(Field('choiceAvoidDownsizing'), css_class='checkbox-inline col-lg-3'),
                Div(Field('choiceAccessFunds', css_class='checkbox-inline col-lg-5')), css_class='row justify-content-md-center'),
                style="background: #F9F8F5; padding: 5px;")
        )



class topUpForm(forms.Form):
    #Form Fields
    topUpAmount = forms.FloatField(widget = forms.HiddenInput(),initial=0)
    topUpIncome=forms.FloatField(widget = forms.HiddenInput(),initial=0)

    #Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(Field('topUpAmount'),
            Field('topUpIncome')))


class debtRepayForm(forms.ModelForm):
    #Form Fields
    class Meta:
        model = Loan
        fields = ['refinanceAmount']

    mortgageDebt = forms.IntegerField(required=False, localize=True, widget=widgets.TextInput())

    #Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(PrependedText('refinanceAmount','$') ))




class giveAmountForm(forms.ModelForm):
    #Nb: Uses two helpers to creata single form

    #Form Fields
    class Meta:
        model = Loan
        fields = ['giveAmount','giveDescription','protectedEquity']

    giveAmount = forms.CharField(max_length=10, label='Give Amount',required=True)
    giveDescription=forms.CharField(max_length=40, label='Description',required=False)
    protectedEquity = forms.ChoiceField(
        choices = (
            (0, "0%"),
            (5, "5%"),
            (10, "10%"),
            (15, "15%"),
            (20, "20%"),
        ),
        widget = forms.RadioSelect,
        label=""
    )

    #Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_tag = False
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-4'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(PrependedText('giveAmount', '$')),
            Div(Field('giveDescription'))
        )
    )

    helper1 = FormHelper()
    helper1.form_tag = False
    helper1.form_id = 'clientForm'
    helper1.form_method = 'POST'
    helper1.form_class = 'form-horizontal'
    helper1.field_class = 'col-lg-6'
    helper1.form_show_labels = False
    helper1.form_show_errors = True
    helper1.layout = Layout(
        Div(
              Div(InlineRadios('protectedEquity'))
        ))



class renovateAmountForm(forms.ModelForm):
    # Form Fields
    class Meta:
        model = Loan
        fields = ['renovateAmount','renovateDescription']
        labels = {
            "renovateAmount": "Amount",
            "renovateDescription": "Description"
        }

    renovateAmount = forms.IntegerField(required=False, localize=True,label='Amount',widget=widgets.TextInput())


    #Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-4'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(PrependedText('renovateAmount', '$')),
            Div(Field('renovateDescription'))
        )
    )


class travelAmountForm(forms.ModelForm):
    # Form Fields
    class Meta:
        model = Loan
        fields = ['travelAmount','travelDescription']
        labels = {
            "travelAmount": "Amount",
            "travelDescription": "Description"
        }

        travelAmount = forms.IntegerField(required=False, localize=True,label='Amount',widget=widgets.TextInput())

    #Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2' #Label sizing
    helper.field_class = 'col-lg-4' #Field sizing
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(PrependedText('travelAmount', '$')),
            Div(Field('travelDescription'))
        )
    )


class careAmountForm(forms.ModelForm):
    #Form Fields

    class Meta:
        model = Loan
        fields = ['careAmount','careDescription']
        labels = {
            "careAmount": "Amount",
            "careDescription": "Description"
        }

    careAmount = forms.IntegerField(required=False, localize=True,label='Amount',widget=widgets.TextInput())


    #Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-4'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(PrependedText('careAmount', '$')),
            Div(Field('careDescription'))
        )
    )


class DetailedChkBoxForm(forms.ModelForm):
    #Form Data
    class Meta:
        model = Loan
        fields = ['choiceTopUp','choiceRefinance','choiceGive','choiceReserve','choiceLive','choiceCare','choiceFuture',
                  'choiceCenterlink','choiceVariable']
    
    
    CHOICES= ((True,u'Yes'),
              (False, u'No'))

    #Form Fields
    choiceTopUp = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to top-up my income/superannuation',required=True)

    choiceRefinance=forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to refinance an existing mortgage',required=True)


    choiceGive = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to give money to others',required=True)

    choiceReserve = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to reserve some equity in my home',required=True)

    choiceLive = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like money for renovations, transport or travel',required=True)

    choiceCare = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like money to fund current aged care requirements',required=True)

    choiceFuture = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                               label='I understand that I will need to consider future age care',required=True)

    choiceCenterlink = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                               label='I understand that I will need to consider impacts on my Centrelink benefits',required=True)

    choiceVariable = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                              label='I  understand that a Household Loan has a variable interest rate',required=True)

    #Form Layout
    helper = FormHelper()
    helper.form_id='clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = True
    helper.form_show_errors = True
    helper.label_class = 'col-lg-9'
    helper.field_class = 'col-lg-3'
    helper.layout = Layout(
        Div(
            Div(
                InlineRadios('choiceTopUp' )),
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
        if self.cleaned_data['choiceVariable']!="True":
            raise forms.ValidationError("Please acknowledge Interest Rate notice")
        return self.cleaned_data['choiceVariable']

    def clean_choiceFuture(self):
        if self.cleaned_data['choiceFuture']!="True":
            raise forms.ValidationError("Please acknowledge Future Care Needs notice")
        return self.cleaned_data['choiceFuture']

    def clean_choiceCenterlink(self):
        if self.cleaned_data['choiceCenterlink']!="True":
            raise forms.ValidationError("Please acknowledge Centerlink Benefits notice")
        return self.cleaned_data['choiceCenterlink']


