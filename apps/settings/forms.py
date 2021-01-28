
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Row, Column
from crispy_forms.bootstrap import InlineCheckboxes

from .models import GlobalSettings


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
            'autoassignees_calculators',
            'autoassignees_STARTS_AT_60',
            'autoassignees_CARE_ABOUT',
            'autoassignees_NATIONAL_SENIORS',
            'autoassignees_YOUR_LIFE_CHOICES',
            'autoassignees_FACEBOOK',
            'autoassignees_LINKEDIN',
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
                    Div(HHCInlineCheckboxes('autoassignees_calculators'), css_class='pb-3')
                ),
                Div(
                    Div(HTML("Partner Channels:"), css_class='form-label pb-1'),
                    Div(
                        Div(
                            Div(HTML("Starts at 60:"), css_class='form-label pb-1'),
                            Div(HHCInlineCheckboxes('autoassignees_STARTS_AT_60'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Care About:"), css_class='form-label pb-1'),
                            Div(HHCInlineCheckboxes('autoassignees_CARE_ABOUT'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("National Seniors:"), css_class='form-label pb-1'),
                            Div(HHCInlineCheckboxes('autoassignees_NATIONAL_SENIORS'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("Your  Life Choices:"), css_class='form-label pb-1'),
                            Div(HHCInlineCheckboxes('autoassignees_YOUR_LIFE_CHOICES'), css_class='pb-3')
                        ),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                Div(
                    Div(HTML("Social Channels:"), css_class='form-label pb-1'),
                    Div(
                        Div(
                            Div(HTML("Facebook:"), css_class='form-label pb-1'),
                            Div(HHCInlineCheckboxes('autoassignees_FACEBOOK'), css_class='pb-3')
                        ),
                        Div(
                            Div(HTML("LinkedIn:"), css_class='form-label pb-1'),
                            Div(HHCInlineCheckboxes('autoassignees_LINKEDIN'), css_class='pb-3')
                        ),
                        css_class='pl-5 col-lg-7'
                    )
                ),
                css_class='col-lg-10'
            ),
            css_class="row "
        )
    )
