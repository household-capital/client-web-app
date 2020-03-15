#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Case, Loan, ModelSetting, FundDetail, LossData, FundedData, FactFind, TransactionData


class FundedDataAdmin(admin.ModelAdmin):
    list_display = ('case', 'advanced', 'principal', 'approved', 'totalValuation', 'settlementDate')


# Model registration to enable maintenance in the Admin screens
admin.site.register(Case)
admin.site.register(Loan)
admin.site.register(FactFind)
admin.site.register(ModelSetting)
admin.site.register(LossData)
admin.site.register(FundDetail)
admin.site.register(TransactionData)
admin.site.register(FundedData, FundedDataAdmin)