# Python Imports
import datetime
import json
import base64
import os
import pathlib

# Django Imports
from django.contrib.auth.decorators import login_required

from django.db.models import Q, F
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView, DetailView

from apps.lib.site_Logging import write_applog
from apps.lib.site_Enums import roleEnum

from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, \
    FacilityPurposes, FacilityEvents, FacilityEnquiry

from .forms import FacilityEnquiryForm

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


# List View
class LoanListView(LoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'servicing/loanList.html'
    context_object_name = 'object_list'
    model = Facility

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = Facility.objects\
            .annotate(availableAmount = F('approvedAmount')-F('advancedAmount')) \
            .filter(settlementDate__isnull=False)
        #    .annotate(planAddition = F('totalLoanAmount')-F('totalPlanAmount'))\


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

        context['recItems'] = Facility.objects.filter(amalReconciliation=False, settlementDate__isnull=False).count()
        context['breachItems'] = Facility.objects.filter(amalBreach=True, settlementDate__isnull=False).count()
        context['enquiryItems'] = FacilityEnquiry.objects.filter(actioned=False).count()

        return context

class LoanEventList(LoginRequiredMixin, ListView):
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

# Loan Detail View
class LoanDetailView(LoginRequiredMixin, DetailView):
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

        facilityObj = self.get_object()
        purposeQs = FacilityEvents.objects.filter(facility=facilityObj).order_by('-eventDate')
        context['eventList'] = purposeQs
        enquiryQs = FacilityEnquiry.objects.filter(facility=facilityObj).order_by('-timestamp')
        context['enquiryList'] = enquiryQs

        context['menuOverview'] = True
        context['facilityObj'] = facilityObj

        return context


class LoanDetailBalances(LoginRequiredMixin, DetailView):
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