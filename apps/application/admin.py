#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Application, ApplicationPurposes

# Model registration to enable maintenance in the Admin screens
admin.site.register(Application)
admin.site.register(ApplicationPurposes)
