from django.contrib import admin

from .models import Case, Loan, ModelSetting, FundDetail

# Register your models here.

admin.site.register(Case)
admin.site.register(Loan)
admin.site.register(ModelSetting)
admin.site.register(FundDetail)
