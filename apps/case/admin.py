#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Case, Loan, ModelSetting, FundDetail, LossData, FactFind, LoanPurposes, LoanApplication

class LoanPurposesAdmin(admin.ModelAdmin):
    list_display = ('loan', 'category', 'intention', 'amount')
    ordering = ('loan','category')

class CaseAdmin(admin.ModelAdmin):
    search_fields = [
        'firstname_1',
        'surname_1',
        'email_1',
        'phoneNumber_1'
    ]

# Model registration to enable maintenance in the Admin screens
admin.site.register(Case, CaseAdmin)
admin.site.register(Loan)
admin.site.register(FactFind)
admin.site.register(ModelSetting)
admin.site.register(LossData)
admin.site.register(FundDetail)
admin.site.register(LoanPurposes, LoanPurposesAdmin)
admin.site.register(LoanApplication)