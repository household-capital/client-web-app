from apps.base.model_utils import address_model_fields

class AddressFormMixin():
    def __init__(self, *args, **kwargs):
        super(AddressFormMixin, self).__init__(*args, **kwargs)
        for field in address_model_fields:
            self.fields[field].disabled = True