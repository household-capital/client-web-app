#Django Imports
from django.contrib import admin

#Local Application Imports
from .models import OrganisationType,Organisation, Contact

# Model registration to enable maintenance in the Admin screens
admin.site.register(OrganisationType)
admin.site.register(Organisation)
admin.site.register(Contact)