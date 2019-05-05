# Django Imports
from django import forms
from django.forms import ValidationError

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML

# Local Application Imports

from .models import Enquiry


# FORMS

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode',
                  'referrer', 'email', 'phoneNumber', 'enquiryNotes', 'referrerID']

        widgets = {
            'enquiryNotes': forms.Textarea(attrs={'rows': 9, 'cols': 50}),
        }

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False  # Hide default error messages
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Client Details</small>")),
                Div(Field('name', placeholder='Name'), css_class="form-group"),
                Div(Field('phoneNumber', placeholder='Phone Number'), css_class="form-group"),
                Div(Field('email', placeholder='Email'), css_class="form-group"),
                Div(Field('enquiryNotes', placeholder='Enquiry Notes'), css_class="form-group"),
                Div(Field('referrer', placeholder='Referrer'), css_class="form-group"),
                Div(Field('referrerID', placeholder='Referrer'), css_class="form-group"),
                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Borrower(s)</small>")),
                Div(Field('loanType', placeholder='Loan Type'), css_class="form-group"),
                Div(Field('age_1', placeholder='Age 1'), css_class="form-group"),
                Div(Field('age_2', placeholder='Age 2'), css_class="form-group"),
                Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;<small>Property</small>")),

                Div(Field('dwellingType', placeholder='Dwelling Type'), css_class="form-group"),
                Div(Field('postcode', placeholder='Enter postcode'), css_class="form-group"),
                Div(Field('valuation', placeholder='Enter valuation'), css_class="form-group"),
                Div(css_class="row"),
                Div(Submit('submit', 'Update', css_class='btn btn-warning')),
                css_class='col-lg-6'),
            css_class="row ")
    )


class ReferrerForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'postcode',
                  'email', 'phoneNumber', 'enquiryNotes']

    enquiryNotes = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 9, 'cols': 50}))
    name=forms.CharField(required=True)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False  # Hide default error messages
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Client Details</small>")),
                Div(Field('name', placeholder='Name'), css_class="form-group"),
                Div(Field('phoneNumber', placeholder='Phone Number'), css_class="form-group"),
                Div(Field('email', placeholder='Email'), css_class="form-group"),
                Div(Field('enquiryNotes', placeholder='Client notes / background'), css_class="form-group"),
                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Home owner(s)</small>")),
                Div(Field('loanType', placeholder='Loan Type'), css_class="form-group"),
                Div(Field('age_1', placeholder='Age 1'), css_class="form-group"),
                Div(Field('age_2', placeholder='Age 2'), css_class="form-group"),
                Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;<small>Home Details</small>")),

                Div(Field('dwellingType', placeholder='Home Type'), css_class="form-group"),
                Div(Field('postcode', placeholder='Enter postcode'), css_class="form-group"),
                Div(css_class="row"),
                Div(Submit('submit', 'Update', css_class='btn btn-warning')),
                css_class='col-lg-6'),
            css_class="row ")
    )


class EnquiryFollowupForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['followUpDate',
                  'referrer', 'email', 'phoneNumber', 'enquiryNotes', 'referrerID']

        widgets = {
            'enquiryNotes': forms.Textarea(attrs={'rows': 9, 'cols': 50}),
        }

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;<small>Client Details</small>")),
                Div(Field('name', placeholder='Name'), css_class="form-group"),
                Div(Field('phoneNumber', placeholder='Phone Number'), css_class="form-group"),
                Div(Field('email', placeholder='Email'), css_class="form-group"),
                Div(Field('enquiryNotes', placeholder='Enquiry Notes'), css_class="form-group"),
                Div(Field('referrer', placeholder='Referrer'), css_class="form-group"),
                Div(Field('referrerID', placeholder='Referrer'), css_class="form-group"),
                css_class='col-lg-6'),
            Div(
                Div(HTML("<i class='far fa-calendar-check fa-fw'></i>&nbsp;&nbsp;<small>Future Follow-up</small>"),css_class="form-group"),
                Div(Field('followUpDate', placeholder='Follow-up Date (if applicable)'), css_class="form-group"),
                Div(Submit('submit', 'Mark Follow-up', css_class='btn btn-warning'),css_class="form-group"),
                css_class='col-lg-6'),
            css_class="row "))
