# Python Imports
import os
import json
import datetime
from datetime import timedelta

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, TemplateView, View
from django.views.decorators.csrf import csrf_exempt

# Third-party Imports
from config.celery import app


# Local Application Imports
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.site_Enums import caseStagesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum, channelTypesEnum
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import ReferrerLoginRequiredMixin
from .forms import EnquiryForm, CaseDetailsForm
from apps.enquiry.models import Enquiry
from apps.case.models import Case
from urllib.parse import urljoin


# Referrer Views

class MainView(ReferrerLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        if request.user.profile.referrer.isCaseReferrer:
            return HttpResponseRedirect(reverse_lazy("referrer:caseList"))
        else:
            return HttpResponseRedirect(reverse_lazy("referrer:enqCreate"))


# Enquiry Detail View
class EnquiryView(ReferrerLoginRequiredMixin, UpdateView):
    template_name = "referrer/enquiry.html"
    form_class = EnquiryForm
    model = Enquiry

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            enqUID = str(self.kwargs['uid'])
            queryset = Enquiry.objects.queryset_byUID(str(enqUID))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryView, self).get_context_data(**kwargs)
        context['title'] = 'Referral'
        context['hideNavbar'] = True

        if "uid" in self.kwargs:
            clientDict = Enquiry.objects.dictionary_byUID(str(self.kwargs['uid']))
            loanObj = LoanValidator(clientDict)
            chkOpp = loanObj.validateLoan()
            context['status'] = chkOpp
            queryset = Enquiry.objects.queryset_byUID(str(self.kwargs['uid']))
            obj = queryset.get()
            context['obj'] = obj
            context['isUpdate'] = True
        return context

    def form_valid(self, form):

        clientDict = form.cleaned_data
        obj = form.save(commit=False)
        obj.valuation = 1000000
        clientDict['valuation'] = obj.valuation

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()

        obj.referralUser = self.request.user
        obj.referrer = directTypesEnum.BROKER.value
        obj.referrerID = self.request.user.profile.referrer.companyName + " - " + \
                         self.request.user.first_name + \
                         " " + self.request.user.last_name

        if chkOpp['status'] == "Error":
            obj.status = 0
            obj.errorText = chkOpp['responseText']
            obj.save()
        else:
            obj.status = 1
            obj.maxLoanAmount = chkOpp['data']['maxLoan']
            obj.maxLVR = chkOpp['data']['maxLVR']
            obj.save()

        # Background task to update SF
        app.send_task('Update_SF_Lead', kwargs={'enqUID': str(obj.enqUID)})

        messages.success(self.request, "Referral Captured or Updated")

        return HttpResponseRedirect(reverse_lazy('referrer:enqUpdate', kwargs={'uid': str(obj.enqUID)}))


class EnquiryEmail(ReferrerLoginRequiredMixin, TemplateView):
    template_name = 'referrer/email/email_referral.html'
    model = Enquiry

    def get(self, request, *args, **kwargs):
        email_context = {}
        enqID = str(kwargs['uid'])

        enqObj = Enquiry.objects.queryset_byUID(enqID).get()

        email_context['obj'] = enqObj
        email_context['absolute_url'] = urljoin(
            settings.SITE_URL,
            settings.STATIC_URL
        )
        email_context['absolute_media_url'] = urljoin(
            settings.SITE_URL,
            settings.MEDIA_URL
        )

        if not enqObj.user:
            messages.error(self.request, "This enquiry is not assigned to a user. Please take ownership")
            return HttpResponseRedirect(reverse_lazy('referrer:enquiryDetail', kwargs={'uid': enqObj.enqUID}))

        bcc = enqObj.user.email
        subject, from_email, to = "Household Capital: Introduction", enqObj.user.email, enqObj.email
        text_content = "Text Message"

        try:
            html = get_template(self.template_name)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            messages.success(self.request, "Introduction emailed to client")

            return HttpResponseRedirect(reverse_lazy('referrer:enquiryDetail', kwargs={'uid': enqObj.enqUID}))

        except:
            write_applog("ERROR", 'FollowUpEmail', 'get',
                         "Failed to email introduction:" + enqID)
            messages.error(self.request, "Introduction could not be emailed")
            return HttpResponseRedirect(reverse_lazy('referrer:enquiryDetail', kwargs={'uid': enqObj.enqUID}))


# Case Views

# Case Detail View (UpdateView)
class CaseDetailView(ReferrerLoginRequiredMixin, UpdateView):
    template_name = 'referrer/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm
    context_object_name = 'obj'

    def get_object(self, queryset=None):
        caseUID = str(self.kwargs['uid'])
        queryset = Case.objects.queryset_byUID(str(caseUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Referral Detail'
        context['isUpdate'] = True
        context['caseStagesEnum'] = caseStagesEnum
        context['hideNavbar'] = True


        clientDict = {}
        clientObj = self.object
        clientDict = clientObj.__dict__
        loanObj = LoanValidator(clientDict)
        context['status'] = loanObj.validateLoan()

        return context

    def form_valid(self, form):

        obj = form.save(commit=False)

        # Update age if birthdate present and user
        if obj.birthdate_1 != None:
            obj.age_1 = int((datetime.date.today() - obj.birthdate_1).days / 365.25)
        if obj.birthdate_2 != None:
            obj.age_2 = int((datetime.date.today() - obj.birthdate_2).days / 365.25)

        obj.salesChannel = channelTypesEnum.BROKER.value
        obj.referralCompany = self.request.user.profile.referrer

        obj.save()

        messages.success(self.request, "Case has been updated")

        return HttpResponseRedirect(reverse_lazy('referrer:caseDetail', kwargs={'uid': obj.caseUID}))


# Case Create View (Create View)
class CaseCreateView(ReferrerLoginRequiredMixin, CreateView):
    template_name = 'referrer/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm

    def get_context_data(self, **kwargs):
        context = super(CaseCreateView, self).get_context_data(**kwargs)
        context['title'] = 'New Referral'
        context['hideNavbar'] = True


        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Prior Nullable field
        if not obj.pensionAmount:
            obj.pensionAmount = 0

        # Update age if birthdate present
        if obj.birthdate_1 != None:
            obj.age_1 = datetime.date.today().year - obj.birthdate_1.year

        if obj.birthdate_2 != None:
            obj.age_2 = datetime.date.today().year - obj.birthdate_2.year

        # Set fields manually
        obj.caseStage = caseStagesEnum.DISCOVERY.value
        obj.user = self.request.user
        obj.referralCompany = self.request.user.profile.referrer
        obj.salesChannel = channelTypesEnum.BROKER.value

        obj.save()
        messages.success(self.request, "Case Created")

        return HttpResponseRedirect(reverse_lazy('referrer:caseDetail', kwargs={'uid': obj.caseUID}))



# Case List View
class CaseListView(ReferrerLoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'referrer/caseList.html'
    context_object_name = 'object_list'
    model = Case

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        qs =Case.objects.filter(referralCompany = self.request.user.profile.referrer)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')

            qs = qs.filter(
                Q(caseDescription__icontains=search) |
                Q(adviser__icontains=search) |
                Q(owner__first_name__icontains=search) |
                Q(owner__last_name__icontains=search) |
                Q(caseNotes__icontains=search) |
                Q(street__icontains=search) |
                Q(surname_1__icontains=search))

        return qs

    def get_context_data(self, **kwargs):
        context = super(CaseListView, self).get_context_data(**kwargs)
        context['title'] = 'Referral List'
        context['hideNavbar'] = True


        return context
