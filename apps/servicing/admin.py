#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, FacilityPurposes, \
    FacilityEvents, FacilityEnquiry, FacilityAdditional


class FacilityTransactionsAdmin(admin.ModelAdmin):
    list_display = ('facility', 'transactionDate')


class FacilityAdmin(admin.ModelAdmin):
    list_display = ('sfLoanName', 'advancedAmount', 'currentBalance', 'approvedAmount', 'totalValuation', 'settlementDate')

class FacilityRolesAdmin(admin.ModelAdmin):
    list_display = ('facility', 'firstName','firstName', 'role')

class FacilityPropertyAdmin(admin.ModelAdmin):
    list_display = ('facility',)

class FacilityPropertyValAdmin(admin.ModelAdmin):
    list_display = ('property', 'valuationDate')

class FacilityPurposesAdmin(admin.ModelAdmin):
    list_display = ('facility', 'category', 'intention', 'amount')

class FacilityEventsAdmin(admin.ModelAdmin):
    list_display = ('facility', 'eventType', 'eventDate')

class FacilityEnquiryAdmin(admin.ModelAdmin):
    list_display = ('facility', 'timestamp')

class FacilityAdditionalAdmin(admin.ModelAdmin):
    list_display = ('facility', 'timestamp', 'submitted')

admin.site.register(Facility, FacilityAdmin)
admin.site.register(FacilityTransactions, FacilityTransactionsAdmin)
admin.site.register(FacilityRoles, FacilityRolesAdmin)
admin.site.register(FacilityProperty,FacilityPropertyAdmin)
admin.site.register(FacilityPropertyVal,FacilityPropertyValAdmin)
admin.site.register(FacilityPurposes,FacilityPurposesAdmin)
admin.site.register(FacilityEvents,FacilityEventsAdmin)
admin.site.register(FacilityEnquiry,FacilityEnquiryAdmin)
admin.site.register(FacilityAdditional,FacilityAdditionalAdmin)