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
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView, DetailView

from apps.lib.site_Logging import write_applog
from apps.lib.site_Enums import roleEnum

from .models import Facility, FacilityTransactions, FacilityRoles, FacilityProperty, FacilityPropertyVal, FacilityPurposes, FacilityEvents


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


# Case List View
class LoanListView(LoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'servicing/loanList.html'
    context_object_name = 'object_list'
    model = Facility

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = Facility.objects.filter(settlementDate__isnull=False)

        if self.request.GET.get('filter') == "Reconciliation":
            queryset = queryset.filter(
                Q(amalReconciliation=False))

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
        context['title'] = 'Facilities'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        context['recItems'] = Facility.objects.filter(amalReconciliation=False).count()

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
        purposeQs = FacilityEvents.objects.filter(facility=facilityObj).order_by('eventDate')
        context['eventList'] = purposeQs

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

        return context




from .tasks import sfDetailSynch, sfSynch, fundedData
class Test(View):
    def get(self, request):
        #print(sfSynch())
        print(sfDetailSynch())
        #print(fundedData())
