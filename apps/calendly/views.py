# Python Imports
from datetime import datetime
import os
import json

# Django Imports
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils import dateparse

from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt


# Local Application Imports
from apps.lib.site_Logging import write_applog
from apps.lib.api_Zoom import apiZoom
from apps.case.models import Case
from apps.enquiry.models import Enquiry
from .models import Calendly


@method_decorator(csrf_exempt, name='dispatch')
class CalendlyWebhook(View):

    def post(self, request, *args, **kwargs):

        # Load the event data from JSON
        data = json.loads(request.body)

        # Determine event type
        hook_event = data["event"]
        meeting_name = data["payload"]["event_type"]["name"]
        calendlyID = data['payload']["event"]["uuid"]
        user_email = data['payload']["event"]["extended_assigned_to"][0]['email']
        start_time = data['payload']["event"]["start_time"]
        time_zone = data['payload']["invitee"]["timezone"]
        user = User.objects.filter(email=user_email).first()
        customer_name = data["payload"]["invitee"]["name"]
        customer_email = data["payload"]["invitee"]["email"]
        customer_phone = phoneNumber = self.getPhoneNumber(data)

        if user_email != 'paul.murray@householdcapital.com':
            return HttpResponse(status=200)

        if "Discovery Call" in meeting_name:

            if 'created' in hook_event:
                # Create db entry (or update if exists)
                obj, created = Calendly.objects.get_or_create(calendlyID=calendlyID)
                obj.user = user
                obj.meetingName = meeting_name
                obj.startTime = dateparse.parse_datetime(start_time)
                obj.timeZone = time_zone
                obj.customerName = customer_name
                obj.customerEmail = customer_email
                obj.customerPhone = customer_phone

                enqObj = Enquiry.objects.filter(email=customer_email).order_by("-timestamp").first()
                if enqObj:
                    obj.enqUID = enqObj.enqUID

                obj.save(update_fields=['user', 'meetingName', 'startTime', 'timeZone','customerName','customerEmail',
                                        'customerPhone','enqUID'])


                write_applog("INFO", 'Calendly', 'post', "Discovery Call Created:" + customer_email )

                #Update enquiry object
                if enqObj:
                    self.updateEnquiry(enqObj, meeting_name, phoneNumber)

            elif 'canceled' in hook_event:
                qs = Calendly.objects.filter(calendlyID=calendlyID)
                if qs:
                    obj = qs.get()
                    obj.isCalendlyLive = False
                    obj.save(update_fields=['isCalendlyLive'])
                    write_applog("INFO", 'Calendly', 'post', "Discovery Call Cancelled:" + customer_email)
                else:
                    write_applog("INFO", 'Calendly', 'post', "Discovery Call Cancelled (but not found):" + customer_email)

        elif "Loan Interview" in meeting_name:

            if 'created' in hook_event:
                # Create db entry (or update if exists)
                obj, created = Calendly.objects.get_or_create(calendlyID=calendlyID)
                obj.user = user
                obj.meetingName = meeting_name
                obj.startTime = dateparse.parse_datetime(start_time)
                obj.timeZone = time_zone
                obj.customerName = customer_name
                obj.customerEmail = customer_email
                obj.customerPhone = customer_phone
                obj.isZoomLive = True

                caseObj = Case.objects.filter(email=customer_email).order_by("-timestamp").first()

                if caseObj:
                    obj.caseUID = caseObj.caseUID

                obj.save(update_fields=['user', 'meetingName', 'startTime', 'timeZone','customerName','customerEmail',
                                        'customerPhone','caseUID', 'isZoomLive'])

                write_applog("INFO", 'Calendly', 'post', "Loan Interview Created:" + customer_email )

                # Create Zoom Meeting
                zoomObj = apiZoom()
                startDate = obj.startTime.strftime('%Y-%m-%dT%H:%M:%S')
                timeZone = 'Australia/Sydney'
                userZoomID = user.profile.zoomID

                if caseObj:
                    tracking_fields = [
                        {"field": 'app_case_UUID', "value": str(caseObj.caseUID)},
                        {"field": 'case_description', "value": str(caseObj.caseDescription)},
                        {"field": 'sf_lead_id', "value": caseObj.sfLeadID}]
                    description = caseObj.caseDescription
                else:
                    tracking_fields = []
                    description = "Missing"

                if not created and obj.zoomID:
                    #Some update - cancel zoom first
                    response = zoomObj.delete_meeting(obj.zoomID)

                # Create Zoom
                response = zoomObj.create_meeting(userZoomID, obj.meetingName,description, startDate,
                                                  timeZone, tracking_fields)

                if response['status'] == "Ok":
                    response_dict = json.loads(response['responseText'])
                    obj.zoomID = response_dict['id']
                    obj.save(update_fields=['zoomID'])

                    if caseObj:
                        caseObj.isZoomMeeting = True
                        caseObj.save(update_fields=['isZoomMeeting'])

                    write_applog("INFO", 'Calendly', 'post', "Loan Interview Zoom Created: " + customer_email)

                else:
                    write_applog("ERROR", 'Calendly', 'post', "Loan Interview Zoom Not Created: " + customer_email
                                 + response['responseText'])

            elif 'canceled' in hook_event:
                qs = Calendly.objects.filter(calendlyID=calendlyID)
                if qs:
                    obj = qs.get()
                    obj.isCalendlyLive = False
                    obj.save(update_fields=['isCalendlyLive'])
                    write_applog("INFO", 'Calendly', 'post', "Loan Interview Cancelled:" + customer_email)

                    #Cancel Zoom Meeting
                    zoomObj = apiZoom()
                    response = zoomObj.delete_meeting(obj.zoomID)

                    if response['status'] == "Ok":
                        obj.isZoomLive = False
                        obj.save(update_fields=['isZoomLive'])

                    caseObj = Case.objects.filter(email=customer_email).order_by("-timestamp").first()
                    if caseObj:
                        caseObj.isZoomMeeting = False
                        caseObj.save(update_fields=['isZoomMeeting'])

                    write_applog("INFO", 'Calendly', 'post', "Loan Interview Zoom Cancelled:" + customer_email)

                else:
                    write_applog("INFO", 'Calendly', 'post', "Loan Interview Cancelled (but not found):" + customer_email)

        else:
            write_applog("INFO", 'Calendly', 'post',
                         "Unhandled Meeting:" + meeting_name)

        return HttpResponse(status=200)


    def updateEnquiry(self, obj, meeting_name, phoneNumber):
        if obj:
            if obj.enquiryNotes:
                obj.enquiryNotes += "\r\n" + "[# Calendly - " + meeting_name + " #]"
            else:
                obj.enquiryNotes = "[# Calendly - " + meeting_name + " #]"

            obj.isCalendly = True

            if phoneNumber and not obj.phoneNumber:
                obj.phoneNumber = phoneNumber

            obj.save(update_fields=['enquiryNotes', 'isCalendly', 'phoneNumber'])


    def getPhoneNumber(self, data):
        phoneNumber = None
        try:
            if 'phone number' in data['payload']['questions_and_answers'][0]['question']:
                phoneNumber = data['payload']['questions_and_answers'][0]['answer']
        except:
            pass

        return phoneNumber