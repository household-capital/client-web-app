# Django Imports
from django import forms
from django.forms import ValidationError

# Third-party Imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML

# Local Application Imports
from apps.lib.site_Enums import loanTypesEnum
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
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Client Details"),css_class='form-header'),
                Div(
                    Div(HTML("Client Name"), css_class='form-label'),
                    Div(Field('name' ))),
                Div(
                    Div(HTML("Client Phone Number"), css_class='form-label'),
                    Div(Field('phoneNumber'))),
                Div(
                    Div(HTML("Client Email"), css_class='form-label'),
                    Div(Field('email'))),
                Div(
                    Div(HTML("Enquiry Notes"), css_class='form-label'),
                    Div(Field('enquiryNotes'))),
                Div(
                    Div(HTML("Enquiry Source"), css_class='form-label'),
                    Div(Field('referrer'))),
                Div(
                    Div(HTML("Referral Source"), css_class='form-label'),
                    Div(Field('referrerID'))),
                css_class='col-lg-6'),

            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header'),
                Div(
                    Div(HTML("Single or Joint Borrowers"), css_class='form-label'),
                    Div(Field('loanType'))),
                Div(
                    Div(HTML("Age Borrower 1"), css_class='form-label'),
                    Div(Field('age_1'))),
                Div(
                    Div(HTML("Age Borrower 2"), css_class='form-label'),
                    Div(Field('age_2'))),

                Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;Property"), css_class='form-header'),
                Div(
                    Div(HTML("Dwelling Type"), css_class='form-label'),
                    Div(Field('dwellingType'))),
                Div(
                    Div(HTML("Postcode"), css_class='form-label'),
                    Div(Field('postcode'))),
                Div(
                    Div(HTML("Valuation"), css_class='form-label'),
                    Div(Field('valuation'))),

                Div(css_class="row"),
                Div(Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')), css_class='text-right'),

                css_class='col-lg-6'),

            css_class="row ")
    )


    def clean(self):
        if self.cleaned_data['loanType'] == loanTypesEnum.SINGLE_BORROWER.value and self.cleaned_data['age_2']:
            raise ValidationError("Please check - is this a single or Joint Loan? ")

        if self.cleaned_data['loanType'] == loanTypesEnum.JOINT_BORROWER.value and not self.cleaned_data['age_2']:
            raise ValidationError("Please add second borrower age ")

        return self.cleaned_data


class EnquiryDetailForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode',
                  'referrer', 'email', 'phoneNumber', 'enquiryNotes', 'referrerID', 'calcTopUp',
                  'calcRefi', 'calcLive', 'calcGive', 'calcCare']

        widgets = {
            'enquiryNotes': forms.Textarea(attrs={'rows': 9, 'cols': 50}),
        }

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Client Details"),css_class='form-header'),
                Div(
                    Div(HTML("Client Name"), css_class='form-label'),
                    Div(Field('name' ))),
                Div(
                    Div(HTML("Client Phone Number"), css_class='form-label'),
                    Div(Field('phoneNumber'))),
                Div(
                    Div(HTML("Client Email"), css_class='form-label'),
                    Div(Field('email'))),
                Div(
                    Div(HTML("Enquiry Notes"), css_class='form-label'),
                    Div(Field('enquiryNotes'))),
                Div(
                    Div(HTML("Enquiry Source"), css_class='form-label'),
                    Div(Field('referrer'))),
                Div(
                    Div(HTML("Referral Source"), css_class='form-label'),
                    Div(Field('referrerID'))),
                css_class='col-lg-6'),

            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header'),
                Div(
                    Div(HTML("Single or Joint Borrowers"), css_class='form-label'),
                    Div(Field('loanType'))),
                Div(
                    Div(HTML("Age Borrower 1"), css_class='form-label'),
                    Div(Field('age_1'))),
                Div(
                    Div(HTML("Age Borrower 2"), css_class='form-label'),
                    Div(Field('age_2'))),

                Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;Property"), css_class='form-header'),
                Div(
                    Div(HTML("Dwelling Type"), css_class='form-label'),
                    Div(Field('dwellingType'))),
                Div(
                    Div(HTML("Postcode"), css_class='form-label'),
                    Div(Field('postcode'))),
                Div(
                    Div(HTML("Valuation"), css_class='form-label'),
                    Div(Field('valuation'))),

                Div(css_class="row"),
                Div(Div(Submit('submit', 'Update', css_class='btn btn-outline-secondary')), css_class='text-right'),
                Div(HTML("<br>")),
                Div(HTML("<i class='fas fa-search-dollar'></i>&nbsp;&nbsp;Funding Requirements"), css_class='form-header'),
                Div(
                    Div(HTML("Top-Up Amount"), css_class='form-label'),
                    Div(Field('calcTopUp'))),
                Div(
                    Div(HTML("Refi Amount"), css_class='form-label'),
                    Div(Field('calcRefi'))),
                Div(
                    Div(HTML("Live Amount"), css_class='form-label'),
                    Div(Field('calcLive'))),
                Div(
                    Div(HTML("Give Amount"), css_class='form-label'),
                    Div(Field('calcGive'))),
                Div(
                    Div(HTML("Care Amount"), css_class='form-label'),
                    Div(Field('calcCare'))),
                css_class='col-lg-6'),

            css_class="row ")
    )

    def clean(self):
        if self.cleaned_data['loanType'] == loanTypesEnum.SINGLE_BORROWER.value and self.cleaned_data['age_2']:
            raise ValidationError("Please check - is this a single or Joint Loan? ")

        if self.cleaned_data['loanType'] == loanTypesEnum.JOINT_BORROWER.value and not self.cleaned_data['age_2']:
            raise ValidationError("Please add second borrower age ")

        return self.cleaned_data


class ReferrerForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'postcode',
                  'email', 'phoneNumber', 'enquiryNotes']

    enquiryNotes = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 9, 'cols': 50}))
    name = forms.CharField(required=True)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False  # Hide default error messages
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Client Details"), css_class='form-header'),
                Div(
                    Div(HTML("Client Name"), css_class='form-label'),
                    Div(Field('name'))),
                Div(
                    Div(HTML("Client Phone Number"), css_class='form-label'),
                    Div(Field('phoneNumber'))),
                Div(
                    Div(HTML("Client Email"), css_class='form-label'),
                    Div(Field('email'))),
                Div(
                    Div(HTML("Enquiry Notes"), css_class='form-label'),
                    Div(Field('enquiryNotes'))),
                css_class='col-lg-6'),

            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Borrower(s)"), css_class='form-header'),
                Div(
                    Div(HTML("Single or Joint Home Owners"), css_class='form-label'),
                    Div(Field('loanType'))),
                Div(
                    Div(HTML("Age - Home Owner 1"), css_class='form-label'),
                    Div(Field('age_1'))),
                Div(
                    Div(HTML("Age - Home Owner 2"), css_class='form-label'),
                    Div(Field('age_2'))),

                Div(HTML("<i class='fas fa-home'> </i>&nbsp;&nbsp;Home Details"), css_class='form-header'),
                Div(
                    Div(HTML("Dwelling Type"), css_class='form-label'),
                    Div(Field('dwellingType'))),
                Div(
                    Div(HTML("Postcode"), css_class='form-label'),
                    Div(Field('postcode'))),

                Div(css_class="row"),
                Div(Div(Submit('submit', 'Update', css_class='btn btn-warning')), css_class='text-right'),
                Div(HTML("<br>")),
                css_class='col-lg-6'),
            css_class="row ")
    )

    def clean(self):
        if self.cleaned_data['loanType'] == loanTypesEnum.SINGLE_BORROWER.value and self.cleaned_data['age_2']:
            raise ValidationError("Please check - is this a single or Joint Loan? ")

        if self.cleaned_data['loanType'] == loanTypesEnum.JOINT_BORROWER.value and not self.cleaned_data['age_2']:
            raise ValidationError("Please add second borrower age ")

        return self.cleaned_data


class EnquiryFollowupForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['followUpDate', 'name',
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
                Div(HTML("<i class='far fa-calendar-check fa-fw'></i>&nbsp;&nbsp;<small>Future Follow-up</small>"),
                    css_class="form-group"),
                Div(Field('followUpDate', placeholder='Follow-up Date (if applicable)'), css_class="form-group"),
                Div(Submit('submit', 'Mark Follow-up', css_class='btn btn-warning'), css_class="form-group"),
                css_class='col-lg-6'),
            css_class="row "))
