#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Application, ApplicationPurposes, ApplicationDocuments

class ApplicationAdmin(admin.ModelAdmin):
    """Admin view settings"""
    list_display = ('surname_1', 'email', 'appStatus', 'timestamp', 'appUID')
    ordering = ('-timestamp',)

class ApplicationDocAdmin(admin.ModelAdmin):
    """Admin view settings"""
    list_display = ('application', 'documentType', 'timestamp')


# Model registration to enable maintenance in the Admin screens
admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationPurposes)
admin.site.register(ApplicationDocuments, ApplicationDocAdmin)
