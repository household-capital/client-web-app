from rest_framework import serializers

from apps.enquiry.models import Enquiry

class EnquirySeraliser(serializers.ModelSerializer):
    class Meta:
        model=Enquiry
        fields=['user', 'loanType', 'name', 'age_1', 'age_2', 'dwellingType', 'valuation',
                'postcode','referrer','referrerID']

