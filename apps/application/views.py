import uuid

# Django Imports
from django.conf import settings

from django.contrib import messages
from django.core.files import File
from django.core import signing
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView, View, UpdateView

# Local Application Imports
from apps.lib.site_Logging import write_applog
from .models import LowLVR
from .forms import InitiateForm
from apps.lib.site_Utilities import sendTemplateEmail

## WARNING VIEWS ARE EXTERNALLY EXPOSED OR SESSION VERIFIED ##

class SessionRequiredMixin(object):
    # Ensures any attempt to access without UID set is redirect to error view
    def dispatch(self, request, *args, **kwargs):
        if 'applicationUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('application:sessionError'))
        return super(SessionRequiredMixin, self).dispatch(request, *args, **kwargs)


## EXTERNALLY EXPOSED VIEWS

class SessionErrorView(TemplateView):
    '''Error page for session errors'''
    template_name = 'application/interface/session_error.html'

    def get_context_data(self, **kwargs):
        context = super(SessionErrorView, self).get_context_data(**kwargs)
        context['title'] = 'Session Error'
        return context

class ValidationErrorView(TemplateView):
    '''Error page for validation errors'''
    template_name = 'application/interface/validation_error.html'

    def get_context_data(self, **kwargs):
        context = super(ValidationErrorView, self).get_context_data(**kwargs)
        context['title'] = 'Validation Error'
        return context

class Validate(View):

    def get(self, request, *args, **kwargs):
        signed_payload = kwargs['signed_pk']
        try:
            payload = signing.loads(signed_payload, max_age=60 * 60 * 24 * 7)
            request.session['applicationUID'] = payload['applicationUID']
            return HttpResponseRedirect(reverse_lazy('application:introduction'))

        except signing.SignatureExpired:
            write_applog("INFO", 'ApplicationValidate', 'get',
                         "Expired Signature")

            return HttpResponseRedirect(reverse_lazy('application:validationError'))

        except signing.BadSignature:
            write_applog("ERROR", 'ApplicationValidate', 'get',
                         "BAD Signature")

            return HttpResponseRedirect(reverse_lazy('application:validationError'))


class InitiateView(FormView):
    '''Initiates Application'''
    template_name = 'application/interface/apply.html'
    model = LowLVR
    form_class = InitiateForm
    success_url = reverse_lazy('application:introduction')

    def get_context_data(self, **kwargs):
        context = super(InitiateView, self).get_context_data(**kwargs)
        context['title'] = 'On-line Application'
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        name = form.cleaned_data['name']
        obj.firstname_1, obj.surname_1 = name.split(" ", 1)
        obj.save()

        self.request.session['applicationUID'] = str(obj.applicationUID)

        self.email_link(obj)

        return super(InitiateView, self).form_valid(form)

    def email_link(self, obj):

        payload = {
            'applicationUID': str(obj.applicationUID)
        }

        signed_payload = signing.dumps(payload)
        signedURL = settings.SITE_URL + str(reverse_lazy('application:validate',  kwargs={'signed_pk':signed_payload}))

        email_template = 'application/email/email_application_link.html'
        email_context = {}
        email_context['obj'] = obj
        email_context['signedURL'] = signedURL
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        subject, from_email, to = "Application Link", \
                                      'noreply@householdcapital.com', \
                                      [obj.email]

        emailSent = sendTemplateEmail(email_template, email_context, subject, from_email, to)
        if emailSent:
            return "Success - Application email link sent"
        else:
            write_applog("ERROR", 'application', 'email_link', "Application email link not sent")
            return "Error - reminder email could not be sent"


## SESSION VALIDATED VIEWS

class IntroductionView(SessionRequiredMixin, TemplateView):
    '''Error page for validation errors'''
    template_name = 'application/interface/introduction.html'

    def get_context_data(self, **kwargs):
        context = super(IntroductionView, self).get_context_data(**kwargs)
        context['title'] = 'The journey begins....'
        obj = LowLVR.objects.filter(applicationUID=uuid.UUID(self.request.session['applicationUID'])).get()
        context['obj'] = obj
        return context