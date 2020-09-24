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
from apps.lib.site_Utilities import raiseTaskAdminError, sendTemplateEmail

from .models import Calendly
from apps.enquiry.models import Enquiry
from apps.case.models import Case
from apps.lib.site_Enums import enquiryStagesEnum
from apps.lib.site_Utilities import chkNone


# CALENDLY TASKS

@app.task(name="Synch_Calendly_Discovery")
def synchCalendly():
    """Attempt to synch unmatched Calendly entries"""

    write_applog("INFO", 'Calendly', 'Tasks-synchCalendly', "Start synch Calendly to Enquiries/Cases")

    tracked_meeting_set = {'discovery', 'callback', 'phone'}
    zoom_meeting_set = {'zoom'}

    fromDate = timezone.now() - datetime.timedelta(days=30)
    qs = Calendly.objects.filter(startTime__gte=fromDate, isCalendlyLive=True)\
        .filter(Q(enqUID__isnull=True) | Q(caseUID__isnull=True))

    for obj in qs:

        meeting_set = set(obj.meetingName.lower().split())

        if meeting_set & tracked_meeting_set:

            if not obj.enqUID:
                enqObj = Enquiry.objects.filter(Q(email__iexact=obj.customerEmail, email__isnull=False) |
                                                Q(phoneNumber__iexact=obj.customerPhone,phoneNumber__isnull=False ))\
                    .order_by("-timestamp").first()

                if enqObj:

                    write_applog("INFO", 'Calendly', 'Tasks-synchCalendly', "Updating Enquiry -" + chkNone(enqObj.name))

                    obj.enqUID = enqObj.enqUID
                    obj.save()
                    updateEnquiry(enqObj.enqUID, obj.meetingName, obj.customerPhone)

                    if not enqObj.closeDate:
                        app.send_task('Update_SF_Lead', kwargs={'enqUID': str(enqObj.enqUID)})

        elif meeting_set & zoom_meeting_set:

            if not obj.caseUID:

                caseObj = Case.objects.filter(Q(email__iexact=obj.customerEmail, email__isnull=False) |
                                                Q(phoneNumber__iexact=obj.customerPhone, phoneNumber__isnull=False ))\
                    .order_by("-timestamp").first()

                if caseObj:
                    write_applog("INFO", 'Calendly', 'Tasks-synchCalendly', "Updating Case - "+ chkNone(caseObj.caseDescription))

                    obj.caseUID = caseObj.caseUID
                    obj.save()
                    updateCase(caseObj.caseUID, obj.meetingName, obj.customerPhone)
                    app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(caseObj.caseUID)})

    write_applog("INFO", 'Calendly', 'Tasks-synchCalendly', "Task completed successfully")

    return "Finished successfully"

def updateEnquiry(enqUID, meeting_name, phoneNumber):

    obj = Enquiry.objects.filter(enqUID=enqUID).first()

    if obj:
        if obj.enquiryNotes:
            obj.enquiryNotes += "\r\n" + "[# Calendly - " + meeting_name + " #]"
        else:
            obj.enquiryNotes = "[# Calendly - " + meeting_name + " #]"

        obj.isCalendly = True

        obj.enquiryStage = enquiryStagesEnum.DISCOVERY_MEETING.value

        if phoneNumber and not obj.phoneNumber:
            obj.phoneNumber = phoneNumber

        obj.save(update_fields=['enquiryNotes', 'isCalendly', 'phoneNumber', 'enquiryStage'])
    return

def updateCase(caseUID, meeting_name, phoneNumber):

    obj = Case.objects.filter(caseUID=caseUID).first()

    if obj:
        if obj.caseNotes:
            obj.caseNotes += "\r\n" + "[# Calendly - " + meeting_name + " #]"
        else:
            obj.caseNotes = "[# Calendly - " + meeting_name + " #]"

        obj.isZoomMeeting = True

        if phoneNumber and not obj.phoneNumber:
            obj.phoneNumber = phoneNumber

        obj.save(update_fields=['caseNotes', 'isZoomMeeting', 'phoneNumber'])
    return