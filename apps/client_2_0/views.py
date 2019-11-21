# Python Imports

import json
from math import log

# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.files import File
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView, View, UpdateView

# Local Application Imports
from apps.case.models import ModelSetting, Loan, Case
from apps.lib.site_Enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum, pensionTypesEnum, \
    loanTypesEnum, incomeFrequencyEnum
from apps.lib.site_Globals import ECONOMIC, APP_SETTINGS, LOAN_LIMITS
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_Logging import write_applog
from .forms import ClientDetailsForm, SettingsForm, IntroChkBoxForm, topUpLumpSumForm, topUpDrawdownForm, debtRepayForm
from .forms import giveAmountForm, renovateAmountForm, travelAmountForm, careAmountForm, DetailedChkBoxForm, \
    protectedEquityForm, interestPaymentForm, careDrawdownForm,topUpContingencyForm
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Utilities import firstNameSplit


# // MIXINS

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
    # Ensures any attempt to acces without UID set is redirct to list view
    def dispatch(self, request, *args, **kwargs):
        if 'caseUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('case:caseList'))
        return super(SessionRequiredMixin, self).dispatch(request, *args, **kwargs)


# // UTILITIES


class ContextHelper():
    # Most of the views require the same validation and context information

    def validate_and_get_context(self):
        # get dictionaries from model
        clientDict = Case.objects.dictionary_byUID(self.request.session['caseUID'])
        loanDict = Loan.objects.dictionary_byUID(self.request.session['caseUID'])
        modelDict = ModelSetting.objects.dictionary_byUID(self.request.session['caseUID'])

        # validate loan
        loanObj = LoanValidator(clientDict, loanDict)
        loanStatus = loanObj.getStatus()

        # update loan
        loanQS = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        loanQS.update(maxLVR=loanStatus['data']['maxLVR'],
                      totalLoanAmount=loanStatus['data']['totalLoanAmount'],
                      establishmentFee=loanStatus['data']['establishmentFee'],
                      actualLVR=loanStatus['data']['actualLVR'],
                      totalPlanAmount=loanStatus['data']['totalPlanAmount'],
                      planEstablishmentFee =loanStatus['data']['planEstablishmentFee'],
                      detailedTitle = loanStatus['data']['detailedTitle']
                    )

        # create context
        context = {}
        context.update(clientDict)
        context.update(loanDict)
        context.update(modelDict)
        context.update(loanStatus['data'])

        context['caseTypesEnum'] = caseTypesEnum
        context['clientSexEnum'] = clientSexEnum
        context['clientTypesEnum'] = clientTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum
        context['pensionTypesEnum'] = pensionTypesEnum
        context['loanTypesEnum'] = loanTypesEnum

        context["transfer_img"] = settings.STATIC_URL + "img/icons/transfer_" + str(
            context['maxLVRPercentile']) + "_icon.png"

        return context


# CLASS BASED VIEWS

# Landing View
class LandingView(LoginRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/landing.html"

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

    def get(self, request, *args, **kwargs):

        if 'uid' in kwargs:
            # Main entry view - save the UID into a session variable
            # Use this to retrieve queryset for each page

            caseUID = str(kwargs['uid'])
            request.session['caseUID'] = caseUID
            write_applog("INFO", 'LandingView', 'get', "Meeting commenced by " + str(request.user) + " for -" + caseUID)

            obj = ModelSetting.objects.queryset_byUID(caseUID)
            obj.update(**ECONOMIC)

        if 'caseUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('case:caseList'))

        return super(LandingView, self).get(self, request, *args, **kwargs)


# Settings Views
class SetClientView(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
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

        loanObj = LoanValidator([], clientDict)
        chkResponse = loanObj.validateLoan()

        if chkResponse['status'] == "Ok":
            # if ok, renders the success_url as normal
            return super(SetClientView, self).form_valid(form)
        else:
            # if error, renders the same page again with error message
            messages.error(self.request, chkResponse['responseText'])
            context = self.get_context_data(form=form)
            return self.render_to_response(context)


class SettingsView(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
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
class IntroductionView1(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/introduction1.html"

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView1, self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        # Page uses post_id (slug) to expose images using same view
        context['post_id'] = kwargs.get("post_id")
        context['imgPath'] = settings.STATIC_URL + 'img/'
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


class IntroductionView2(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
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
        context['imgPath'] = settings.STATIC_URL + 'img/'

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


class IntroductionView3(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
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
            loanProj = LoanProjection()
            result = loanProj.create(self.extra_context, frequency=1)
            proj_data = loanProj.getFutureEquityArray(increment=1000)['data']
            context['sliderData'] = json.dumps(proj_data['dataArray'])
            context['futHomeValue'] = proj_data['futHomeValue']
            context['sliderPoints'] = proj_data['intervals']
            context['imgPath'] = settings.STATIC_URL + 'img/icons/block_equity_0_icon.png'
            context['transferImagePath'] = settings.STATIC_URL + 'img/icons/transfer_0_icon.png'

        return context


# Navigation View

class NavigationView(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
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
        }
                                   }

        return context


# Top Up Views
class TopUp1(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/topUp1.html"
    model = Loan
    form_class = topUpLumpSumForm
    success_url = reverse_lazy('client2:navigation')

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(TopUp1, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "intro": False,
            "topUp": True,
            'refi': False,
            'live': False,
            'give': False,
            'care': False,
            'options': False
        }
                                   }

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


# Top Up Views
class TopUp2(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/topUp2.html"
    model = Loan
    form_class = topUpDrawdownForm
    success_url = reverse_lazy('client2:navigation')

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(TopUp2, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "topUp": True,
            'refi': False,
            'live': False,
            'give': False,
            'care': False,
        }
                                   }

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Calculate Top-up Plan Amount
        if obj.topUpFrequency == incomeFrequencyEnum.FORTNIGHTLY.value:
            obj.topUpPlanAmount = obj.topUpIncomeAmount * obj.topUpPeriod * 26
        else:
            obj.topUpPlanAmount = obj.topUpIncomeAmount  * obj.topUpPeriod * 12

        # Calculate Top-up Drawdown Amount - 12 months only
        if obj.topUpFrequency == incomeFrequencyEnum.FORTNIGHTLY.value:
            obj.topUpDrawdownAmount = obj.topUpIncomeAmount * 26
        else:
            obj.topUpDrawdownAmount = obj.topUpIncomeAmount * 12

        if not obj.topUpDrawdownAmount:
            obj.topUpBuffer = 0

        if obj.topUpBuffer:
            obj.topUpDrawdownAmount += LOAN_LIMITS['topUpBufferAmount']
            obj.topUpPlanAmount += LOAN_LIMITS['topUpBufferAmount']

        obj.save()
        return super(TopUp2, self).form_valid(form)


class TopUp3(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/topUp3.html"
    model = Loan
    form_class = topUpContingencyForm
    success_url = reverse_lazy('client2:navigation')

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(TopUp3, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "intro": False,
            "topUp": True,
            'refi': False,
            'live': False,
            'give': False,
            'care': False,
            'options': False
        }
                                   }

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj

# Refinance
class Refi(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/refi.html"
    form_class = debtRepayForm
    model = Loan
    success_url = reverse_lazy('client2:navigation')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Refi, self).get_context_data(**kwargs)
        context['title'] = 'Refinance'
        context['titleUrl'] = reverse_lazy('client2:navigation')

        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "intro": False,
            "topUp": False,
            'refi': True,
            'live': False,
            'give': False,
            'care': False,
            'options': False
        }
                                   }

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj

    def get_initial(self):
        # Pre-populate with existing debt
        initial = super(Refi, self).get_initial()

        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()

        if obj.mortgageDebt != 0:
            initial["refinanceAmount"] = obj.mortgageDebt
        return initial


# Live Views
class Live1(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/live1.html"
    form_class = renovateAmountForm
    model = Loan
    success_url = reverse_lazy('client2:live2')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Live1, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "intro": False,
            "topUp": False,
            'refi': False,
            'live': True,
            'give': False,
            'care': False,
            'options': False
        }
                                   }

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


class Live2(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/live2.html"
    form_class = travelAmountForm
    model = Loan
    success_url = reverse_lazy('client2:navigation')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Live2, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "intro": False,
            "topUp": False,
            'refi': False,
            'live': True,
            'give': False,
            'care': False,
            'options': False
        }
                                   }

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


# Give Views
class Give(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/give.html"
    form_class = giveAmountForm
    model = Loan
    success_url = reverse_lazy('client2:navigation')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Give, self).get_context_data(**kwargs)
        context['title'] = 'Give'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "intro": False,
            "topUp": False,
            'refi': False,
            'live': False,
            'give': True,
            'care': False,
            'options': False
        }
                                   }

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


# Care Views
class Care1(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    template_name = "client_2_0/interface/care1.html"
    form_class = careAmountForm
    model = Loan
    success_url = reverse_lazy('client2:navigation')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Care1, self).get_context_data(**kwargs)
        context['title'] = 'Care'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
            "intro": False,
            "topUp": False,
            'refi': False,
            'live': False,
            'give': False,
            'care': True,
            'options': False
        }
                                   }
        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj

class Care2(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
        template_name = "client_2_0/interface/care2.html"
        form_class = careDrawdownForm
        model = Loan
        success_url = reverse_lazy('client2:navigation')

        def get_context_data(self, **kwargs):
            # Update and add to context
            self.extra_context = self.validate_and_get_context()

            context = super(Care2, self).get_context_data(**kwargs)
            context['title'] = 'Care'
            context['titleUrl'] = reverse_lazy('client2:navigation')
            context['menuPurposes'] = {"display": True, "navigation": True, 'data': {
                "intro": False,
                "topUp": False,
                'refi': False,
                'live': False,
                'give': False,
                'care': True,
                'options': False
            }
                                       }
            return context

        def get_object(self, queryset=None):
            queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
            obj = queryset.get()
            return obj

        def form_valid(self, form):
            obj = form.save(commit=False)

            # Calculate Top-up Plan Amount
            if obj.careFrequency == incomeFrequencyEnum.FORTNIGHTLY.value:
                obj.carePlanAmount = obj.careRegularAmount * obj.carePeriod * 26
            else:
                obj.carePlanAmount = obj.careRegularAmount * obj.carePeriod * 12

            # Calculate Top-up Drawdown Amount - 12 months only
            if obj.careFrequency == incomeFrequencyEnum.FORTNIGHTLY.value:
                obj.careDrawdownAmount = obj.careRegularAmount * 26
            else:
                obj.careDrawdownAmount = obj.careRegularAmount * 12

            obj.save()
            return super(Care2, self).form_valid(form)


# Options Views
class Options1(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
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
        context["img_path"] = settings.STATIC_URL + "img/"

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


class Options2(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
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
        context["img_path"] = settings.STATIC_URL + "img/"

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

class Results1(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
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


class Results2(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
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
        loanDict = Loan.objects.dictionary_byUID(self.request.session['caseUID'])

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


class Results3(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/results3.html"

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Results3, self).get_context_data(**kwargs)

        context['title'] = 'Projections'
        context['titleUrl'] = reverse_lazy('client2:navigation')
        context['hideMenu'] = True

        # Loan Projections
        loanProj = LoanProjection()
        result = loanProj.create(context, frequency=12)
        if result['status'] == "Error":
            write_applog("ERROR", 'client_1_0', 'Results3', result['responseText'])
        result = loanProj.calcProjections()

        # Build results dictionaries

        # Check for no top-up Amount
        if context["topUpDrawdownAmount"] == 0 and context["careDrawdownAmount"] == 0:
            context['topUpProjections'] = False
        else:
            context['topUpProjections'] = True
            context['resultsTotalIncome'] = loanProj.getResultsList('TotalIncome', imageSize=150, imageMethod='lin')[
                'data']
            context['resultsIncomeImages'] = \
                loanProj.getImageList('PensionIncomePC', settings.STATIC_URL + 'img/icons/income_{0}_icon.png')['data']

        context['resultsAge'] = loanProj.getResultsList('BOPAge')['data']
        context['resultsLoanBalance'] = loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquity'] = loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages'] = \
            loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
        context['resultsHouseValue'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
            'data']

        context['totalInterestRate'] = context['interestRate'] + context['lendingMargin']

        context['resultsNegAge'] = loanProj.getNegativeEquityAge()['data']

        if context['loanType'] == loanTypesEnum.JOINT_BORROWER.value:
            if context['age_1'] < context['age_2']:
                context['ageAxis'] = firstNameSplit(context['firstname_1']) + "'s age"
            else:
                context['ageAxis'] = firstNameSplit(context['firstname_2']) + "'s age"
        else:
            context['ageAxis'] = "Your age"

        if context['interestPayAmount']:
            # Interest Payment Calc
            result = loanProj.calcProjections(makeIntPayment=True)
            context['resultsLoanBalance4'] = loanProj.getResultsList('BOPLoanValue')['data']
            context['resultsHomeEquity4'] = loanProj.getResultsList('BOPHomeEquity')['data']
            context['resultsHomeEquityPC4'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
            context['resultsHomeImages4'] = \
                loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')[
                    'data']
            context['resultsHouseValue4'] = \
                loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
                    'data']
        return context


class Results4(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
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

class FinalView(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/final.html"

    def get_context_data(self, **kwargs):
        context = super(FinalView, self).get_context_data(**kwargs)

        context['pdfURL'] = self.request.build_absolute_uri(reverse('client2:finalPdf'))

        return context


class FinalErrorView(LoginRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_2_0/interface/final_error.html"


class FinalPDFView(LoginRequiredMixin, SessionRequiredMixin, View):
    # This view is called via javascript from the final page to generate the report pdf
    # It uses a utility to render the report and then save and serves the pdf

    def get(self, request):

        sourceUrl = 'https://householdcapital.app/client2/pdfLoanSummary/' + self.request.session['caseUID']
        componentFileName = settings.MEDIA_ROOT + "/customerReports/Component-" + self.request.session['caseUID'][
                                                                             -12:] + ".pdf"
        componentURL= 'https://householdcapital.app/media/' + "/customerReports/Component-" + self.request.session['caseUID'][
                                                                             -12:] + ".pdf"
        targetFileName = settings.MEDIA_ROOT + "/customerReports/Summary-" + self.request.session['caseUID'][
                                                                                  -12:] + ".pdf"

        pdf = pdfGenerator(self.request.session['caseUID'])
        created, text = pdf.createPdfFromUrl(sourceUrl, 'HouseholdSummary.pdf', componentFileName)

        if not created:
            return HttpResponseRedirect(reverse_lazy('client2:finalError'))

        #Merge Additional Components
        urlList=[componentURL,
                 'https://householdcapital.app/static/img/document/LoanSummaryAdditional.pdf']

        created, text = pdf.mergePdfs(urlList=urlList, pdfDescription="HHC-LoanSummary.pdf", targetFileName=targetFileName)

        if not created:
            return HttpResponseRedirect(reverse_lazy('client2:finalError'))

        try:
            # SAVE TO DATABASE
            localfile = open(targetFileName, 'rb')

            qsCase = Case.objects.queryset_byUID(self.request.session['caseUID'])
            qsCase.update(summaryDocument=File(localfile), newProcess = True )

            pdf_contents = localfile.read()

            ## RENDER FILE TO HTTP RESPONSE
            response = HttpResponse(pdf.getContent(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="HHC-LoanSummary.pdf"'
            localfile.close()

        except:
            write_applog("ERROR", 'PdfProduction', 'get',
                         "Failed to save Summary Report in Database: " + self.request.session['caseUID'])
            return HttpResponseRedirect(reverse_lazy('client2:finalError'))

        # log user out
        write_applog("INFO", 'PdfProduction', 'get',
                     "Meeting ended for:" + self.request.session['caseUID'])
        logout(self.request)
        return response


# REPORT VIEWS

class PdfLoanSummary(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/loanSummary.html"

    def get_context_data(self, **kwargs):

        context = super(PdfLoanSummary, self).get_context_data(**kwargs)

        if 'uid' in kwargs:

            caseUID = str(kwargs['uid'])

            # get objects
            clientObj = Case.objects.queryset_byUID(caseUID).get()
            loanObj = Loan.objects.queryset_byUID(caseUID).get()
            modelObj = ModelSetting.objects.queryset_byUID(caseUID).get()

            context['obj'] = clientObj
            context['loanObj'] = loanObj

            context.update(clientObj.__dict__)
            context.update(loanObj.__dict__)
            context.update(modelObj.__dict__)

            # validate loan
            loanObj = LoanValidator(context)
            loanStatus = loanObj.getStatus()
            context.update(loanStatus['data'])

            # Loan Projections
            loanProj = LoanProjection()
            result = loanProj.create(context, frequency=12)
            result = loanProj.calcProjections()

            if context["topUpDrawdownAmount"] == 0:
                context['topUpProjections'] = False
            else:
                context['topUpProjections'] = True
                context['resultsTotalIncome'] = \
                    loanProj.getResultsList('TotalIncome', imageSize=150, imageMethod='lin')[
                        'data']
                context['resultsIncomeImages'] = \
                    loanProj.getImageList('PensionIncomePC', settings.STATIC_URL + 'img/icons/income_{0}_icon.png')[
                        'data']

            context['resultsAge'] = loanProj.getResultsList('BOPAge')['data']
            context['resultsLoanBalance'] = loanProj.getResultsList('BOPLoanValue')['data']
            context['resultsHomeEquity'] = loanProj.getResultsList('BOPHomeEquity')['data']
            context['resultsHomeEquityPC'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
            context['resultsHomeImages'] = \
                loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
            context['resultsHouseValue'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
                'data']

            context['totalInterestRate'] = context['interestRate'] + context['lendingMargin']

            context['resultsNegAge'] = loanProj.getNegativeEquityAge()['data']

            context['comparisonRate'] = context['totalInterestRate'] + context['comparisonRateIncrement']

            context['loanTypesEnum'] = loanTypesEnum
            context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

            if context['loanType'] == loanTypesEnum.JOINT_BORROWER.value:
                if context['age_1'] < context['age_2']:
                    context['ageAxis'] = firstNameSplit(context['firstname_1']) + "'s age"
                else:
                    context['ageAxis'] = firstNameSplit(context['firstname_2']) + "'s age"
            else:
                context['ageAxis'] = "Your age"

            # Stress Results

            # Stress-1
            result = loanProj.calcProjections(hpiStressLevel=APP_SETTINGS['hpiLowStressLevel'])
            context['hpi1'] = APP_SETTINGS['hpiLowStressLevel']
            context['intRate1'] = context['totalInterestRate']

            context['resultsLoanBalance1'] = loanProj.getResultsList('BOPLoanValue')['data']
            context['resultsHomeEquity1'] = loanProj.getResultsList('BOPHomeEquity')['data']
            context['resultsHomeEquityPC1'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
            context['resultsHomeImages1'] = \
                loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
            context['resultsHouseValue1'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
                'data']

            # Stress-2
            result = loanProj.calcProjections(hpiStressLevel=APP_SETTINGS['hpiHighStressLevel'])
            context['hpi2'] = APP_SETTINGS['hpiHighStressLevel']
            context['intRate2'] = context['totalInterestRate']

            context['resultsLoanBalance2'] = loanProj.getResultsList('BOPLoanValue')['data']
            context['resultsHomeEquity2'] = loanProj.getResultsList('BOPHomeEquity')['data']
            context['resultsHomeEquityPC2'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
            context['resultsHomeImages2'] = \
                loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
            context['resultsHouseValue2'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
                'data']

            # Stress-3
            result = loanProj.calcProjections(intRateStress=APP_SETTINGS['intRateStress'])
            context['hpi3'] = context['housePriceInflation']
            context['intRate3'] = context['totalInterestRate'] + APP_SETTINGS['intRateStress']

            context['resultsLoanBalance3'] = loanProj.getResultsList('BOPLoanValue')['data']
            context['resultsHomeEquity3'] = loanProj.getResultsList('BOPHomeEquity')['data']
            context['resultsHomeEquityPC3'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
            context['resultsHomeImages3'] = \
                loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
            context['resultsHouseValue3'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
                'data']

            # Stress-4
            result = loanProj.calcProjections(makeIntPayment=True)
            context['resultsLoanBalance4'] = loanProj.getResultsList('BOPLoanValue')['data']
            context['resultsHomeEquity4'] = loanProj.getResultsList('BOPHomeEquity')['data']
            context['resultsHomeEquityPC4'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
            context['resultsHomeImages4'] = \
                loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
            context['resultsHouseValue4'] = loanProj.getResultsList('BOPHouseValue', imageSize=110, imageMethod='lin')[
                'data']
        return context


class PdfRespLending(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/respLending.html"

    def get_context_data(self, **kwargs):
        context = super(PdfRespLending, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            clientDict = Case.objects.dictionary_byUID(caseUID)
            loanDict = Loan.objects.dictionary_byUID(caseUID)

            context.update(clientDict)
            context.update(loanDict)
            context['caseUID'] = caseUID

        return context


class PdfPrivacy(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/privacy.html"

    def get_context_data(self, **kwargs):
        context = super(PdfPrivacy, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            clientDict = Case.objects.dictionary_byUID(caseUID)
            loanDict = Loan.objects.dictionary_byUID(caseUID)

            context.update(clientDict)
            context.update(loanDict)
            context['caseUID'] = caseUID
            context['loanTypesEnum'] = loanTypesEnum

        return context


class PdfElectronic(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/electronic.html"

    def get_context_data(self, **kwargs):
        context = super(PdfElectronic, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            clientDict = Case.objects.dictionary_byUID(caseUID)
            loanDict = Loan.objects.dictionary_byUID(caseUID)

            context.update(clientDict)
            context.update(loanDict)
            context['caseUID'] = caseUID
            context['loanTypesEnum'] = loanTypesEnum

        return context


class PdfClientData(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/clientData.html"

    def get_context_data(self, **kwargs):
        context = super(PdfClientData, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            qsClient = Case.objects.queryset_byUID(caseUID)
            qsLoan = Loan.objects.queryset_byUID(caseUID)

            context['client'] = qsClient.get()
            context['loan'] = qsLoan.get()
            context['loanTypesEnum'] = loanTypesEnum
            context['caseUID'] = caseUID

        return context


class PdfInstruction(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/clientInstruction.html"

    def get_context_data(self, **kwargs):
        context = super(PdfInstruction, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            qsClient = Case.objects.queryset_byUID(caseUID)
            qsLoan = Loan.objects.queryset_byUID(caseUID)

            context['client'] = qsClient.get()
            context['loan'] = qsLoan.get()
            context['loanTypesEnum'] = loanTypesEnum
            context['caseUID'] = caseUID

        return context


class PdfValInstruction(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_2_0/documents/clientValInstruction.html"

    def get_context_data(self, **kwargs):
        context = super(PdfValInstruction, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            qsClient = Case.objects.queryset_byUID(caseUID)
            qsLoan = Loan.objects.queryset_byUID(caseUID)

            context['client'] = qsClient.get()
            context['loan'] = qsLoan.get()
            context['loanTypesEnum'] = loanTypesEnum
            context['caseUID'] = caseUID

        return context
