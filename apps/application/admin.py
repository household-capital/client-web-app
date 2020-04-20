#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import LowLVR, IncomeCalculator

# Model registration to enable maintenance in the Admin screens
admin.site.register(LowLVR)
admin.site.register(IncomeCalculator)