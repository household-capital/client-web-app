
# Python Imports
from datetime import datetime

# Django Imports
from django import forms
from django.contrib.auth.models import User
from django.forms import ValidationError


# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML

# Local Application Imports

from .models import LowLVR


class InitiateForm(forms.ModelForm):
    class Meta:
        model = LowLVR
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super(InitiateForm, self).__init__(*args, **kwargs)

    name = forms.CharField(max_length=60, required=True)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(Div(HTML("Your Name"), css_class='form-label'),
                    Div(Field('name'))),
                Div(Div(HTML("Your Email"), css_class='form-label'),
                    Div(Field('email'))),

                Div(Div(Submit('submit', 'Start', css_class='btn btn-warning')), css_class='text-right'),
                Div(HTML("<br>")),

                css_class='col-lg-10'),
            css_class="row ")

    )

