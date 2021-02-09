from django.db import models

db_to_sf_map = {
    'base_specificity': 'unit',
    'street_number': 'streetNumber',
    'street_name': 'streetName',
    'street_type': 'streetType',
    'gnaf_id': 'gnaf_id'
}

address_model_fields = list(db_to_sf_map.keys()) 

hidden_form_fields = [
    'gnaf_id'
]

class AbstractAddressModel(models.Model): 

    class Meta:
        abstract = True
        
    base_specificity = models.CharField(max_length=20, blank=True, null=True) # Unit/Apartment/Street/lot
    street_number = models.CharField(max_length=10, blank=True, null=True) # reason why its not a int: Cater for 14A Street Name 
    street_name = models.CharField(max_length=80, blank=True, null=True)
    street_type = models.CharField(max_length=80, blank=True, null=True)
    gnaf_id = models.CharField(max_length=80, blank=True, null=True)
