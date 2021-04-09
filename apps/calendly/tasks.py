# Python Imports
import json
import base64
import datetime

# Django Imports
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError
from apps.lib.site_EmailUtils import sendTemplateEmail

from .models import Calendly
from apps.enquiry.models import Enquiry
from apps.case.models import Case
from apps.lib.site_Enums import enquiryStagesEnum
from apps.lib.site_Utilities import chkNone
from apps.enquiry.note_utils import add_enquiry_note
from apps.case.note_utils import add_case_note
from apps.operational.decorators import email_admins_on_failure


# CALENDLY TASKS

@app.task(name="Synch_Calendly_Discovery")
@email_admins_on_failure(task_name='Synch_Calendly_Discovery')
def synchCalendly():
    """Attempt to synch unmatched Calendly entries"""

    write_applog("INFO", 'Calendly', 'Tasks-synchCalendly', "Start synch Calendly to Enquiries/Cases")


    lead_meeting_set = { 
        'discovery', 
        'callback', 
        'phone',
        'zoom'
    } 

    fromDate = timezone.now() - datetime.timedelta(days=30)
    qs = Calendly.objects.filter(startTime__gte=fromDate, isCalendlyLive=True)\
        .filter(Q(enqUID__isnull=True) | Q(caseUID__isnull=True))

    for obj in qs:

        meeting_set = set(obj.meetingName.lower().split())
        if meeting_set & lead_meeting_set: 
            if not obj.caseUID:

                caseObj = Case.objects.filter(
                        Q(deleted_on__isnull=True) & (
                            Q(email_1__iexact=obj.customerEmail, email_1__isnull=False) |
                            Q(phoneNumber_1__iexact=obj.customerPhone, phoneNumber_1__isnull=False )
                        )
                    )\
                    .order_by("-timestamp").first()

                if caseObj:
                    write_applog("INFO", 'Calendly', 'Tasks-synchCalendly', "Updating Case - "+ chkNone(caseObj.caseDescription))

                    obj.caseUID = caseObj.caseUID
                    obj.save()
                    updateCase(caseObj.caseUID, obj.meetingName, obj.customerPhone)
                    app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(caseObj.caseUID)})

    write_applog("INFO", 'Calendly', 'Tasks-synchCalendly', "Task completed successfully")

    return "Finished successfully"


def updateCase(caseUID, meeting_name, phoneNumber):

    obj = Case.objects.filter(caseUID=caseUID, deleted_on__isnull=True).first()

    if obj:
        add_case_note(obj, "[# Calendly - " + meeting_name + " #]", user=None)
        obj.isZoomMeeting = True
        if phoneNumber and not obj.phoneNumber:
            obj.phoneNumber = phoneNumber

        obj.save(update_fields=['isZoomMeeting', 'phoneNumber'])
    return
