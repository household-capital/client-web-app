#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import WebCalculator

# Model registration to enable maintenance in the Admin screens
admin.site.register(WebCalculator)


