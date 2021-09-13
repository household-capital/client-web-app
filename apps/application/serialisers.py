"""
API model serialisers
    * Defines model serialisers for API using Django Rest Framework
    * Analogous to Django Forms
"""

# Django Imports
from rest_framework import serializers
from django.utils.timezone import utc

# Local Import
from .models import Application
from apps.lib.site_Enums import *

class IncomeApplicationSeraliser(serializers.ModelSerializer):
    """Serialiser to receive application POST data

    Note: serialiser does not validate field type (as a form would) therefore explicit field definitions required"""

    age_1 = serializers.IntegerField()
    age_2 = serializers.IntegerField(required=False)
    valuation = serializers.IntegerField()
    postcode = serializers.IntegerField()

    # TO DO - add these fields to the web site submission
    # submissionOrigin = serializers.CharField(source='origin', required=False)
    # origin_timestamp = serializers.DateTimeField(source='timestamp', required=False, default_timezone=utc)
    # origin_id = serializers.CharField(source='uuid', required=False)

    class Meta:
        model = Application

        fields = [
            'productType', 'loanType','age_1', 'age_2', 'dwellingType', 'valuation',
            'streetAddress', 'suburb', 'state', 'postcode',
            'submissionOrigin', 'origin_timestamp', 'origin_id',
        ]

    def validate(self, data):
        loanType = data.get('loanType')
        if loanType == loanTypesEnum.JOINT_BORROWER.value:
            if not data.get("age_2"):
                raise serializers.ValidationError('age_2 required for joint loan type')
        return data
