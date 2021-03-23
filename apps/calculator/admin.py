#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import WebCalculator,WebContact

class WebCalculatorAdmin(admin.ModelAdmin):
    list_display = ('status','age_1','age_2','postcode','maxLVR','maxLoanAmount', 'firstname', 'lastname', 'email','timestamp')


class WebContactAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'email', 'phone', 'timestamp','message')


# Model registration to enable maintenance in the Admin screens
admin.site.register(WebCalculator, WebCalculatorAdmin)
admin.site.register(WebContact,WebContactAdmin)


