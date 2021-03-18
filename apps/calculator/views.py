# Python Imports
import json

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.views.generic import UpdateView,  ListView, View
from django.urls import reverse_lazy, reverse

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.site_Enums import directTypesEnum, enquiryStagesEnum
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.site_Utilities import getEnquiryProjections, updateNavQueue
from apps.lib.mixins import HouseholdLoginRequiredMixin

from apps.case.helpers import should_lead_owner_update

from apps.enquiry.models import Enquiry
from .models import WebCalculator, WebContact
from .forms import WebContactDetail
from .util import  convert_calc, ProcessingError
from urllib.parse import urljoin

# AUTHENTICATED VIEWS EXPOSED VIEWS

# Calculator Queue

class CalcListView(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 6
    template_name = 'calculator/calculatorList.html'
    context_object_name = 'object_list'
    model = WebCalculator

    def get_queryset(self, **kwargs):
        queryset = super(CalcListView, self).get_queryset()

        queryset = queryset.filter(email__isnull=False, actioned=0).order_by('-timestamp')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(CalcListView, self).get_context_data(**kwargs)
        context['title'] = 'Web Calculator Queue'

        # Update Nav Queues
        updateNavQueue(self.request)

        return context


class CalcCreateEnquiry(HouseholdLoginRequiredMixin, UpdateView):
    """ This view does not render it creates and enquiry, sends an email, updates the calculator
    and redirects to the Enquiry ListView"""
    context_object_name = 'object_list'
    model = WebCalculator

    def get(self, request, *args, **kwargs):
        calc_uid = str(kwargs['uid'])
        calculator = WebCalculator.objects.queryset_byUID(str(calc_uid)).get()

        try:
            convert_calc(calculator, request.user, pause_for_dups=False)
        except ProcessingError as ex:
            messages.error(self.request, ex.args[0])
        else:
            messages.success(self.request, "Client has been emailed and enquiry created")

        return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))


# Calculator Delete View (Delete View)
class CalcDeleteView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        obj = WebCalculator.objects.filter(calcUID=kwargs['uid']).get()
        obj.actioned = -1
        obj.save(update_fields=['actioned'])
        messages.success(self.request, "Web Calculator Enquiry deleted")

        return HttpResponseRedirect(reverse_lazy('calculator:calcList'))


# Contact Queue
class ContactListView(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 10
    template_name = 'calculator/contactList.html'
    context_object_name = 'object_list'
    model = WebContact

    def get_queryset(self, **kwargs):
        queryset = super(ContactListView, self).get_queryset()

        queryset = queryset.exclude(actioned=-1).order_by('-timestamp')[:200]

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContactListView, self).get_context_data(**kwargs)
        context['title'] = 'Web Contact Queue'

        # Update Nav Queues
        updateNavQueue(self.request)

        return context


# Contact Detail View
class ContactDetailView(HouseholdLoginRequiredMixin, UpdateView):
    template_name = "calculator/contactDetail.html"
    form_class = WebContactDetail
    model = WebContact

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            queryset = WebContact.objects.queryset_byUID(str(self.kwargs['uid']))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(ContactDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Web Contact Detail'
        context['obj'] = self.get_object()
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        obj.save()

        messages.success(self.request, "Contact Updated")

        return HttpResponseRedirect(reverse_lazy('calculator:contactDetail', kwargs={'uid': str(obj.contUID)}))


class ContactActionView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            queryset = WebContact.objects.queryset_byUID(str(kwargs['uid']))
            obj = queryset.get()
            obj.actioned = 1
            obj.actionedBy = request.user
            obj.actionDate = timezone.now()
            obj.save(update_fields=['actioned', 'actionedBy', 'actionDate'])
            messages.success(self.request, "Contact marked as actioned")

        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))


# Enquiry Delete View (Delete View)
class ContactDeleteView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        obj = WebContact.objects.filter(contUID=kwargs['uid']).get()
        obj.actioned = -1
        obj.save(update_fields=['actioned'])
        messages.success(self.request, "Contact deleted")

        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))

# Convert Contact
class ContactConvertView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        contObj = WebContact.objects.filter(contUID=kwargs['uid']).get()

        #Check whether user can create enquiry
        if request.user.profile.isCreditRep:
            userRef = request.user
        else:
            userRef = None

        enquiryNotes = ''.join(filter(None,[contObj.message, chr(13), contObj.actionNotes]))

        #Create enquiry
        enq_obj = Enquiry.objects.create(
            user=userRef,
            referrer=directTypesEnum.WEB_ENQUIRY.value,
            name=contObj.name,
            email=contObj.email,
            phoneNumber=contObj.phone,
            enquiryNotes=enquiryNotes,
            submissionOrigin=contObj.submissionOrigin,
            origin_timestamp=contObj.origin_timestamp,
            origin_id=contObj.origin_id,
            requestedCallback=True
        )
        enq_obj.save()
        lead = enq_obj.case
        if should_lead_owner_update(lead):
            lead.owner = userRef
            lead.save(should_sync=True)
        # Mark contact as closed
        contObj.actioned = True
        contObj.actionedBy = request.user
        contObj.actionDate = timezone.now()
        contObj.actionNotes = ''.join(filter(None,[contObj.actionNotes, "** converted to enquiry"]))
        contObj.save(update_fields=['actioned', 'actionedBy','actionDate', 'actionNotes'])

        messages.success(self.request, "Contact converted")
        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))


