#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import Calendly

# Model registration to enable maintenance in the Admin screens

class CalendlyAdmin(admin.ModelAdmin):
    list_display = ('customerName','customerEmail','meetingName','startTime','isCalendlyLive',
                    'isZoomLive', 'calendlyID','zoomID')

admin.site.register(Calendly,CalendlyAdmin)