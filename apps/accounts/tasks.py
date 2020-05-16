# Python Imports
import json
import base64

# Django Imports
from django.conf import settings
from django.contrib.sessions.models import Session

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.site_Logging import write_applog


@app.task(name="Clear_Session_Data")
def clearSessionData():
    # Clears session data and logs-out users
    write_applog("Info", 'Accounts', 'Tasks-clearSessionData', "Creating all session data")
    Session.objects.all().delete()
    return "Finished - Successfully"

