#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Enquiry, MarketingCampaign
# Model registration to enable maintenance in the Admin screens


class EnquiryAdmin(admin.ModelAdmin):
    search_fields = [
        'firstname',
        'lastname',
        'email',
        'phoneNumber'
    ]
    
# admin.site.register(Enquiry,EnquiryAdmin)
admin.site.register(Enquiry, EnquiryAdmin)
admin.site.register(MarketingCampaign)