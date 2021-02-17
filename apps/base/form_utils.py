from django import forms
from apps.base.model_utils import address_model_fields, hidden_form_fields

class AddressFormMixin():
    def __init__(self, *args, **kwargs):
        super(AddressFormMixin, self).__init__(*args, **kwargs)
        for field in address_model_fields:
            self.fields[field].disabled = True
        for field in hidden_form_fields: 
            self.fields[field].widget = forms.HiddenInput()
            self.fields[field].label = False