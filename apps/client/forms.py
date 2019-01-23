from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML
from crispy_forms.bootstrap import (PrependedText, InlineCheckboxes,PrependedAppendedText, FormActions)

from django import forms


class ClientDetailsForm(forms.Form):

    CLIENT = (
        ('Murray - Neutral Bay', u"Murray - Neutral Bay"),
    )

    BORROWER=(('Single',u'Single'),
              ('Couple', u'Couple'))

    BUILDING=(('House',u'House'),
              ('Apartment', u'Apartment'))

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

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False  # Hide default error messages
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

    def __init__(self, *args, **kwargs):
        super(ClientDetailsForm, self).__init__(*args, **kwargs)

class SettingsForm(forms.Form):
    inflation = forms.FloatField()
    investmentReturn = forms.FloatField()
    housePriceInflation=forms.FloatField()
    interestRate=forms.FloatField()

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False  # Hide default error messages
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

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)


class IntroChkBoxForm(forms.Form):

    clientChoices = forms.MultipleChoiceField(
        choices=(
            ('clientRetireAtHome', "Retire at home"),
            ('clientAvoidDownsizing', 'Avoid downsizing'),
            ('clientAccessFunds', 'Access additional retirement funds')),
        label="",
        widget = forms.CheckboxSelectMultiple)

    helper = FormHelper()
    helper.form_id='clientForm'
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

    topUpAmount = forms.FloatField(widget = forms.HiddenInput(),initial=0)

    helper = FormHelper()
    helper.form_id = 'clientForm'
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'
    helper.field_class = 'col-lg-12'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(Field('topUpAmount')))

    def __init__(self, *args, **kwargs):
        super(topUpForm, self).__init__(*args, **kwargs)