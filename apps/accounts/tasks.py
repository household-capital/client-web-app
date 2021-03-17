# Python Imports

# Django Imports
from django.contrib.sessions.models import Session

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.site_Logging import write_applog
from apps.operational.decorators import email_admins_on_failure

@app.task(name="Clear_Session_Data")
@email_admins_on_failure(task_name="Clear_Session_Data")
def clearSessionData():
    """Task to clear all session data (and log all users out)"""
    write_applog("INFO", 'Accounts', 'Tasks-clearSessionData', "Clearing all session data")
    Session.objects.all().delete()
    return "Finished - Successfully"


