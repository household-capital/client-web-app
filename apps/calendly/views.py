# Python Imports
from datetime import timedelta
import os
import json

# Third-party Imports
from config.celery import app

# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import dateparse
from django.utils import timezone


from django.views.generic import View,  ListView
from django.views.decorators.csrf import csrf_exempt


# Local Application Imports
from apps.lib.site_Logging import write_applog
from apps.lib.api_Zoom import apiZoom
from apps.lib.site_Utilities import raiseAdminError, cleanPhoneNumber
from apps.lib.site_EmailUtils import sendTemplateEmail
from apps.case.models import Case
from apps.lib.site_Enums import enquiryStagesEnum
from apps.enquiry.note_utils import add_enquiry_note
from apps.case.note_utils import add_case_note
from .models import Calendly
from urllib.parse import urljoin

# UNAUTHENTICATED VIEWS

@method_decorator(csrf_exempt, name='dispatch')
class CalendlyWebhook(View):

    def post(self, request, *args, **kwargs):

        zoom_meeting_set = {'zoom'}
        tracked_meeting_set = {'discovery', 'callback', 'phone'}

        #Get webhook ID from environmental settings
        calendly_webhook_id = os.getenv("CALENDLY_WEBHOOK_ID")

        # Check the webhook ID header (security)
        if 'HTTP_X_CALENDLY_HOOK_ID' not in request.META:
            write_applog("ERROR", 'Calendly', 'post', "No X_CALENDLY_HOOK_ID in request header" )
            return HttpResponse(status=403)

        if request.META['HTTP_X_CALENDLY_HOOK_ID'] != calendly_webhook_id:
            write_applog("ERROR", 'Calendly', 'post', "Unrecognised X_CALENDLY_HOOK_ID in header" )
            return HttpResponse(status=401)

        # Load the event data from JSON
        data = json.loads(request.body)

        # Determine event type

        hook_event = data["event"]
        meeting_name = data["payload"]["event_type"]["name"]
        meeting_set = set(meeting_name.lower().split())
        calendlyID = data['payload']["event"]["uuid"]
        user_email = data['payload']["event"]["extended_assigned_to"][0]['email']
        start_time = data['payload']["event"]["start_time"]
        start_time_pretty = data['payload']["event"]["start_time_pretty"]
        time_zone = data['payload']["invitee"]["timezone"]
        customer_name = data["payload"]["invitee"]["name"]
        customer_email = data["payload"]["invitee"]["email"]
        customer_phone = self.getPhoneNumber(data)

        #Look up user (from email)
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            write_applog("ERROR", 'Calendly', 'post', "Not processed - unknown user: " + user_email)
            return HttpResponse(status=200)


        if meeting_set & tracked_meeting_set:

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

                case_obj = Case.objects.filter(
                    Q(deleted_on__isnull=True) &(Q(email_1__iexact=customer_email) | Q(phoneNumber_1__iexact=customer_phone))
                ).order_by("-timestamp").first()
                if case_obj:
                    obj.caseUID = case_obj.caseUID

                

                # Update enquiry object and Synch with SF
                if case_obj:
                    self.updateLead(case_obj, meeting_name, customer_phone)
                
                obj.save(should_sync=True)

                write_applog("INFO", 'Calendly', 'post', "Discovery Call Created:" + customer_email )

            elif 'canceled' in hook_event:
                qs = Calendly.objects.filter(calendlyID=calendlyID)
                if qs:
                    obj = qs.get()
                    obj.isCalendlyLive = False
                    obj.save(update_fields=['isCalendlyLive'])
                    write_applog("INFO", 'Calendly', 'post', "Discovery Call Cancelled:" + customer_email)
                else:
                    write_applog("INFO", 'Calendly', 'post', "Discovery Call Cancelled (but not found):" + customer_email)

        elif meeting_set & zoom_meeting_set:

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

                caseObj = Case.objects.filter(email_1__iexact=customer_email, deleted_on__isnull=True).order_by("-timestamp").first()

                if caseObj:
                    obj.caseUID = caseObj.caseUID

                obj.save(update_fields=['user', 'meetingName', 'startTime', 'timeZone','customerName','customerEmail',
                                        'customerPhone','caseUID', 'isZoomLive'])

                # Synch with SF
                if caseObj:
                    app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(caseObj.caseUID)})

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

                response = zoomObj.create_meeting(userZoomID, obj.meetingName,description, startDate,
                                                  timeZone, tracking_fields, False)

                if response['status'] == "Ok":
                    response_dict = json.loads(response['responseText'])
                    obj.zoomID = response_dict['id']
                    obj.save(update_fields=['zoomID'])

                    if caseObj:
                        caseObj.isZoomMeeting = True
                        add_case_note(caseObj, "[# Calendly - " + meeting_name + " #]", user=None)
                        caseObj.save(update_fields=['isZoomMeeting'])

                    write_applog("INFO", 'Calendly', 'post', "Loan Interview Zoom Created: " + customer_email)

                    # Send Email Confirmation
                    template_name = 'calendly/email/email_zoom.html'

                    subject, from_email, to, cc = "Household Capital - Meeting Details", user_email, customer_email, user_email

                    email_context = {'user_mobile':user.profile.mobile,
                                   'user_first_name':user.first_name,
                                   'user_last_name': user.last_name,
                                   'customer_name': customer_name,
                                   'meeting_id': str(obj.zoomID),
                                   'start_time':start_time_pretty}

                    email_context['absolute_url'] = urljoin(
                        settings.SITE_URL,
                        settings.STATIC_URL
                    ) 

                    emailSent = sendTemplateEmail(template_name, email_context,subject, from_email, to, cc)

                    if not emailSent:
                        write_applog("ERROR", 'Calendly', 'post', "Customer email could not be sent")

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

                    caseObj = Case.objects.filter(email_1=customer_email, deleted_on__isnull=True).order_by("-timestamp").first()
                    if caseObj:
                        caseObj.isZoomMeeting = False
                        caseObj.save(update_fields=['isZoomMeeting'])

                    write_applog("INFO", 'Calendly', 'post', "Loan Interview Zoom Cancelled:" + customer_email)

                else:
                    write_applog("INFO", 'Calendly', 'post', "Loan Interview Cancelled (but not found):" + customer_email)

        else:
            write_applog("INFO", 'Calendly', 'post',
                         "Unhandled Meeting:" + meeting_name)
            raiseAdminError("Calendly - Unhandled Meeting", "The following meeting type was not handled by the webhook" + meeting_name)

        return HttpResponse(status=200)

    def updateLead(self, obj, meeting_name, phoneNumber):
        if obj:
            add_case_note(obj, "[# Calendly - " + meeting_name + " #]", user=None)
            if phoneNumber and not obj.phoneNumber_1:
                obj.phoneNumber_1 = phoneNumber
            obj.save(update_fields=['phoneNumber'])

    def getPhoneNumber(self, data):
        phoneNumber = None
        try:
            if 'phone number' in data['payload']['questions_and_answers'][0]['question']:
                answer = data['payload']['questions_and_answers'][0]['answer']
                # strip characters and trim response (shouldn't be required, but in case Calendly field not correctly defined as phone)
                answer_digits = ''.join([c for c in answer if c in '0123456789'])
                phoneNumber = cleanPhoneNumber(answer_digits[:15])
        except:
            pass
        return phoneNumber


# //MIXINS

class LoginRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

    # Ensures views will not render unless Household employee, redirects to Landing
    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))


# //CLASS BASED VIEWS

# Case List View
class MeetingList(LoginRequiredMixin, ListView):
    paginate_by = 10
    template_name = 'calendly/meetingList.html'
    context_object_name = 'obj'
    model = Calendly
    zoomUrl= 'https://householdcapital.zoom.us/s/'
    calendlyUrl = 'https://calendly.com/app/scheduled_events/user/me'
    customerUrl = 'https://householdcapital.com.au/meeting/'

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter

        delta = timedelta(hours=8)
        windowDate = timezone.now() - delta

        queryset = super(MeetingList, self).get_queryset()

        filter = self.request.GET.get('filter')

        if filter == "ZoomGroup":
            qs = queryset.filter(startTime__gte=windowDate,
                                 isZoomLive=True,
                                 isCalendlyLive=True).order_by('startTime')

        elif filter == "CalendlyInd":
            qs = queryset.filter(startTime__gte=windowDate, isCalendlyLive=True, user=self.request.user)\
                .exclude(isZoomLive=True)\
                .order_by('startTime')

        elif filter == "CalendlyGroup":
            qs = queryset.filter(startTime__gte=windowDate, isCalendlyLive=True)\
                .exclude(isZoomLive=True)\
                .order_by('startTime')

        else:
            qs = queryset.filter(startTime__gte=windowDate, isZoomLive=True,
                                 isCalendlyLive=True, user=self.request.user).order_by('startTime')

        return qs

    def get_context_data(self, **kwargs):
        context = super(MeetingList, self).get_context_data(**kwargs)
        context['title'] = 'Scheduled Meetings'
        context['zoomUrl'] = self.zoomUrl
        context['calendlyUrl'] =  self.calendlyUrl
        context['customerUrl']  =  self.customerUrl
        context['filter'] = self.request.GET.get('filter')
        if context['filter'] == None:
            context['filter'] = "ZoomInd"

        if "Zoom" in context['filter']:
            context['isZoom'] = True

        return context