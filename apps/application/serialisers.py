'''API model serialisers'''
# Defines model serialisers for API using Django Rest Framework (analogous to Django Forms)


# Django Imports
from rest_framework import serializers

# Local Import
from .models import Application


class IncomeApplicationSeraliser(serializers.ModelSerializer):
    class Meta:
        model=Application
        fields=[ 'productType', 'loanType','age_1', 'age_2', 'dwellingType', 'valuation',
                'streetAddress', 'suburb', 'state', 'postcode'
                 ]
