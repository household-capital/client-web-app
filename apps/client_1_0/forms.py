#Django Imports
from django import forms

#Third-party Imports
from crispy_forms.bootstrap import (PrependedText, InlineCheckboxes,PrependedAppendedText, FormActions, InlineRadios)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML


# FORMS

class ClientDetailsForm(forms.Form):
    #Form Data
    CLIENT = (
        ('Murray - Neutral Bay', u"Murray - Neutral Bay"),
    )

    BORROWER=(('Single',u'Single'),
              ('Couple', u'Couple'))

    BUILDING=(('House',u'House'),
              ('Apartment', u'Apartment'))

    #Form Fields
    clientDescription = forms.ChoiceField(choices=CLIENT)
    clientSurname=forms.CharField(max_length=25)
    clientFirstname=forms.CharField(max_length=25)
    clientAge=forms.IntegerField()
    clientType = forms.ChoiceField(choices=BORROWER)
    clientStreet=forms.CharField(max_length=35)
    clientPostcode=forms.CharField(max_length=4)
    clientValuation=forms.IntegerField()
    clientBuilding=forms.ChoiceField(choices=BUILDING)
    clientMortgageDebt=forms.IntegerField()
    clientSuperName=forms.CharField(max_length=25)
    clientSuperAmount=forms.IntegerField()
    clientPension = forms.IntegerField()

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
                                    Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Borrower(s)</small>")),
                                    Div(Field('clientDescription', placeholder='Client Description')),
                                    Div(Field('clientSurname', placeholder='Client Surname')),
                                    Div(Field('clientFirstname', placeholder='Client Firstname')),
                                    Div(Field('clientAge', placeholder='Client Age')),
                                    Div(Field('clientType', placeholder='Client Type')),

                                    css_class="col-md-4"),
                                Div(
                                    Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;<small>Property</small>")),
                                    Div(Field('clientStreet', placeholder='Client Street')),
                                    Div(Field('clientPostcode', placeholder='Post Code')),
                                    Div(Field('clientBuilding', placeholder='Building Type')),
                                    Div(HTML("<i class='fas fa-tag'> </i>&nbsp;&nbsp;<small>Valuation</small>")),
                                    Div(PrependedText('clientValuation', "<i class='fas fa-dollar-sign'></i>"), placeholder='Estimated Valuation'),
                                    Div(HTML("<i class='fas fa-university'> </i>&nbsp;&nbsp;<small>Mortgage</small>")),
                                    Div(PrependedText('clientMortgageDebt', "<i class='fas fa-dollar-sign'></i>"), placeholder='Outstanding Mortgage'),
                                    css_class="col-md-4"),
                                Div(
                                    Div(HTML("<i class='fas fa-piggy-bank'> </i>&nbsp;&nbsp;<small>Superannuation</small>")),
                                    Div(Field('clientSuperName', placeholder='Super Fund Name')),
                                    Div(PrependedText('clientSuperAmount',"<i class='fas fa-dollar-sign'></i>"), placeholder='Super Amount'),
                                    Div(Div(HTML('<br>'),css_class="form-control-hidden"),css_class="form-group row"),
                                    Div(HTML("<i class='fas fa-hand-holding-usd'> </i>&nbsp;&nbsp;<small>Pension</small>")),
                                    Div(PrependedText('clientPension', "<i class='fas fa-dollar-sign'></i>"),placeholder='Pension Amount'),
                                    css_class="col-md-4"),
                                css_class='row'),
                            Div(
                                Div(
                                    HTML("<br>"),
                                    Div(Submit('submit', 'Set Client Data', css_class='btn btn-warning')),
                                    css_class="col lg-12, text-center"),
                                css_class='row')
                        )
    )



class SettingsForm(forms.Form):
    #Form Fields
    inflation = forms.FloatField()
    investmentReturn = forms.FloatField()
    housePriceInflation=forms.FloatField()
    interestRate=forms.FloatField()

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
                                    Div(HTML("<i class='fas fa-heart-rate'></i>&nbsp;&nbsp;<small>Interest Rate</small>")),
                                    Div(PrependedText('interestRate','%') ,placeholder='Interest Rate'),
                                    css_class="col-md-4"),

                                 Div(
                                    Div(HTML("<i class='fas fa-piggy-bank'></i>&nbsp;&nbsp;<small>Investment Return)</small>")),
                                    Div(PrependedText('investmentReturn', '%'), placeholder='Investment Return'),
                                    Div(HTML("<i class='fas fa-chart-line'></i>&nbsp;&nbsp;<small>Inflation</small>")),
                                    Div(PrependedText('inflation', '%'), placeholder='inflation'),
                                    css_class="col-md-4"),
                                css_class='row justify-content-md-center'),
                            Div(
                                Div(
                                    HTML("<br>"),
                                    Div(Submit('submit', 'Update Settings', css_class='btn btn-warning')),
                                    css_class="col-md-4 text-center"),
                                css_class='row justify-content-md-center')

    ))



class IntroChkBoxForm(forms.Form):
    #Form Fields
    clientChoices = forms.MultipleChoiceField(
        choices=(
            ('clientRetireAtHome', "Retire at home"),
            ('clientAvoidDownsizing', 'Avoid downsizing'),
            ('clientAccessFunds', 'Access additional retirement funds')),
        label="",
        widget = forms.CheckboxSelectMultiple)

    #Form Layout
    helper = FormHelper()
    helper.form_id='clientForm'  # Using a navigation button to submit, so form name has to be the same
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                InlineCheckboxes('clientChoices', style="background: #F9F8F5; padding: 10px;"))
        )
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



class debtRepayForm(forms.Form):
    #Form Fields
    clientMortgageDebt = forms.CharField(max_length=10)

    #Form Layout
    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(PrependedText('clientMortgageDebt','$') ))

    #Custom form validation
    def clean_clientMortgageDebt(self):
        'Check can convert to int'
        try:
            dataInput = int(self.cleaned_data['clientMortgageDebt'].replace(",", ""))
        except:
            raise forms.ValidationError("Please enter a mortgage debt amount")
        return self.cleaned_data['clientMortgageDebt'].replace(",", "")



class giveAmountForm(forms.Form):
    #Nb: Uses two helpers to creata single form

    #Form Fields
    giveAmount = forms.CharField(max_length=10, label='Give Amount',required=True)
    giveDescription=forms.CharField(max_length=40, label='Description',required=False)
    protectedEquity = forms.ChoiceField(
        choices = (
            (0, "0%"),
            (15, "5%"),
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

    #Custom Form Validation
    def clean_giveAmount(self):
        'Check can convert to int'
        try:
            dataInput = int(self.cleaned_data['giveAmount'].replace(",", ""))
        except:
            raise forms.ValidationError("Please enter a give amount")
        return self.cleaned_data['giveAmount'].replace(",", "")



class renovateAmountForm(forms.Form):
        #Form Fields
        renovateAmount = forms.CharField(max_length=10, label='Amount', required=True)
        renovateDescription = forms.CharField(max_length=40, label='Description', required=False)

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

        def clean_renovateAmount(self):
            'Check can convert to int'
            try:
                dataInput = int(self.cleaned_data['renovateAmount'].replace(",", ""))
            except:
                raise forms.ValidationError("Please enter a renovate amount")
            return self.cleaned_data['renovateAmount'].replace(",", "")



class travelAmountForm(forms.Form):
    #Form Fields
    travelAmount = forms.CharField(max_length=10, label='Amount', required=True)
    travelDescription = forms.CharField(max_length=40, label='Description', required=False)

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

    #Custom Field Validation
    def clean_travelAmount(self):
        'Check can convert to int'
        try:
            dataInput = int(self.cleaned_data['travelAmount'].replace(",", ""))
        except:
            raise forms.ValidationError("Please enter a travel amount")
        return self.cleaned_data['travelAmount'].replace(",", "")



class careAmountForm(forms.Form):
    #Form Fields
    careAmount = forms.CharField(max_length=10, label='Amount', required=True)
    careDescription = forms.CharField(max_length=40, label='Description', required=False)

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

    #Custom Form Validation
    def clean_careAmount(self):
        'Check can convert to int'
        try:
            dataInput = int(self.cleaned_data['careAmount'].replace(",", ""))
        except:
            raise forms.ValidationError("Please enter a care amount")
        return self.cleaned_data['careAmount'].replace(",", "")


class DetailedChkBoxForm(forms.Form):
    #Form Data
    CHOICES= ((True,u'Yes'),
              (False, u'No'))

    #Form Fields
    clientTopUp = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to top-up my income/superannuation',required=True)

    clientRefinance=forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to refinance an existing mortgage',required=True)


    clientGive = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to give money to others',required=True)

    clientReserve = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like to reserve some equity in my home',required=True)

    clientLive = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like money for renovations, transport or travel',required=True)

    clientCare = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(),
                                               label='I would like money to fund current aged care requirements',required=True)

    clientFuture = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                               label='I understand that I will need to consider future age care',required=True)

    clientCenterlink = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
                                               label='I understand that I will need to consider impacts on my Centerlink benefits',required=True)

    clientVariable = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect,
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
                InlineRadios('clientTopUp' )),
            Div(
                InlineRadios('clientRefinance')),
            Div(
                InlineRadios('clientGive')),
            Div(
                InlineRadios('clientReserve')),
            Div(
                InlineRadios('clientLive')),
            Div(
                InlineRadios('clientCare')),
            Div(
                InlineRadios('clientFuture')),
            Div(
                InlineRadios('clientCenterlink')),
            Div(
                InlineRadios('clientVariable')),
            css_class='narrow-row small'
        )
    )

    def clean_clientVariable(self):
        if self.cleaned_data['clientVariable']!="True":
            raise forms.ValidationError("Please acknowledge Interest Rate notice")
        return self.cleaned_data['clientVariable']

    def clean_clientFuture(self):
        if self.cleaned_data['clientFuture']!="True":
            raise forms.ValidationError("Please acknowledge Future Care Needs notice")
        return self.cleaned_data['clientFuture']

    def clean_clientCenterlink(self):
        if self.cleaned_data['clientCenterlink']!="True":
            raise forms.ValidationError("Please acknowledge Centerlink Benefits notice")
        return self.cleaned_data['clientCenterlink']


