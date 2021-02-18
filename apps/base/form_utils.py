from django import forms
from apps.base.model_utils import hidden_form_fields

class AddressFormMixin():
    def __init__(self, *args, **kwargs):
        super(AddressFormMixin, self).__init__(*args, **kwargs)
        for field in hidden_form_fields: 
            self.fields[field].widget = forms.HiddenInput()
            self.fields[field].label = False