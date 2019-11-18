# Django Imports
from django.core.exceptions import ValidationError
from django import forms

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, Fieldset, Button, HTML

# Local Application Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum
from .models import WebCalculator, WebContact



class WebContactDetail(forms.ModelForm):
    class Meta:
        model = WebContact
        fields = ['name', 'email', 'phone', 'message','actionNotes']

        widgets = {'message': forms.Textarea(attrs={'rows': 9, 'cols': 50}),'actionNotes': forms.Textarea(attrs={'rows': 8, 'cols': 50}) }

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
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Client Information</small>")),
                Div(Field('name', placeholder='Enter your name'), css_class="form-group"),
                Div(Field('email', placeholder='Enter your email'), css_class="form-group"),
                Div(Field('phone', placeholder='Enter your phone number'), css_class="form-group"),
                Div(Field('message', placeholder='Tell us how me might be able to assist you'),
                    css_class="form-group"),
                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='fas fa-pencil-alt'></i>&nbsp;&nbsp;<small>Notes</small>")),
                Div(Field('actionNotes', placeholder='Enter action notes'),
                    css_class="form-group"),
                Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')),
                css_class='col-lg-6'),
        css_class="row"))


