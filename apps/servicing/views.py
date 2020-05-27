# Python Imports
import datetime
import json
import base64
import os
import pathlib

# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core import signing
from django.db.models import Q, F
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView, DetailView

from apps.lib.site_Logging import write_applog
from apps.lib.site_Enums import roleEnum
from apps.lib.site_Utilities import updateNavQueue, sendTemplateEmail

from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, \
    FacilityPurposes, FacilityEvents, FacilityEnquiry, FacilityAdditional

from .forms import FacilityEnquiryForm, FacilityAdditionalRequest, FacilityBorrowerForm, FacilityAdditionalConfirm


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

class SessionRequiredMixin(object):
    # Ensures any attempt to access without UID set is redirect to error view
    def dispatch(self, request, *args, **kwargs):
        if 'additionalUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('servicing:sessionError'))
        return super(SessionRequiredMixin, self).dispatch(request, *args, **kwargs)


# List View
class LoanListView(LoginRequiredMixin, ListView):
    #List view of all loans (Facility Objects)
    paginate_by = 8
    template_name = 'servicing/loanList.html'
    context_object_name = 'object_list'
    model = Facility

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = Facility.objects\
            .annotate(availableAmount = F('approvedAmount')-F('advancedAmount')) \
            .filter(settlementDate__isnull=False)

        if self.request.GET.get('filter') == "Reconciliation":
            queryset = queryset.filter(
                Q(amalReconciliation=False))

        if self.request.GET.get('filter') == "Breach":
            queryset = queryset.filter(
                Q(amalBreach=True))

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(sfLoanName__icontains = search) |
                Q(sfLoanID__icontains=search)
            )

        orderBy = ['-settlementDate']

        queryset = queryset.order_by(*orderBy)[:160]


        return queryset

    def get_context_data(self, **kwargs):
        context = super(LoanListView, self).get_context_data(**kwargs)
        context['title'] = 'Funded Loans'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        # Counts for pills in buttons
        context['recItems'] = Facility.objects.filter(amalReconciliation=False, settlementDate__isnull=False).count()
        context['breachItems'] = Facility.objects.filter(amalBreach=True, settlementDate__isnull=False).count()
        context['enquiryItems'] = FacilityEnquiry.objects.filter(actioned=False).count()

        # Update Nav Queues
        updateNavQueue(self.request)

        return context

class LoanEventList(LoginRequiredMixin, ListView):
    #List view of recent loan events
    paginate_by = 8
    template_name = 'servicing/loanEventList.html'
    context_object_name = 'object_list'
    model = Facility

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = FacilityEvents.objects.all().order_by('-eventDate')

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(facility__sfLoanName__icontains = search) |
                Q(facility__sfLoanID__icontains=search) |
                Q(facility__amalID__contains=search)
            )

        queryset=queryset.exclude(eventType = 1) ####

        return queryset[:160]

    def get_context_data(self, **kwargs):
        context = super(LoanEventList, self).get_context_data(**kwargs)
        context['title'] = 'Recent Events'

        return context

class LoanEnquiryList(LoginRequiredMixin, ListView):
    #List view of unactioned Loan Enquiries
    paginate_by = 8
    template_name = 'servicing/loanEnquiryList.html'
    context_object_name = 'object_list'
    model = FacilityEnquiry

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = FacilityEnquiry.objects.all().order_by('-timestamp')

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(facility__sfLoanName__icontains = search) |
                Q(facility__sfLoanID__icontains=search) |
                Q(facility__amalID__contains=search)
            )

        queryset=queryset.exclude(actioned = True) ####

        return queryset[:160]

    def get_context_data(self, **kwargs):
        context = super(LoanEnquiryList, self).get_context_data(**kwargs)
        context['title'] = 'Open Enquiries'

        return context


class LoanRecentEnquiryList(LoginRequiredMixin, ListView):
    #List view of recent Loan Enquiries
    paginate_by = 8
    template_name = 'servicing/loanEnquiryList.html'
    context_object_name = 'object_list'
    model = FacilityEnquiry

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = FacilityEnquiry.objects.all().order_by('-timestamp')

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(facility__sfLoanName__icontains = search) |
                Q(facility__sfLoanID__icontains=search) |
                Q(facility__amalID__contains=search) |
                Q(actionNotes__contains=search)
            )

        return queryset[:160]

    def get_context_data(self, **kwargs):
        context = super(LoanRecentEnquiryList, self).get_context_data(**kwargs)
        context['title'] = 'Recent Enquiries'

        return context


class LoanDetailView(LoginRequiredMixin, DetailView):
    # Loan Detail View
    template_name = 'servicing/loanDetail.html'
    model = FacilityPurposes
    context_object_name = "obj"

    def get_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(LoanDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Loan Details - Overview'

        # Data for event and equiry lists
        facilityObj = self.get_object()
        purposeQs = FacilityEvents.objects.filter(facility=facilityObj).order_by('-eventDate')
        context['eventList'] = purposeQs
        enquiryQs = FacilityEnquiry.objects.filter(facility=facilityObj).order_by('-timestamp')
        context['enquiryList'] = enquiryQs

        context['menuOverview'] = True
        context['facilityObj'] = facilityObj

        return context


class LoanDetailBalances(LoginRequiredMixin, DetailView):
    # Sub-menu view of Loan Balances and Transactions
    template_name = 'servicing/loanDetailBalances.html'
    model = Facility
    context_object_name = "obj"

    def get_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(LoanDetailBalances, self).get_context_data(**kwargs)
        context['title'] = 'Loan Details - Balances'

        facilityObj = self.get_object()
        transQs = FacilityTransactions.objects.filter(facility=facilityObj).order_by('-tranRef')
        context['transList']=transQs
        context['menuBalances'] = True
        context['facilityObj'] = facilityObj

        return context


class LoanDetailRoles(LoginRequiredMixin, DetailView):
    # Sub-menu view of Loan Roles/Contacts
    template_name = 'servicing/loanDetailRoles.html'
    model = Facility
    context_object_name = "obj"

    def get_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(LoanDetailRoles, self).get_context_data(**kwargs)
        context['title'] = 'Loan Details - Roles'

        facilityObj = self.get_object()
        roleQs = FacilityRoles.objects.filter(facility=facilityObj).order_by('role')
        context['roleList'] = roleQs
        context['roleEnum'] = roleEnum
        context['menuRoles'] = True
        context['facilityObj'] = facilityObj

        return context


class LoanDetailProperty(LoginRequiredMixin, DetailView):
    # Sub-menu view of Loan property details
    template_name = 'servicing/loanDetailProperty.html'
    model = FacilityProperty
    context_object_name = "obj"

    def get_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(LoanDetailProperty, self).get_context_data(**kwargs)
        context['title'] = 'Loan Details - Property'

        propertyObj = FacilityProperty.objects.filter(facility= self.get_object()).get()
        valQs = FacilityPropertyVal.objects.filter(property=propertyObj).order_by('valuationDate')
        context['valuationList'] = valQs
        context['property'] = propertyObj
        context['menuProperty'] = True
        context['facilityObj'] = self.get_object()

        return context


class LoanDetailPurposes(LoginRequiredMixin, DetailView):
    # Sub-menu view of Loan purposes
    template_name = 'servicing/loanDetailPurposes.html'
    model = FacilityPurposes
    context_object_name = "obj"

    def get_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(LoanDetailPurposes, self).get_context_data(**kwargs)
        context['title'] = 'Loan Details - Purposes'

        facilityObj = self.get_object()
        purposeQs = FacilityPurposes.objects.filter(facility=facilityObj).order_by('category')
        context['purposeList'] = purposeQs
        context['menuPurposes'] = True
        context['facilityObj'] = Facility.objects.queryset_byUID(str(self.kwargs['uid'])).get()

        return context


class LoanEnquiry(LoginRequiredMixin, CreateView):
    # Loan Action - create an enquiry
    template_name = 'servicing/loanEnquiry.html'
    model=FacilityEnquiry
    form_class = FacilityEnquiryForm

    def get_facility_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_form_kwargs(self, **kwargs):
        # add facility object to form kwargs (ussd to populate dropdown in form)
        kwargs = super(LoanEnquiry, self).get_form_kwargs(**kwargs)
        facilityUID = str(self.kwargs['uid'])
        obj = self.get_facility_object()
        kwargs.update({'facility_instance': obj})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LoanEnquiry, self).get_context_data(**kwargs)
        context['title'] = 'Loan Enquiry'
        context['facilityObj'] = self.get_facility_object()
        context['hideActions'] = True

        # Contact Details (used to autofill based on drop down - jquery)
        data=[]
        qs = FacilityRoles.objects.filter(facility=context['facilityObj'])
        for role in qs:
            phone= role.mobile if role.mobile is not None else role.phone
            data.append({"enquirer": role.firstName + " " + role.lastName + " - " + role.enumRole(), "email" : role.email, "phone" : phone })
        context['dataLookup'] = json.dumps(data)

        return context

    def form_valid(self, form):
        obj=form.save(commit=False)
        obj.facility = self.get_facility_object()
        obj.owner = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))


class LoanEnquiryUpdate(LoginRequiredMixin, UpdateView):
    #Update view for a loan enquiry
    template_name = 'servicing/loanEnquiry.html'
    model=FacilityEnquiry
    form_class = FacilityEnquiryForm

    def get_object(self, queryset=None):
        facility = self.get_facility_object()
        pk = self.kwargs['pk']
        queryset = FacilityEnquiry.objects.filter(facility=facility, id = pk)
        obj = queryset.get()
        return obj

    def get_facility_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_form_kwargs(self, **kwargs):
        # add facility object to form kwargs (ussd to populate dropdown in form)
        kwargs = super(LoanEnquiryUpdate, self).get_form_kwargs(**kwargs)
        facilityUID = str(self.kwargs['uid'])
        obj = self.get_facility_object()
        kwargs.update({'facility_instance': obj})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LoanEnquiryUpdate, self).get_context_data(**kwargs)
        context['title'] = 'Loan Enquiry'
        context['facilityObj'] = self.get_facility_object()
        context['hideActions'] = True

        # Contact Details (used to autofill based on drop down - jquery)
        data=[]
        qs = FacilityRoles.objects.filter(facility=context['facilityObj'])
        for role in qs:
            phone= role.mobile if role.mobile is not None else role.phone
            data.append({"enquirer": role.firstName + " " + role.lastName + " - " + role.enumRole(), "email" : role.email, "phone" : phone })
        context['dataLookup'] = json.dumps(data)

        return context

    def form_valid(self, form):
        obj=form.save(commit=False)
        obj.facility = self.get_facility_object()
        obj.owner = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))


class LoanAdditionalLink(LoginRequiredMixin, FormView):
    #Loan Action - Create Additional Amount email link
    form_class = FacilityBorrowerForm
    template_name = 'servicing/loanAdditional.html'

    def get(self,request, *args, **kwargs):
        maxDrawDown = self.get_max_drawdown()
        if maxDrawDown <= 0:
            messages.error(request, "There are no available funds for the client to draw")
            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': str(self.kwargs['uid'])}))

        if maxDrawDown < 500:
            messages.info(request, "Info: there is only a small balance available $ "+str(int(maxDrawDown)))

        return super(LoanAdditionalLink, self).get(self,request, *args, **kwargs)

    def get_max_drawdown(self):
        facilityObj = self.get_facility_object()
        availableLimit = facilityObj.approvedAmount - facilityObj.advancedAmount
        maxDrawdownAmount = availableLimit / (1 + facilityObj.establishmentFeeRate)
        return int(maxDrawdownAmount)

    def get_facility_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_form_kwargs(self, **kwargs):
        # add facility object to form kwargs (ussd to populate dropdown in form)
        kwargs = super(LoanAdditionalLink, self).get_form_kwargs(**kwargs)
        obj = self.get_facility_object()
        kwargs.update({'facility_instance': obj})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LoanAdditionalLink, self).get_context_data(**kwargs)
        context['title'] = 'Additional Drawdown Request'
        context['facilityObj'] = self.get_facility_object()
        context['hideActions'] = True

        # Contact Details (used to autofill based on drop down - jquery)
        data=[]
        qs = FacilityRoles.objects.filter(facility=context['facilityObj'])
        for role in qs:
            phone= role.mobile if role.mobile is not None else role.phone
            data.append({"enquirer": role.firstName + " " + role.lastName + " - " + role.enumRole(), "email" : role.email, "phone" : phone })
        context['dataLookup'] = json.dumps(data)

        return context

    def form_valid(self, form):
        roleObj = form.cleaned_data['identifiedEnquirer']
        facilityObj = self.get_facility_object()

        # Creation Additional Drawdown object
        additionalDict = {
            'facility': facilityObj,
            'identifiedRequester': roleObj,
            'requestedEmail': form.cleaned_data['contactEmail'],
            'establishmentFeeRate': facilityObj.establishmentFeeRate,
        }

        try:
            obj = FacilityAdditional.objects.create(**additionalDict)
        except:
            write_applog("ERROR", 'servicing', 'form_valid', "Additional drawdown instance not created")
            messages.error(self.request, "Additional drawdown link not sent")
            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))

        # Email Signed Link to customer
        payload = {'additionalUID':str(obj.additionalUID)}
        result = self.email_link(obj, payload)

        if result['status'] == 'Ok':
            messages.success(self.request, result['responseText'])

            #Create automated enquiry entry
            payload = {'facility': facilityObj,
                       'owner': self.request.user,
                       'identifiedEnquirer': roleObj,
                       'contactEmail': form.cleaned_data['contactEmail'] ,
                       'actionNotes': 'Additional drawdown link sent to client',
                       'actioned': True,
                       'actionedBy': self.request.user
            }

            FacilityEnquiry.objects.create(**payload)

        else:
            messages.error(self.request, result['responseText'])

        return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))

    def email_link(self, obj, payload):
        #Use signing to generate signed URL parameter
        signed_payload = signing.dumps(payload)
        signedURL = settings.SITE_URL + str(reverse_lazy('servicing:loanAdditionalValidate',  kwargs={'signed_pk':signed_payload}))

        email_template = 'servicing/email/email_additional_link.html'
        email_context = {}
        email_context['firstName'] = obj.identifiedRequester.firstName
        email_context['signedURL'] = signedURL
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        subject, from_email, to = "HHC: Additional drawdown request link", \
                                      'noreply@householdcapital.com', \
                                      [obj.requestedEmail]

        emailSent = sendTemplateEmail(email_template, email_context, subject, from_email, to)

        if emailSent:
            return {"status":"Ok", "responseText": "Additional drawdown link emailed to client" }
        else:
            write_applog("ERROR", 'servicing', 'email_link', "Additional drawdown link not sent")
            return {"status": "Error", "responseText": "Additional drawdown link not sent"}


## EXTERNALLY EXPOSED VIEWS ##

class SessionErrorView(TemplateView):
    #Error page for session errors
    template_name = 'servicing/interface/session_error.html'

    def get_context_data(self, **kwargs):
        context = super(SessionErrorView, self).get_context_data(**kwargs)
        context['title'] = 'Session Error'
        return context


class ValidationErrorView(TemplateView):
    #Error page for validation errors
    template_name = 'servicing/interface/validation_error.html'

    def get_context_data(self, **kwargs):
        context = super(ValidationErrorView, self).get_context_data(**kwargs)
        context['title'] = 'Validation Error'
        return context


class LoanAdditionalValidate(View):
    # Validate signed URL parameter

    def get(self, request, *args, **kwargs):
        signed_payload = kwargs['signed_pk']
        try:
            #Decrypt with expiry check
            payload = signing.loads(signed_payload, max_age=60 * 60 * 24 * 2)

            #Save payload (UID) to session
            request.session.update(payload)
            return HttpResponseRedirect(reverse_lazy('servicing:loanAdditionalRequest'))

        except signing.SignatureExpired:
            write_applog("INFO", 'ApplicationValidate', 'get',
                         "Expired Signature")

            return HttpResponseRedirect(reverse_lazy('servicing:validationError'))

        except signing.BadSignature:
            write_applog("ERROR", 'ApplicationValidate', 'get',
                         "BAD Signature")

            return HttpResponseRedirect(reverse_lazy('servicing:validationError'))



## SESSION VALIDATED VIEWS

class LoanAdditionalRequest(SessionRequiredMixin, UpdateView):
    '''First Page for Additional Request'''
    template_name = 'servicing/interface/additionalRequest.html'
    model = FacilityAdditional
    form_class = FacilityAdditionalRequest

    def get(self,request, *args, **kwargs):
        obj = self.get_object()
        if obj.submitted:
            return HttpResponseRedirect(reverse_lazy('servicing:loanAdditionalSubmitted'))
        return super(LoanAdditionalRequest, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        additionalUID = self.request.session['additionalUID']
        queryset = FacilityAdditional.objects.filter(additionalUID=additionalUID).get()
        return queryset

    def get_max_drawdown(self):
        #Calculate available funds that may be drawn
        obj = self.get_object()
        facilityObj = obj.facility

        availableLimit = facilityObj.approvedAmount - facilityObj.advancedAmount
        maxDrawdownAmount = availableLimit / (1 + facilityObj.establishmentFeeRate)
        return int(maxDrawdownAmount)

    def get_form_kwargs(self, **kwargs):
        # add maxDrawdownAmount to form kwargs
        kwargs = super(LoanAdditionalRequest, self).get_form_kwargs(**kwargs)

        kwargs.update({'maxDrawdownAmount': self.get_max_drawdown()})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LoanAdditionalRequest, self).get_context_data(**kwargs)
        context['title'] = 'Drawdown Request'
        context['maxDrawdownAmount'] = self.get_max_drawdown()
        context['obj'] = self.get_object()
        return context

    def form_valid(self, form):
        obj=form.save()
        obj.amountEstablishmentFee = round(obj.amountRequested * obj.establishmentFeeRate,0)
        obj.amountTotal = round(obj.amountRequested * (1+obj.establishmentFeeRate), 0)
        obj.requestedDate = timezone.now()
        obj.IP = self.request.META.get("REMOTE_ADDR")
        obj.save()

        return HttpResponseRedirect(reverse_lazy('servicing:loanAdditionalConfirm'))


class LoanAdditionalConfirm(SessionRequiredMixin, UpdateView):
    '''Second Page for Additional Request'''
    template_name = 'servicing/interface/additionalConfirm.html'
    model = FacilityAdditional
    form_class = FacilityAdditionalConfirm

    def get_object(self, queryset=None):
        additionalUID = self.request.session['additionalUID']
        queryset = FacilityAdditional.objects.filter(additionalUID=additionalUID).get()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LoanAdditionalConfirm, self).get_context_data(**kwargs)
        context['title'] = 'Drawdown Request'
        context['obj'] = self.get_object()

        return context

    def form_valid(self, form):
        obj=form.save(commit=False)
        obj.submitted=True
        obj.save()

        # Create automated event
        try:
            payload = {'facility': obj.facility,
                       'owner': obj.facility.owner,
                       'identifiedEnquirer': obj.identifiedRequester,
                       'contactEmail': obj.requestedEmail,
                       'actionNotes': 'Drawdown request received from customer and submitted for funding. Drawdown request: $ '+str(int(obj.amountTotal)),
                       'actioned': True,
                       'actionedBy': obj.facility.owner
                       }

            FacilityEnquiry.objects.create(**payload)
        except:
            pass

        return HttpResponseRedirect(reverse_lazy('servicing:loanAdditionalThankYou'))


class LoanAdditionalThankYou(SessionRequiredMixin, TemplateView):
    '''Thank You Page for Additional Request'''
    template_name = 'servicing/interface/additionalThankYou.html'

    def get_context_data(self, **kwargs):
        context = super(LoanAdditionalThankYou, self).get_context_data(**kwargs)
        context['title'] = 'Thank you'
        self.request.session.flush()
        return context


class LoanAdditionalSubmitted(SessionRequiredMixin, TemplateView):
    #Request already submitted page
    template_name = 'servicing/interface/additionalSubmitted.html'

    def get_context_data(self, **kwargs):
        context = super(LoanAdditionalSubmitted, self).get_context_data(**kwargs)
        context['title'] = 'Drawdown submitted'
        self.request.session.flush()
        return context