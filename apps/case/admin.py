from django.contrib import admin

from .models import Case, Loan, ModelSetting

# Register your models here.

admin.site.register(Case)
admin.site.register(Loan)
admin.site.register(ModelSetting)
