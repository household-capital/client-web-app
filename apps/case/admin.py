#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Case, Loan, ModelSetting, FundDetail, LossData, FundedData, FactFind

# Model registration to enable maintenance in the Admin screens
admin.site.register(Case)
admin.site.register(Loan)
admin.site.register(FactFind)
admin.site.register(ModelSetting)
admin.site.register(LossData)
admin.site.register(FundDetail)
admin.site.register(FundedData)