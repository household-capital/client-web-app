
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
        fields = ['autoassignees_calculators']

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
                    Div(HTML("Web Calculators:"), css_class='form-label pb-3'),
                    Div(HHCInlineCheckboxes('autoassignees_calculators'))
                ),
                css_class='col-lg-8'
            ),
            css_class="row "
        )
    )
