from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML
from crispy_forms.bootstrap import (PrependedText, PrependedAppendedText, FormActions)

from django import forms



class ValidateForm(forms.Form):

    BORROWER = (
        ('SINGLE', u"SINGLE"),
        ('COUPLE', u"COUPLE")
    )

    DWELLING=(
        ('HOUSE', u"HOUSE"),
        ('APARTMENT', u"APARTMENT")
    )

    AGE=(
        ('60','60'),
        ('61', '61'),
        ('62', '62'),
        ('63', '63'),
        ('64', '64'),
        ('65', '65'),
        ('66', '66'),
        ('67', '67'),
        ('68', '68'),
        ('69', '69'),
        ('70', '70'),
        ('71', '71'),
        ('72', '72'),
        ('73', '73'),
        ('74', '74'),
        ('75', '75'),
        ('76', '76'),
        ('77', '77'),
        ('78', '78'),
        ('79', '79'),
        ('80', '80'),
        ('81', '81'),
        ('82', '82'),
        ('83', '83'),
        ('84', '84'),
        ('85', '85'),
        ('86', '86'),
        ('87', '87'),
        ('88', '88'),
        ('89', '89')
    )


    borrower_type = forms.ChoiceField(choices=BORROWER)
    youngest_age=forms.ChoiceField(choices=AGE)
    dwelling_type = forms.ChoiceField(choices=DWELLING)
    postcode=forms.CharField(max_length=4)
    valuation = forms.CharField(max_length=10)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-11'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False  # Hide default error messages
    helper.form_show_errors = False
    helper.layout = Layout(
                        Div (
                            Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Borrower(s)</small>")),
                            Div(Field('borrower_type', placeholder='borrower_type'), css_class="form-group"),
                            Div(HTML("<small>Youngest borrower's age</small>")),
                            Div(Field('youngest_age', placeholder='youngest_age'), css_class="form-group"),
                            Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;<small>Property</small>")),


                            Div(Field('dwelling_type', placeholder='dwelling_type'), css_class="form-group"),
                            Div(Field('postcode', placeholder='Enter postcode'), css_class="form-group"),
                            Div(Field('valuation', placeholder='Enter valuation'), css_class="form-group"),
                            Div(css_class="row"),
                            Div(HTML("<br>")),
                            Div(Submit('submit', 'Check Eligibility', css_class='btn btn-warning')),
                        ))

    def __init__(self, *args, **kwargs):
        super(ValidateForm, self).__init__(*args, **kwargs)


class EmailForm(forms.Form):

    adviser_name = forms.CharField(max_length=20, required=True)
    client_reference = forms.CharField(max_length=20, required=True)
    client_name=forms.CharField(max_length=20, required=False)
    client_address=forms.CharField(max_length=50, required=False)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-11'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False  # Hide default error messages
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(Field('adviser_name', placeholder='Enter Adviser Firstname'), css_class="form-group"),
            Div(Field('client_reference', placeholder='Enter a Client Reference'), css_class="form-group"),
            Div(Field('client_name', placeholder='Client Name e.g.,Mr & Mrs Smith (optional)'), css_class="form-group"),
            Div(Field('client_address', placeholder='Client Street Address (optional)'), css_class="form-group"),

            Div(css_class="row"),
            Div(HTML("<br>")),
            Div(Submit('submit', 'Create draft email', css_class='btn btn-warning'))
        ))
    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)

