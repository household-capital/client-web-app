# Python Imports
import datetime
import json
import base64
import os
import pathlib
import uuid

from datetime import timedelta

# Third-party Imports
from config.celery import app


# Django Imports
from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.db.models import Q, F, ExpressionWrapper, DurationField

from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView, DetailView

from apps.accounts.models import SessionLog
from apps.lib.site_Logging import write_applog
from apps.lib.site_DataMapping import mapFacilityToCase
from apps.lib.site_Enums import roleEnum, caseStagesEnum, loanTypesEnum, appTypesEnum, clientTypesEnum, \
    channelTypesEnum, facilityStatusEnum

from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.site_Utilities import HouseholdLoginRequiredMixin, updateNavQueue, sendTemplateEmail
from apps.case.utils import createLoanVariation

from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, \
    FacilityPurposes, FacilityEvents, FacilityEnquiry, FacilityAdditional, FacilityAnnual

from .forms import FacilityEnquiryForm, FacilityAdditionalRequest, FacilityBorrowerForm, \
    FacilityAdditionalConfirm, AnnualHouseholdForm, AnnualHomeForm, AnnualNeedsForm, AnnualReviewForm
from urllib.parse import urljoin

class SessionRequiredMixin(object):
    """Ensures any attempt to access without UID set is redirect to error view"""
    def dispatch(self, request, *args, **kwargs):
        if ('additionalUID' not in request.session) and ('annualUID' not in request.session):
            return HttpResponseRedirect(reverse_lazy('servicing:sessionError'))
        return super(SessionRequiredMixin, self).dispatch(request, *args, **kwargs)

# Helper
class AnnualReviewHelper(object):
    """Helper class to extend and override generic class based views"""

    def get_object(self, queryset=None):
        annualUID = self.request.session['annualUID']
        obj = FacilityAnnual.objects.filter(annualUID=annualUID).get()
        return obj

    def get_bound_data(self):
        """
        Returns form data dictionary.
            * Enables manipulation of data in case where from invalid as data returned as a string.
            * Used when manually rendering forms
        """

        form = self.get_form()
        boundData = {}
        for name, field in form.fields.items():
            boundData[name] = form[name].value()
            if boundData[name] == "True":
                boundData[name] = True
            if boundData[name] == "False":
                boundData[name] = False
        return boundData

# List View
class LoanListView(HouseholdLoginRequiredMixin, ListView):
    # List view of all loans (Facility Objects)
    paginate_by = 8
    template_name = 'servicing/loanList.html'
    context_object_name = 'object_list'
    model = Facility

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = Facility.objects \
            .annotate(availableAmount=F('approvedAmount') - F('advancedAmount')) \
            .annotate(planAddition=F('totalPlanAmount') - F('totalLoanAmount'))

        if self.request.GET.get('filter') == "Reconciliation":
            queryset = queryset.filter(
                Q(amalReconciliation=False))

        if self.request.GET.get('filter') == "Breach":
            queryset = queryset.filter(
                Q(amalBreach=True))

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(sfLoanName__icontains=search) |
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


class LoanEventList(HouseholdLoginRequiredMixin, ListView):
    """List view of recent loan events """
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
                Q(facility__sfLoanName__icontains=search) |
                Q(facility__sfLoanID__icontains=search) |
                Q(facility__amalID__contains=search)
            )

        queryset = queryset.exclude(eventType=1)  ####

        return queryset[:160]

    def get_context_data(self, **kwargs):
        context = super(LoanEventList, self).get_context_data(**kwargs)
        context['title'] = 'Recent Events'

        return context

class LoanAnnualList(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'servicing/loanAnnualList.html'
    context_object_name = 'object_list'
    model = Facility

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        futureDate = timezone.now() + timedelta(weeks=8)
        queryset = Facility.objects.filter(nextAnnualService__lte=futureDate,
                                           settlementDate__isnull=False,
                                           status=facilityStatusEnum.ACTIVE.value) \
            .annotate(availableAmount=F('approvedAmount') - F('advancedAmount')) \
            .annotate(planAddition=F('totalPlanAmount') - F('totalLoanAmount')) \
            .order_by('nextAnnualService')

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(sfLoanName__icontains=search) |
                Q(sfLoanID__icontains=search) |
                Q(amalID__contains=search)
            )

        # ...orderby.....
        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            orderBy = ['nextAnnualService']
        else:
            orderBy = [self.request.GET.get('order'), 'nextAnnualService']

        queryset = queryset.order_by(*orderBy)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(LoanAnnualList, self).get_context_data(**kwargs)
        context['title'] = 'Annual Reviews'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""


        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            context['order'] = 'nextAnnualService'
        else:
            context['order'] = self.request.GET.get('order')

        return context

class LoanAnnualCompletedList(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'servicing/loanAnnualListCompleted.html'
    context_object_name = 'object_list'
    model = Facility

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = FacilityAnnual.objects.filter(submitted=True)  \
            .annotate(availableAmount=F('facility__approvedAmount') - F('facility__advancedAmount')) \
            .annotate(planAddition=F('facility__totalPlanAmount') - F('facility__totalLoanAmount'))

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(sfLoanName__icontains=search) |
                Q(sfLoanID__icontains=search) |
                Q(amalID__contains=search)
            )

        # ...orderby.....
        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            orderBy = ['-reviewDate']
        else:
            orderBy = [self.request.GET.get('order'), '-reviewDate']

        queryset = queryset.order_by(*orderBy)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(LoanAnnualCompletedList, self).get_context_data(**kwargs)
        context['title'] = 'Completed Annual Reviews'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""


        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            context['order'] = '-reviewDate'
        else:
            context['order'] = self.request.GET.get('order')

        return context


class LoanEnquiryList(HouseholdLoginRequiredMixin, ListView):
    # List view of unactioned Loan Enquiries
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
                Q(facility__sfLoanName__icontains=search) |
                Q(facility__sfLoanID__icontains=search) |
                Q(facility__amalID__contains=search)
            )

        queryset = queryset.exclude(actioned=True)  ####

        return queryset[:160]

    def get_context_data(self, **kwargs):
        context = super(LoanEnquiryList, self).get_context_data(**kwargs)
        context['title'] = 'Open Enquiries'

        return context


class LoanRecentEnquiryList(HouseholdLoginRequiredMixin, ListView):
    # List view of recent Loan Enquiries
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
                Q(facility__sfLoanName__icontains=search) |
                Q(facility__sfLoanID__icontains=search) |
                Q(facility__amalID__contains=search) |
                Q(actionNotes__contains=search)
            )

        return queryset[:160]

    def get_context_data(self, **kwargs):
        context = super(LoanRecentEnquiryList, self).get_context_data(**kwargs)
        context['title'] = 'Recent Enquiries'

        return context


class LoanDetailView(HouseholdLoginRequiredMixin, DetailView):
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


class LoanDetailBalances(HouseholdLoginRequiredMixin, DetailView):
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
        transQs = FacilityTransactions.objects.filter(facility=facilityObj).order_by('-effectiveDate', '-tranRef')
        context['transList'] = transQs
        context['menuBalances'] = True
        context['facilityObj'] = facilityObj
        if facilityObj.establishmentFeeRate:
            context['availableFunds'] = max(facilityObj.totalLoanAmount-facilityObj.advancedAmount,0)/(1+facilityObj.establishmentFeeRate)

        return context

class LoanDetailAnnualList(HouseholdLoginRequiredMixin, DetailView):
    # Sub-menu view of Loan Annual Reviews
    template_name = 'servicing/loanDetailReviewList.html'
    model = Facility
    context_object_name = "obj"

    def get_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(LoanDetailAnnualList, self).get_context_data(**kwargs)
        context['title'] = 'Loan Details - Annual Reviews'
        context['menuAnnual'] = True

        facilityObj = self.get_object()
        objList = FacilityAnnual.objects.filter(facility=facilityObj).order_by('-reviewDate')

        context['objList'] = objList
        context['facilityObj'] = facilityObj

        return context


class LoanDetailAnnual(HouseholdLoginRequiredMixin, UpdateView):
    # Sub-menu view of Loan Balances and Transactions
    template_name = 'servicing/loanDetailReview.html'
    model = FacilityAnnual
    form_class = AnnualReviewForm
    context_object_name = "obj"

    def get_object(self, queryset=None):
        annualUID = self.kwargs['uid']
        obj = FacilityAnnual.objects.filter(annualUID=annualUID).get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(LoanDetailAnnual, self).get_context_data(**kwargs)
        context['title'] = 'Annual Review - Detail'

        obj=self.get_object()
        queryset = Facility.objects.queryset_byUID(str(obj.facility.facilityUID))
        facilityObj = queryset.get()

        context['menuAnnual'] = True
        context['facilityObj'] = facilityObj

        if facilityObj.totalPlanAmount > facilityObj.totalLoanAmount:
            messages.warning(self.request, "Note: Future Plan Amounts - loan variation required?")

        if facilityObj.advancedAmount < facilityObj.totalLoanAmount:
            messages.warning(self.request, "Note: Undrawn amounts - loan extension required?")

        return context

    def form_valid(self, form):
        obj = form.save()

        queryset = Facility.objects.queryset_byUID(str(obj.facility.facilityUID))
        facilityObj = queryset.get()

        if obj.reviewDate == facilityObj.nextAnnualService:
            facilityObj.nextAnnualService = facilityObj.nextAnnualService + timedelta(days=365)
            facilityObj.annualServiceNotification = False
            facilityObj.save()
        messages.success(self.request,"Annual Review Completed")
        return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': str(facilityObj.facilityUID)}))


class LoanDetailRoles(HouseholdLoginRequiredMixin, DetailView):
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


class LoanDetailProperty(HouseholdLoginRequiredMixin, DetailView):
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

        propertyObj = FacilityProperty.objects.filter(facility=self.get_object()).get()
        valQs = FacilityPropertyVal.objects.filter(property=propertyObj).order_by('valuationDate')
        context['valuationList'] = valQs
        context['property'] = propertyObj
        context['menuProperty'] = True
        context['facilityObj'] = self.get_object()

        return context


class LoanDetailPurposes(HouseholdLoginRequiredMixin, DetailView):
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


class LoanEnquiry(HouseholdLoginRequiredMixin, CreateView):
    # Loan Action - create an enquiry
    template_name = 'servicing/loanEnquiry.html'
    model = FacilityEnquiry
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
        data = []
        qs = FacilityRoles.objects.filter(facility=context['facilityObj'])
        for role in qs:
            phone = role.mobile if role.mobile is not None else role.phone
            data.append({"enquirer": role.firstName + " " + role.lastName + " - " + role.enumRole, "email": role.email,
                         "phone": phone})
        context['dataLookup'] = json.dumps(data)

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.facility = self.get_facility_object()
        obj.owner = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))


class LoanEnquiryUpdate(HouseholdLoginRequiredMixin, UpdateView):
    # Update view for a loan enquiry
    template_name = 'servicing/loanEnquiry.html'
    model = FacilityEnquiry
    form_class = FacilityEnquiryForm

    def get_object(self, queryset=None):
        facility = self.get_facility_object()
        pk = self.kwargs['pk']
        queryset = FacilityEnquiry.objects.filter(facility=facility, id=pk)
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
        data = []
        qs = FacilityRoles.objects.filter(facility=context['facilityObj'])
        for role in qs:
            phone = role.mobile if role.mobile is not None else role.phone
            data.append({"enquirer": role.firstName + " " + role.lastName + " - " + role.enumRole, "email": role.email,
                         "phone": phone})
        context['dataLookup'] = json.dumps(data)

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.facility = self.get_facility_object()
        obj.owner = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))


class LoanCreateVariation(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        facilityUID = str(self.kwargs['uid'])
        facilityObj = Facility.objects.queryset_byUID(facilityUID).get()

        result = createLoanVariation(facilityObj)

        if result['status'] == 'Error':
            messages.error(self.request, result['responseText'])
            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': facilityUID}))

        else:
            newCaseUID = result['data']['caseUID']

        messages.success(self.request, "This is a variation of the original loan")
        messages.success(self.request, "Update the meeting based on additional amounts")
        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': newCaseUID}))


class LoanAdditionalLink(HouseholdLoginRequiredMixin, FormView):
    # Loan Action - Create Additional Amount email link
    form_class = FacilityBorrowerForm
    template_name = 'servicing/loanAdditional.html'

    def get(self, request, *args, **kwargs):
        maxDrawDown = self.get_max_drawdown()
        if maxDrawDown <= 0:
            messages.error(request, "There are no available funds for the client to draw")
            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': str(self.kwargs['uid'])}))

        if maxDrawDown < 500:
            messages.info(request, "Info: there is only a small balance available $ " + str(int(maxDrawDown)))

        return super(LoanAdditionalLink, self).get(self, request, *args, **kwargs)

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
        context['title'] = 'Drawdown Request'
        context['facilityObj'] = self.get_facility_object()
        context['hideActions'] = True

        # Contact Details (used to autofill based on drop down - jquery)
        data = []
        qs = FacilityRoles.objects.filter(facility=context['facilityObj'])
        for role in qs:
            phone = role.mobile if role.mobile is not None else role.phone
            data.append({"contact": role.firstName + " " + role.lastName + " - " + role.enumRole, "email": role.email,
                         "phone": phone})
        context['dataLookup'] = json.dumps(data)

        return context

    def form_valid(self, form):
        roleObj = form.cleaned_data['identifiedContact']
        facilityObj = self.get_facility_object()

        # Creation Additional Drawdown object
        additionalDict = {
            'facility': facilityObj,
            'identifiedContact': roleObj,
            'contactEmail': form.cleaned_data['contactEmail'],
            'establishmentFeeRate': facilityObj.establishmentFeeRate }

        try:
            obj = FacilityAdditional.objects.create(**additionalDict)


        except:
            write_applog("ERROR", 'servicing', 'form_valid', "Additional drawdown instance not created")
            messages.error(self.request, "Additional drawdown link not sent")
            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))

        if "sendLink" in form.data:

            # Email Signed Link to customer
            payload = {'action': 'Additional',
                       'additionalUID': str(obj.additionalUID)}

            result = self.email_link(obj, payload)

            if result['status'] == 'Ok':
                messages.success(self.request, result['responseText'])

                # Create automated enquiry entry
                payload = {'facility': facilityObj,
                           'owner': self.request.user,
                           'identifiedEnquirer': roleObj,
                           'contactEmail': form.cleaned_data['contactEmail'],
                           'actionNotes': 'Additional drawdown link sent to client',
                           'actioned': True,
                           'actionedBy': self.request.user
                           }

                FacilityEnquiry.objects.create(**payload)

            else:
                messages.error(self.request, result['responseText'])

            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))

        else:
            obj.completedBy = self.request.user
            obj.save()
            payload = {'action': 'Additional',
                       'additionalUID': str(obj.additionalUID)}

            signed_payload = signing.dumps(payload)
            signedURL = urljoin(
                settings.SITE_URL,
                str(reverse_lazy('servicing:servicingValidate', kwargs={'signed_pk': signed_payload}))
            )

            messages.warning(self.request,"Completed on behalf of client")

            return HttpResponseRedirect(signedURL)


    def email_link(self, obj, payload):
        # Use signing to generate signed URL parameter
        signed_payload = signing.dumps(payload)
        signedURL = urljoin(
            settings.SITE_URL,
            str(reverse_lazy('servicing:servicingValidate', kwargs={'signed_pk': signed_payload}))
        ) 

        email_template = 'servicing/email/email_additional_link.html'
        email_context = {}
        email_context['firstName'] = obj.identifiedContact.firstName
        email_context['signedURL'] = signedURL
        email_context['absolute_url'] = urljoin(
            settings.SITE_URL,
            settings.STATIC_URL
        )
        
        subject, from_email, to = "HHC: Additional drawdown request link", \
                                  'noreply@householdcapital.com', \
                                  obj.contactEmail

        emailSent = sendTemplateEmail(email_template, email_context, subject, from_email, to)

        if emailSent:
            return {"status": "Ok", "responseText": "Additional drawdown link emailed to client"}
        else:
            write_applog("ERROR", 'servicing', 'email_link', "Additional drawdown link not sent")
            return {"status": "Error", "responseText": "Additional drawdown link not sent"}


class LoanAnnualLink(HouseholdLoginRequiredMixin, FormView):
    # Loan Action - Create Annual Review email link
    form_class = FacilityBorrowerForm
    template_name = 'servicing/loanAnnual.html'

    def get_facility_object(self, queryset=None):
        facilityUID = str(self.kwargs['uid'])
        queryset = Facility.objects.queryset_byUID(str(facilityUID))
        obj = queryset.get()
        return obj

    def get_form_kwargs(self, **kwargs):
        # add facility object to form kwargs (ussd to populate dropdown in form)
        kwargs = super(LoanAnnualLink, self).get_form_kwargs(**kwargs)
        obj = self.get_facility_object()
        kwargs.update({'facility_instance': obj})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LoanAnnualLink, self).get_context_data(**kwargs)
        context['title'] = 'Annual Review'
        context['facilityObj'] = self.get_facility_object()
        context['hideActions'] = True

        # Contact Details (used to autofill based on drop down - jquery)
        data = []
        qs = FacilityRoles.objects.filter(facility=context['facilityObj'])
        for role in qs:
            phone = role.mobile if role.mobile is not None else role.phone
            data.append({"contact": role.firstName + " " + role.lastName + " - " + role.enumRole, "email": role.email,
                         "phone": phone})
        context['dataLookup'] = json.dumps(data)

        return context

    def form_valid(self, form):
        roleObj = form.cleaned_data['identifiedContact']
        facilityObj = self.get_facility_object()

        # Creation Annual Review object

        try:
            obj, created = FacilityAnnual.objects.get_or_create(facility=facilityObj,
                                                           reviewDate = facilityObj.nextAnnualService)

            obj.identifiedContact = form.cleaned_data['identifiedContact']
            obj.contactEmail = form.cleaned_data['contactEmail']
            obj.save()

        except:
            write_applog("ERROR", 'servicing', 'form_valid', "Annual review instance not created")
            messages.error(self.request, "Annual review link not sent")
            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))

        if "sendLink" in form.data:

            # Email Signed Link to customer
            payload = {'action': 'Annual',
                       'annualUID': str(obj.annualUID)}

            result = self.email_link(obj, payload)

            if result['status'] == 'Ok':
                messages.success(self.request, result['responseText'])

            return HttpResponseRedirect(reverse_lazy('servicing:loanDetail', kwargs={'uid': self.kwargs.get('uid')}))

        else:
            obj.completedBy = self.request.user
            obj.save()
            payload = {'action': 'Annual',
                       'annualUID': str(obj.annualUID)}

            signed_payload = signing.dumps(payload)
            signedURL = urljoin(
                settings.SITE_URL,
                str(reverse_lazy('servicing:servicingValidate', kwargs={'signed_pk': signed_payload}))
            )

            messages.warning(self.request,"Completed on behalf of client")

            return HttpResponseRedirect(signedURL)


    def email_link(self, obj, payload):
        # Use signing to generate signed URL parameter
        signed_payload = signing.dumps(payload)
        signedURL = urljoin(
            settings.SITE_URL,
            str(reverse_lazy('servicing:servicingValidate', kwargs={'signed_pk': signed_payload}))
        )  

        email_template = 'servicing/email/email_annual_link.html'
        email_context = {}
        email_context['firstName'] = obj.identifiedContact.firstName
        email_context['signedURL'] = signedURL
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        subject, from_email, to = "HHC: Annual check-in", \
                                  'noreply@householdcapital.com', \
                                  obj.contactEmail

        emailSent = sendTemplateEmail(email_template, email_context, subject, from_email, to)

        if emailSent:
            return {"status": "Ok", "responseText": "Annual review link emailed to client"}
        else:
            write_applog("ERROR", 'servicing', 'email_link', "Annual review link not sent")
            return {"status": "Error", "responseText": "Annual review link not sent"}


## UNAUTHENTICATED VIEWS

class SessionErrorView(TemplateView):
    # Error page for session errors
    template_name = 'servicing/interface/session_error.html'

    def get_context_data(self, **kwargs):
        context = super(SessionErrorView, self).get_context_data(**kwargs)
        context['title'] = 'Expired session'
        return context


class ValidationErrorView(TemplateView):
    # Error page for validation errors
    template_name = 'servicing/interface/validation_error.html'

    def get_context_data(self, **kwargs):
        context = super(ValidationErrorView, self).get_context_data(**kwargs)
        context['title'] = 'Validation Error'
        return context


class ServicingValidate(View):
    # Validate signed URL parameter

    def get(self, request, *args, **kwargs):
        signed_payload = kwargs['signed_pk']
        try:
            # Decrypt with expiry check
            payload = signing.loads(signed_payload, max_age=60 * 60 * 24 * 7)

            # Save payload (UID) to session
            request.session.update(payload)

            if payload['action'] == "Additional":
                SessionLog.objects.create(
                    description="Additional Drawdown session",
                    referenceUID=uuid.UUID(payload['additionalUID'])
                )

                return HttpResponseRedirect(reverse_lazy('servicing:loanAdditionalRequest'))

            elif payload['action'] == "Annual":

                SessionLog.objects.create(
                    description="Annual Review session",
                    referenceUID=uuid.UUID(payload['annualUID'])
                )
                return HttpResponseRedirect(reverse_lazy('servicing:loanAnnualHousehold'))

            else:
                write_applog("ERROR", 'ServicingValidate', 'get', "UNKNOWN ACTION")
                return HttpResponseRedirect(reverse_lazy('servicing:validationError'))


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

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.submitted:
            return HttpResponseRedirect(reverse_lazy('servicing:loanAdditionalSubmitted'))
        return super(LoanAdditionalRequest, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        additionalUID = self.request.session['additionalUID']
        queryset = FacilityAdditional.objects.filter(additionalUID=additionalUID).get()
        return queryset

    def get_max_drawdown(self):
        # Calculate available funds that may be drawn
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
        obj = form.save()
        obj.amountEstablishmentFee = round(obj.amountRequested * obj.establishmentFeeRate, 0)
        obj.amountTotal = round(obj.amountRequested * (1 + obj.establishmentFeeRate), 0)
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
        obj = form.save(commit=False)
        obj.submitted = True
        obj.requestedIP = self.request.META['HTTP_X_REAL_IP'] if 'HTTP_X_REAL_IP' in self.request.META else None
        obj.save()

        # Create automated event

        payload = {'facility': obj.facility,
                   'owner': obj.facility.owner,
                   'identifiedEnquirer': obj.identifiedContact,
                   'contactEmail': obj.contactEmail,
                   'actionNotes': 'Drawdown request received from customer and submitted for funding. Drawdown request: $ ' + str(
                       int(obj.amountTotal)),
                   'actioned': True,
                   'actionedBy': obj.facility.owner
                   }

        FacilityEnquiry.objects.create(**payload)

        # Create SF Payment Task

        FUNDING_TEAM = '00G2P000000O09vUAC'

        description = "Customer {0} with Facility {1} and Loan ID {2} has requested:\r\n" \
            .format(obj.identifiedContact.__str__(), obj.facility.sfLoanName, obj.facility.sfLoanID)
        description += "\r\n${0} comprised of a payment of ${1} and establishment fee of ${2}\r\n" \
            .format(f'{obj.amountTotal:,.0f}', f'{obj.amountRequested:,.0f}', f'{obj.amountEstablishmentFee:,.0f}')
        description += "\r\nThis was requested on {0}".format(obj.requestedDate.strftime("%Y-%m-%d"))

        if obj.completedBy:
            description += "\r\nThis was requested by {0} on behalf of the client".format(obj.completedBy.username)

        payload = {'OwnerId' : FUNDING_TEAM,
                   'ActivityDate' : datetime.datetime.now().strftime("%Y-%m-%d"),
                   'Subject' : 'Drawdown Request - ' + obj.facility.sfLoanID,
                   'Description' : description,
                   'Priority': 'High',
                   'WhatId' : obj.facility.sfID,
                   'WhoId' : obj.identifiedContact.sfContactID }

        app.send_task('SF_Create_Task', kwargs={'payload': payload})

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
    # Request already submitted page
    template_name = 'servicing/interface/additionalSubmitted.html'

    def get_context_data(self, **kwargs):
        context = super(LoanAdditionalSubmitted, self).get_context_data(**kwargs)
        context['title'] = 'Drawdown submitted'
        self.request.session.flush()
        return context


class LoanAnnualHousehold(SessionRequiredMixin, AnnualReviewHelper, UpdateView):
    # Annual Review start page
    template_name = 'servicing/interface/annualHousehold.html'
    form_class = AnnualHouseholdForm
    success_url = reverse_lazy('servicing:loanAnnualHome')

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.submitted:
            return HttpResponseRedirect(reverse_lazy('servicing:loanAnnualSubmitted'))
        return super(LoanAnnualHousehold, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LoanAnnualHousehold, self).get_context_data(**kwargs)
        context['title'] = 'Annual Review'

        context['menuBarItems'] = {"data": [
            {"button": True,
             "text": " Next ",
             "href": '',
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        obj= self.get_object()
        context['obj'] = obj
        roleQs = FacilityRoles.objects.filter(facility=obj.facility)\
            .filter(role__in=[roleEnum.BORROWER.value, roleEnum.PRINCIPAL_BORROWER.value, roleEnum.SECONDARY_BORROWER.value, roleEnum.NOMINATED_OCCUPANT.value, roleEnum.PERMITTED_COHABITANT.value])\
            .order_by('role')
        context['roleList'] = roleQs

        context['formData'] = self.get_bound_data()

        return context



class LoanAnnualHome(SessionRequiredMixin, AnnualReviewHelper, UpdateView):
    # Request already submitted page
    model = FacilityAnnual
    template_name = 'servicing/interface/annualHome.html'
    form_class = AnnualHomeForm
    success_url = reverse_lazy('servicing:loanAnnualNeeds')


    def get_context_data(self, **kwargs):
        context = super(LoanAnnualHome, self).get_context_data(**kwargs)
        context['title'] = 'Annual Review'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('servicing:loanAnnualHousehold'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": True,
             "text": " Next ",
             "href": '',
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        obj= self.get_object()
        context['obj'] = obj

        context['formData'] = self.get_bound_data()

        return context

class LoanAnnualNeeds(SessionRequiredMixin, AnnualReviewHelper, UpdateView):
    # Request already submitted page
    template_name = 'servicing/interface/annualNeeds.html'
    form_class = AnnualNeedsForm
    model = FacilityAnnual
    success_url = reverse_lazy('servicing:loanAnnualThankYou')

    def get_context_data(self, **kwargs):
        context = super(LoanAnnualNeeds, self).get_context_data(**kwargs)
        context['title'] = 'Annual Review'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('servicing:loanAnnualHome'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": True,
             "text": " Next ",
             "href": '',
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        obj= self.get_object()
        context['obj'] = obj

        if (obj.facility.approvedAmount - obj.facility.advancedAmount) > 500:
            context['undrawnAmount'] = True
            context['displayLoan'] = True

        if (obj.facility.totalPlanAmount - obj.facility.totalLoanAmount) > 500:
            context['regularDrawdown'] = True
            context['displayLoan'] = True

        context['formData'] = self.get_bound_data()

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.submitted = True
        obj.responseIP = self.request.META['HTTP_X_REAL_IP'] if 'HTTP_X_REAL_IP' in self.request.META else None
        obj.responseDate = timezone.now()
        obj.save()
        return HttpResponseRedirect(self.success_url)


class LoanAnnualThankYou(SessionRequiredMixin, TemplateView):
    '''Thank You Page for Annual Review Request'''
    template_name = 'servicing/interface/annualThankYou.html'

    def get_context_data(self, **kwargs):
        context = super(LoanAnnualThankYou, self).get_context_data(**kwargs)
        context['title'] = 'Thank you'
        self.request.session.flush()
        return context

class LoanAnnualSubmitted(SessionRequiredMixin, TemplateView):
    # Annual review already submitted page
    template_name = 'servicing/interface/annualSubmitted.html'

    def get_context_data(self, **kwargs):
        context = super(LoanAnnualSubmitted, self).get_context_data(**kwargs)
        context['title'] = 'Annual review submitted'
        self.request.session.flush()
        return context