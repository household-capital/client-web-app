#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Enquiry, MarketingCampaign
# Model registration to enable maintenance in the Admin screens


class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('user','status','age_1','age_2','postcode','maxLVR','maxLoanAmount', 'lastname', 'firstname', 'email','timestamp')


# admin.site.register(Enquiry,EnquiryAdmin)
admin.site.register(Enquiry)
admin.site.register(MarketingCampaign)