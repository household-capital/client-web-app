# Python Imports

import json, requests, os


# Django Imports
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView, View, UpdateView
from django.views.generic.base import TemplateResponseMixin
from urllib.parse import urljoin
# Third-party Imports
from config.celery import app


# Local Application Imports
from apps.case.models import ModelSetting, Loan, Case, LoanPurposes

from apps.lib.site_Enums import caseStagesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum, pensionTypesEnum, \
    loanTypesEnum, incomeFrequencyEnum, purposeCategoryEnum, purposeIntentionEnum

from apps.lib.api_Pdf import pdfGenerator
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.site_DataMapping import serialisePurposes
from apps.lib.site_Globals import ECONOMIC, APP_SETTINGS, LOAN_LIMITS
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import firstNameSplit, loan_api_response, validate_loan
from apps.case.utils import createCaseModelSettings
from apps.lib.site_ViewUtils import updateNavQueue
from apps.lib.site_LoanUtils import validateLoanGetContext, getProjectionResults, populateDrawdownPurpose
from apps.lib.mixins import HouseholdLoginRequiredMixin
from .forms import ClientDetailsForm, SettingsForm, IntroChkBoxForm, lumpSumPurposeForm, drawdownPurposeForm, \
    DetailedChkBoxForm,  protectedEquityForm, interestPaymentForm


# // MIXINS


class SessionRequiredMixin(object):
    # Ensures any attempt to acces without UID set is redirct to list view
    def dispatch(self, request, *args, **kwargs):
        if 'caseUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('case:caseList'))
        return super(SessionRequiredMixin, self).dispatch(request, *args, **kwargs)


# // UTILITIES

class ContextHelper():
    # Most of the views require the same validation and context information

    def validate_and_get_context(self):

        context = validateLoanGetContext(self.request.session['caseUID'])

        context['caseStagesEnum'] = caseStagesEnum
        context['clientSexEnum'] = clientSexEnum
        context['clientTypesEnum'] = clientTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum
        context['pensionTypesEnum'] = pensionTypesEnum
        context['loanTypesEnum'] = loanTypesEnum

        context["transfer_img"] = staticfiles_storage.url("img/icons/transfer_" + str(
            context['maxLVRPercentile']) + "_icon.png")

        return context


# CLASS BASED VIEWS

# Landing View
class LandingView(HouseholdLoginRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/landing.html"

    def get(self, request, *args, **kwargs):

        if request.user.profile.isCreditRep != True and request.user.is_superuser != True:
            messages.error(self.request, "Must be a Credit Rep to access meeting")
            return HttpResponseRedirect(reverse_lazy('case:caseList'))

        # Main entry view - save the UID into a session variable
        # Use this to retrieve queryset for each page

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])
            request.session['caseUID'] = caseUID

        elif 'caseUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('case:caseList'))

        else:
            caseUID = request.session['caseUID']

        write_applog("INFO", 'LandingView', 'get', "Meeting commenced by " + str(request.user) + " for -" + caseUID)

        # Esnure model settings populated
        createCaseModelSettings(caseUID)

        return super(LandingView, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        self.extra_context = self.validate_and_get_context()

        # Add's client information to the context (if it exists) for navigation purposes
        context = super(LandingView, self).get_context_data(**kwargs)

        # Set Initial Parameters - Potentially Undefined/None
        # Pension Income
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        caseObj = Case.objects.queryset_byUID(self.request.session['caseUID'])

        if self.extra_context['pensionAmount'] != None:
            loanObj.update(annualPensionIncome=self.extra_context['pensionAmount'] * 26)
        else:
            loanObj.update(annualPensionIncome=0)

        # mortgageDebt
        if self.extra_context['mortgageDebt'] == None:
            caseObj.update(mortgageDebt=0)

        # mortgageDebt
        if self.extra_context['superAmount'] == None:
            caseObj.update(superAmount=0)

        # Check and set consents/meeting date
        if context['consentPrivacy'] == True and context['consentElectronic'] == True:
            context['post_id'] = 2
        else:
            if 'post_id' in kwargs:
                context['post_id'] = kwargs['post_id']
                if kwargs['post_id'] == 1:
                    loanObj.update(consentPrivacy=True)
                if kwargs['post_id'] == 2:
                    loanObj.update(consentElectronic=True)
                    caseObj.update(meetingDate=timezone.now())

        return context


# Settings Views
class SetClientView(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    # Sets the initial client data (in associated dictionary)

    template_name = "client_2_0/interface/settings.html"
    form_class = ClientDetailsForm
    model = Case
    success_url = reverse_lazy('client2:meetingStart')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(SetClientView, self).get_context_data(**kwargs)
        context['title'] = 'Client Information'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['hideMenu'] = True

        return context

    def get_object(self, queryset=None):
        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj

    def form_valid(self, form):

        self.object = form.save()

        if form.cleaned_data['resetConsents']:
            loanQs = Loan.objects.queryset_byUID(self.request.session['caseUID'])
            loanRecord = loanQs.get()
            caseQS = Case.objects.queryset_byUID(self.request.session['caseUID'])
            caseRecord = caseQS.get()

            loanRecord.choiceFuture = False
            loanRecord.choiceCenterlink = False
            loanRecord.choiceVariable = False
            loanRecord.consentPrivacy = False
            loanRecord.consentElectronic = False
            loanRecord.choiceRetireAtHome = False
            loanRecord.choiceAvoidDownsizing = False
            loanRecord.choiceAccessFunds = False
            caseQS.meetingDate = None

            loanRecord.save(update_fields=['choiceFuture', 'choiceCenterlink', 'choiceVariable', 'consentPrivacy',
                                           'consentElectronic', 'choiceRetireAtHome', 'choiceAvoidDownsizing',
                                           'choiceAccessFunds'])

            caseRecord.save(update_fields=['meetingDate'])

        # perform high-level validation of client data
        clientDict = {}
        clientDict = self.get_queryset().values()[0]
        case_obj = self.get_object()
        
        chkResponse =  validate_loan(
            clientDict,
            case_obj.loan.product_type
        )

        if chkResponse['status'] == "Ok":
            # if ok, renders the success_url as normal
            return super(SetClientView, self).form_valid(form)
        else:
            # if error, renders the same page again with error message
            messages.error(self.request, chkResponse['responseText'])
            context = self.get_context_data(form=form)
            return self.render_to_response(context)


class SettingsView(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/settings.html"
    form_class = SettingsForm
    model = ModelSetting
    success_url = reverse_lazy('client2:meetingStart')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(SettingsView, self).get_context_data(**kwargs)
        context['title'] = 'Model Settings'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['hideMenu'] = True

        return context

    def get_object(self, queryset=None):
        queryset = ModelSetting.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


# Introduction Views
class IntroductionView1(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/introduction1.html"

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView1, self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        # Page uses post_id (slug) to expose images using same view
        context['post_id'] = kwargs.get("post_id")
        if context['post_id'] == 4:
            context['menuBarItems'] = {"data": [
                {"button": False,
                 "text": "Yes, that's correct",
                 "href": reverse_lazy('client2:introduction2')}]}

        # use object to retrieve image
        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()

        context['obj'] = obj
        return context


class IntroductionView2(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/introduction2.html"
    form_class = IntroChkBoxForm
    model = Loan
    success_url = reverse_lazy('client2:introduction3')

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView2, self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        # use object to retrieve image
        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()

        context['obj'] = obj

        context['menuBarItems'] = {"data": [
            {"button": True,
             "text": "Yes, that's correct",
             "href": reverse_lazy('client2:introduction2')}]}

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


class IntroductionView3(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/introduction3.html"

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView3, self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['post_id'] = kwargs.get("post_id")
        if not context['post_id']:
            context['post_id'] = 1

        if context['post_id'] == 5:
            context['menuBarItems'] = {"data": [
                {"button": False,
                 "text": "Explore your funding needs",
                 "href": reverse_lazy('client2:navigation')}]}

        if context['post_id'] != 5:
            context['menuBarItems'] = {"data": [
                {"button": False,
                 "text": "Next",
                 "href": reverse_lazy('client2:introduction3') + "/" + str(context['post_id'] + 1)}]}

        if context['post_id'] == 4:
            # Loan Projections
            proj_data = loan_api_response(
                "api/calc/v1/slider/equity",
                self.extra_context,
                {
                    'increment': 100,
                    'years': 15,
                    "product": self.extra_context.get('product_type', "HHC.RM.2021")
                }
            )
            context['sliderData'] = json.dumps(proj_data['dataArray'])
            context['futHomeValue'] = proj_data['futHomeValue']
            context['sliderPoints'] = proj_data['intervals']
            context['imgPath'] = staticfiles_storage.url('img/icons/block_equity_0_icon.png')
            context['transferImagePath'] = staticfiles_storage.url('img/icons/transfer_0_icon.png')

        return context


# Navigation View

class NavigationView(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/navigation.html"

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(NavigationView, self).get_context_data(**kwargs)
        context['title'] = 'Your needs'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, 'data': {
            'intro': True,
            "topUp": True,
            'refi': True,
            'live': True,
            'give': True,
            'care': True,
            'options': True
        }}

        return context


# Top Up Views
class TopUp1(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/topUp1.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = lumpSumPurposeForm
    category = purposeCategoryEnum.TOP_UP.value
    intention = purposeIntentionEnum.INVESTMENT.value

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(TopUp1, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {"topUp": True}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category, intention=self.intention)
        return obj

    def get_form_kwargs(self, **kwargs):
        # add facility object to form kwargs (ussd to populate dropdown in form)
        kwargs = super(TopUp1, self).get_form_kwargs(**kwargs)
        kwargs.update({'descriptionLabel': 'Planned use of top-up funds'})
        return kwargs



# Top Up Views
class TopUp2(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/topUp2.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = drawdownPurposeForm
    category = purposeCategoryEnum.TOP_UP.value
    intention = purposeIntentionEnum.REGULAR_DRAWDOWN.value


    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()
        case = Case.objects.get(caseUID=self.request.session['caseUID'])
        product_type = case.loan.product_type
        context = super(TopUp2, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['drawdownmonths'] = LOAN_LIMITS['maxDrawdownYears'] * 12
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "topUp": True}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category,
                                                          intention=self.intention)
        return obj

    def get_initial(self):
        # Set initial frequency if not set
        initial = super(TopUp2, self).get_initial()

        obj = self.get_object()
        if obj.drawdownFrequency == None :
            initial["drawdownFrequency"] = incomeFrequencyEnum.MONTHLY.value
        return initial

    def form_valid(self, form):
        obj = form.save()

        #Purpose is specified in years, need to populate specific periods and amounts
        obj = populateDrawdownPurpose(obj)

        obj.save()

        return super(TopUp2, self).form_valid(form)


class TopUp3(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/topUp3.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = lumpSumPurposeForm
    category = purposeCategoryEnum.TOP_UP.value
    intention = purposeIntentionEnum.CONTINGENCY.value

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(TopUp3, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "topUp": True}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category, intention=self.intention)
        return obj

    def get_form_kwargs(self, **kwargs):
        # add facility object to form kwargs (ussd to populate dropdown in form)
        kwargs = super(TopUp3, self).get_form_kwargs(**kwargs)
        kwargs.update({'descriptionLabel': 'Your objective for contingency funding'})
        return kwargs

# Refinance
class Refi(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/refi.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = lumpSumPurposeForm
    category = purposeCategoryEnum.REFINANCE.value
    intention = purposeIntentionEnum.MORTGAGE.value

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Refi, self).get_context_data(**kwargs)
        context['title'] = 'Refinance'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            'refi': True}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category, intention=self.intention)
        return obj

    def get_form_kwargs(self, **kwargs):
        # add facility object to form kwargs (ussd to populate dropdown in form)
        kwargs = super(Refi, self).get_form_kwargs(**kwargs)
        kwargs.update({'amountLabel': 'Estimated refinance Amount'})
        return kwargs

    def get_initial(self):
        # Pre-populate with existing debt
        initial = super(Refi, self).get_initial()

        obj = self.get_object()
        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        caseObj = queryset.get()

        if obj.amount == 0 and caseObj.mortgageDebt != 0:
            initial["amount"] = caseObj.mortgageDebt
        return initial


# Live Views
class Live1(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/live1.html"
    success_url = reverse_lazy('client2:live2')
    form_class = lumpSumPurposeForm
    category = purposeCategoryEnum.LIVE.value
    intention = purposeIntentionEnum.RENOVATIONS.value

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Live1, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            'live': True}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category, intention=self.intention)
        return obj



class Live2(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/live2.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = lumpSumPurposeForm
    category = purposeCategoryEnum.LIVE.value
    intention = purposeIntentionEnum.TRANSPORT_AND_TRAVEL.value

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Live2, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            'live': True}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category, intention=self.intention)
        return obj


# Give Views
class Give(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/give.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = lumpSumPurposeForm
    category = purposeCategoryEnum.GIVE.value
    intention = purposeIntentionEnum.GIVE_TO_FAMILY.value

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Give, self).get_context_data(**kwargs)
        context['title'] = 'Give'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            'give': True}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category, intention=self.intention)
        return obj


# Care Views
class Care1(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/care1.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = lumpSumPurposeForm
    category = purposeCategoryEnum.CARE.value
    intention = purposeIntentionEnum.LUMP_SUM.value

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Care1, self).get_context_data(**kwargs)
        context['title'] = 'Care'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            'care': True,}}

        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category, intention=self.intention)
        return obj


class Care2(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/care2.html"
    success_url = reverse_lazy('client2:navigation')
    form_class = drawdownPurposeForm
    category = purposeCategoryEnum.CARE.value
    intention = purposeIntentionEnum.REGULAR_DRAWDOWN.value


    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()
        case = Case.objects.get(caseUID=self.request.session['caseUID'])
        product_type = case.loan.product_type
        context = super(Care2, self).get_context_data(**kwargs)
        context['title'] = 'Care'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            'care': True}}
        context['drawdownmonths'] = LOAN_LIMITS['maxDrawdownYears'] * 12
        return context

    def get_object(self, queryset=None):
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        obj, created = LoanPurposes.objects.get_or_create(loan=loanObj, category=self.category,
                                                          intention=self.intention)
        return obj

    def get_initial(self):
        # Se iniial frequency if not set
        initial = super(Care2, self).get_initial()

        obj = self.get_object()
        if obj.drawdownFrequency == None :
            initial["drawdownFrequency"] = incomeFrequencyEnum.MONTHLY.value
        return initial

    def form_valid(self, form):

        obj = form.save()

        # Purpose is specified in years, need to populate specific periods and amounts
        obj = populateDrawdownPurpose(obj)

        obj.save()

        return super(Care2, self).form_valid(form)


# Options Views
class Options1(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/options1.html"
    form_class = protectedEquityForm
    model = Loan
    success_url = reverse_lazy('client2:options1')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Options1, self).get_context_data(**kwargs)
        context['title'] = 'Reserved Equity'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('client2:navigation'),
             "btn_class": 'btn-outline-hhcBlue'},

            {"button": False,
             "text": "Next",
             "href": reverse_lazy('client2:options2')}
        ]}

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


class Options2(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/options2.html"
    form_class = interestPaymentForm
    model = Loan
    success_url = reverse_lazy('client2:results1')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Options2, self).get_context_data(**kwargs)
        context['title'] = 'Interest Payment'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('client2:options1'),
             "btn_class": 'btn-outline-hhcBlue'},

            {"button": False,
             "text": "Next",
             "href": reverse_lazy('client2:results1')}
        ]}

        context['interestAmount'] = int(
            (context['interestRate'] + context['lendingMargin']) * context['totalLoanAmount'] / 1200)

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


# Results View

class Results1(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/results1.html"

    def get(self, request, *args, **kwargs):
        aggDict = self.validate_and_get_context()

        # Check initial check boxes
        if aggDict['choiceRetireAtHome'] == False or aggDict['choiceAvoidDownsizing'] == False or aggDict[
            'choiceAccessFunds'] == False:
            flagError = True
        else:
            flagError = False

        if aggDict['errors'] == False and flagError == False:
            return HttpResponseRedirect(reverse_lazy('client2:results2'))
        return super(Results1, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Results1, self).get_context_data(**kwargs)
        context['title'] = 'Checks'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('client2:navigation'),
             "btn_class": 'btn-outline-hhcBlue'}]}

        # Check initial check boxes
        if context['choiceRetireAtHome'] == False or context['choiceAvoidDownsizing'] == False or context[
            'choiceAccessFunds'] == False:
            context['flagErrors'] = True

        return context


class Results2(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/results2.html"
    form_class = DetailedChkBoxForm
    model = Loan
    success_url = reverse_lazy('client2:results3')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Results2, self).get_context_data(**kwargs)
        context['title'] = 'Review'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('client2:navigation'),
             "btn_class": 'btn-outline-hhcBlue'},
            {"button": True,
             "text": "Projections",
             "href": reverse_lazy('client2:results3')}
        ]}

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        self.initFormData = super(Results2, self).get_initial()
        loanObj = Loan.objects.queryset_byUID(self.request.session['caseUID']).get()
        loanDict = loanObj.__dict__
        # extend loanDict with purposes
        loanDict.update(serialisePurposes(loanObj))

        self.setInitialValues('choiceTopUp', [loanDict['topUpAmount']])
        self.setInitialValues('choiceRefinance', [loanDict['refinanceAmount']])
        self.setInitialValues('choiceGive', [loanDict['giveAmount']])
        self.setInitialValues('choiceReserve', [loanDict['protectedEquity']])
        self.setInitialValues('choiceLive', [loanDict['renovateAmount'],
                                             loanDict['travelAmount']])
        self.setInitialValues('choiceCare', [loanDict['careAmount']])

        return self.initFormData

    def setInitialValues(self, fieldName, dictName):

        initial = False
        for field in dictName:
            if field != 0:
                initial = True

        self.initFormData[fieldName] = initial


class Results3(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/results3.html"

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Results3, self).get_context_data(**kwargs)

        context['title'] = 'Projections'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['hideMenu'] = True

        #Get projection results (site utility using Loan Projection)
        projectionContext = getProjectionResults(context, ['baseScenario', 'incomeScenario', 'intPayScenario'])
        context.update(projectionContext)

        return context


class Results4(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/results4.html"

    def get_context_data(self, **kwargs):
        context = super(Results4, self).get_context_data(**kwargs)

        context['title'] = 'Thank you'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Finish",
             "btn_class": 'btn-hhcGold',
             "href": reverse_lazy('client2:final')}  # , kwargs={'uid': self.request.session['caseUID']})}
        ]}

        return context


# Final Views

class FinalView(HouseholdLoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateResponseMixin, View):
    template_name = "client_2_0/interface/final.html"

    def get(self, request, *args, **kwargs):
        app.send_task('Create_Loan_Summary', kwargs={'caseUID': self.request.session['caseUID']})
        context={}
        context['successCaseUrl'] = reverse_lazy("case:caseDetail", kwargs={"uid": self.request.session['caseUID']})
        context['failURL'] = self.request.build_absolute_uri(reverse('client2:finalError'))
        messages.success(request, "File generating - please wait")

        return self.render_to_response(context)


    def post(self, request, *args, **kwargs):
        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()

        if obj.summaryDocument:
            return HttpResponse(json.dumps({'pdfURL': self.request.build_absolute_uri(reverse('client2:finalPdf'))}), content_type='application/json', status=200)
        else:
            return HttpResponse(json.dumps({"error": "Document not available"}), content_type='application/json', status=404)


class FinalErrorView(HouseholdLoginRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/final_error.html"


class FinalPDFView(HouseholdLoginRequiredMixin, SessionRequiredMixin, View):
    # This view is called via javascript from the final page to generate the report pdf
    # It uses a utility to render the report and then save and serves the pdf

    def get(self, request):

        obj = Case.objects.queryset_byUID(self.request.session['caseUID']).get()

        pdfFile = default_storage.open(obj.summaryDocument.name)
        pdf_contents = pdfFile.read()
        pdfFile.close()

        ## RENDER FILE TO HTTP RESPONSE
        response = HttpResponse(pdf_contents, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="HHC-LoanSummary.pdf"'

        return response

# REPORT VIEWS

class pdfLoanSummary(ContextHelper,TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/loanSummary.html"

    def get_context_data(self, **kwargs):

        context = super(pdfLoanSummary, self).get_context_data(**kwargs)

        caseUID = str(kwargs['uid'])

        #Validate the loan and generate combined context
        context = validateLoanGetContext(caseUID)
        # Get projection results (site utility using Loan Projection)
        projectionContext = getProjectionResults(context, ['baseScenario', 'incomeScenario', 'intPayScenario',
                                                               'pointScenario', 'stressScenario' ])
        context.update(projectionContext)

        return context






