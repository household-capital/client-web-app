
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Row, Column
from crispy_forms.bootstrap import InlineCheckboxes

from .models import GlobalSettings



# This is now redundant - its for is we want to switch to django checkboxes
class HHCInlineCheckboxes(InlineCheckboxes):
    """
    Layout object for rendering checkboxes inline::

        InlineCheckboxes('field_name')
    """
    template = "%s/layout/checkboxselectmultiple.html"



class GlobalSettingsForm(forms.ModelForm):

    class Meta:
        model = GlobalSettings
        fields = [
            'autoassignees_pre_qual',
            'autoassignees_calculators',
            'autoassignees_web_visa',
            'autoassignees_STARTS_AT_60',
            'autoassignees_CARE_ABOUT',
            'autoassignees_NATIONAL_SENIORS',
            'autoassignees_YOUR_LIFE_CHOICES',
            'autoassignees_FACEBOOK',
            'autoassignees_FACEBOOK_INTERACTIVE',
            'autoassignees_FACEBOOK_CALCULATOR',
            'autoassignees_FACEBOOK_VISA',
            'autoassignees_GOOGLE_MOBILE',
            'autoassignees_LINKEDIN',
            'autocampaigns_STARTS_AT_60',
            'autocampaigns_CARE_ABOUT',
            'autocampaigns_NATIONAL_SENIORS',
            'autocampaigns_YOUR_LIFE_CHOICES',
            'autocampaigns_FACEBOOK',
            'autocampaigns_LINKEDIN',
        ]

    helper = FormHelper()
    helper.form_method = 'POST'
    helper.field_class = 'col-lg-12'
    helper.form_class = 'form-horizontal'
    helper.form_show_labels = False
    helper.form_show_errors = True
    helper.layout = Layout(
        Div(
            Div(
                Div(
                    Div(Submit('submit', 'Save', css_class='btn btn-outline-secondary')),
                    css_class='text-right'
                ),
                css_class='col-lg-12'
            ),
            Div(
                Div(
                    HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Auto Assignment of Enquiries"),
                    css_class='form-header mb-3 border-bottom'
                ),
                Div(
                    Div(HTML("Web Calculators:"), css_class='form-label pb-1'),
                    Div(
                        Field('autoassignees_calculators'),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                Div(
                    Div(HTML("Web Pre Qual:"), css_class='form-label pb-1'),
                    Div(
                        Field('autoassignees_pre_qual'),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                Div(
                    Div(HTML("Web Visa:"), css_class='form-label pb-1'),
                    Div(
                        Field('autoassignees_web_visa'),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                Div(
                    Div(HTML("Partner Channels:"), css_class='form-label pb-1'),
                    Div(
                        Div(
                            Div(HTML("Starts at 60:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_STARTS_AT_60'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Google ads mobile:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_GOOGLE_MOBILE'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Care About:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_CARE_ABOUT'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("National Seniors:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_NATIONAL_SENIORS'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Your  Life Choices:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_YOUR_LIFE_CHOICES'), css_class='pb-3')
                        ),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                Div(
                    Div(HTML("Social Channels:"), css_class='form-label pb-1'),
                    Div(
                        Div(
                            Div(HTML("Facebook:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_FACEBOOK'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Facebook Interactive:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_FACEBOOK_INTERACTIVE'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Facebook Calculator:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_FACEBOOK_CALCULATOR'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Facebook VISA:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_FACEBOOK_VISA'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("LinkedIn:"), css_class='form-label pb-1'),
                            Div(Field('autoassignees_LINKEDIN'), css_class='pb-3')
                        ),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                css_class='col-lg-10'
            ),
            Div(
                HTML('<hr/>'),
                Div(
                    HTML("<i class='fas fa-user-friends'></i>&nbsp;&nbsp;Auto Campaigns for Enquiries"),
                    css_class='form-header mb-3 border-bottom'
                ),
                Div(
                    Div(HTML("Partner Channels:"), css_class='form-label pb-1'),
                    Div(
                        Div(
                            Div(HTML("Starts at 60:"), css_class='form-label pb-1'),
                            Div(Field('autocampaigns_STARTS_AT_60'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Care About:"), css_class='form-label pb-1'),
                            Div(Field('autocampaigns_CARE_ABOUT'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("National Seniors:"), css_class='form-label pb-1'),
                            Div(Field('autocampaigns_NATIONAL_SENIORS'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Your  Life Choices:"), css_class='form-label pb-1'),
                            Div(Field('autocampaigns_YOUR_LIFE_CHOICES'), css_class='pb-3')
                        ),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                Div(
                    Div(HTML("Social Channels:"), css_class='form-label pb-1'),
                    Div(
                        Div(
                            Div(HTML("Facebook:"), css_class='form-label pb-1'),
                            Div(Field('autocampaigns_FACEBOOK'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("LinkedIn:"), css_class='form-label pb-1'),
                            Div(Field('autocampaigns_LINKEDIN'), css_class='pb-3')
                        ),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                css_class='col-lg-10'
            ),
            css_class="row"
        )
    )
