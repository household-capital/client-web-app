# Django Imports
from django import forms
from django.contrib.auth.models import User
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
                  'referrer', 'email', 'phoneNumber', 'enquiryNotes', 'referrerID',
                  'marketingSource', 'callReason']

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
                Div(
                    Div(HTML("Enquiry Source"), css_class='form-label'),
                    Div(Field('referrer'))),
                Div(
                    Div(HTML("Referral Source"), css_class='form-label'),
                    Div(Field('referrerID'))),
                Div(
                    Div(HTML("How did you hear about us?"), css_class='form-label'),
                    Div(Field('marketingSource'))),
                Div(
                    Div(HTML("Reason for call"), css_class='form-label'),
                    Div(Field('callReason'))),

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
                  'marketingSource', 'callReason',
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
                Div(
                    Div(HTML("How did you hear about us?"), css_class='form-label'),
                    Div(Field('marketingSource'))),
                 Div(
                    Div(HTML("Reason for call"), css_class='form-label'),
                    Div(Field('callReason'))),
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



class EnquiryCallForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['name', 'postcode', 'phoneNumber', 'marketingSource', 'callReason', 'enquiryNotes']

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
                    Div(HTML("Phone Number"), css_class='form-label'),
                    Div(Field('phoneNumber'))),
                Div(
                    Div(HTML("Enquiry Notes"), css_class='form-label'),
                    Div(Field('enquiryNotes'))),
                css_class='col-lg-6'),

            Div(
                Div(HTML("<i class='fas fa-headset'></i>&nbsp;&nbsp;Call details"), css_class='form-header'),
                Div(
                    Div(HTML("How did you hear about us?"), css_class='form-label'),
                    Div(Field('marketingSource'))),
                Div(
                    Div(HTML("Postcode"), css_class='form-label'),
                    Div(Field('postcode'))),
                Div(
                    Div(HTML("Reason for call"), css_class='form-label'),
                    Div(Field('callReason'))),

                Div(css_class="row"),
                Div(Div(Submit('close', 'End call', css_class='btn btn-outline-secondary'),
                        Submit('submit', 'Continue', css_class='btn btn-warning')), css_class='text-right'),
                Div(HTML("<br>")),

                css_class='col-lg-6'),

            css_class="row ")
    )

    def clean(self):
        if 'close' in self.data:
            if not self.cleaned_data['marketingSource']:
                raise ValidationError('Please select a marketing source')
            if not self.cleaned_data['callReason']:
                raise ValidationError('Please select a call reason')

        return self.cleaned_data





class EnquiryCloseForm(forms.ModelForm):
    # Form Data

    class Meta:
        model = Enquiry
        fields = ['closeReason', 'closeDate',
                  'followUpDate', 'followUpNotes',
                  'doNotMarket'
                  ]

        widgets = {
            'lossNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
            'followUpNotes': forms.Textarea(attrs={'rows': 5, 'cols': 100}),

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
                HTML("<i class='fas fa-user-times'></i>&nbsp;&nbsp;<small>Close Notes</small>"),
                Div(
                    Div(
                        Div(Div(HTML("Close Reason"), css_class='form-label'),
                            Div(Field('closeReason'))),
                    )

                ),
                Div(Div(HTML("<br>"))),
                Div(HTML("<i class='far fa-envelope pb-2'></i></i>&nbsp;&nbsp;<small>Marketing</small>"),
                    Div(
                        Div(Field('doNotMarket'), css_class="col-lg-2"),
                        Div(HTML("<p>Do Not Market</p>"), css_class="col-lg-8 pt-1 pl-0 "),
                        css_class="row "),
                    css_class='col-lg-12'),

                css_class="col-lg-6"),

            Div(
                HTML("<i class='fas fa-user-tag'></i>&nbsp;&nbsp;<small>Follow-up Required</small>"),
                Div(
                    Div(Div(HTML("Follow-up Date"), css_class='form-label'),
                        Div(Field('followUpDate'))),
                    Div(Div(HTML("Follow-up Notes"), css_class='form-label'),
                        Div(Field('followUpNotes'))),
                ),
                css_class="col-lg-6"),

            css_class='row'),

        Div((Div(Div(Submit('submit', 'Update', css_class='btn btn-warning')), css_class='text-right')

        ))
        )


class EnquiryAssignForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['user']

    def __init__(self, *args, **kwargs):
        super(EnquiryAssignForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(profile__isCreditRep=True)

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = False
    helper.layout = Layout(
        Div(
            Div(
                Div(HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Assign enquiry"),css_class='form-header'),
                Div(
                    Div(HTML("Credit Representative"), css_class='form-label'),
                    Div(Field('user' ))),
                Div(Div(Submit('submit', 'Assign', css_class='btn btn-outline-secondary')), css_class='text-right'),
                Div(HTML("<br>")),

                css_class='col-lg-6'),
            css_class="row ")
    )

    def clean(self):
        if not self.cleaned_data['user']:
            raise ValidationError("Please select Credit Representative")