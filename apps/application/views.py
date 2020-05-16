from datetime import datetime
from datetime import timedelta, date
import json
import random
import uuid

# Django Imports
from django.conf import settings

from django.contrib import messages
from django.core import signing
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView, View, UpdateView

# Third Party Imports
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from config.celery import app

# Local Application Imports
from apps.lib.api_BurstSMS import apiBurst
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_Enums import directTypesEnum, appStatusEnum, loanTypesEnum, incomeFrequencyEnum, \
    purposeIntentionEnum, purposeCategoryEnum, clientTypesEnum
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import sendTemplateEmail, raiseAdminError, populateDrawdownPurpose, \
    getProjectionResults, validateApplicationGetContext, populateDrawdownPurpose

from apps.accounts.models import SessionLog
from apps.enquiry.models import Enquiry
from .models import Application
from .forms import InitiateForm, TwoFactorForm, ObjectivesForm, ApplicantForm, ApplicantTwoForm, \
    LoanObjectivesForm, AssetsForm, IncomeForm, ConsentsForm, BankForm, SigningForm

from .serialisers import IncomeApplicationSeraliser
from .models import Application, ApplicationPurposes


## VIEWS ARE EXTERNALLY EXPOSED OR SESSION VERIFIED ##

# Mixins
class SessionIdOnlyMixin(object):
    # Ensures any attempt to access without UID set is redirect to error view

    def dispatch(self, request, *args, **kwargs):
        if 'appUID' not in request.session:
            request.session['appUID'] = str(Application.objects.first().appUID)
            #return HttpResponseRedirect(reverse_lazy('application:sessionError'))

        return super(SessionIdOnlyMixin, self).dispatch(request, *args, **kwargs)


class SessionRequiredMixin(object):
    # Ensures any attempt to access without UID set is redirect to error view

    def dispatch(self, request, *args, **kwargs):
        if 'appUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('application:sessionError'))

        if 'pin' not in request.session:
            return HttpResponseRedirect(reverse_lazy('application:resume'))

        return super(SessionRequiredMixin, self).dispatch(request, *args, **kwargs)


# Helper

class ApplicationHelper(object):
    # Common get_object override

    def get_object(self, queryset=None):
        return Application.objects.filter(appUID=uuid.UUID(self.request.session['appUID'])).get()

    def get_purpose_object(self):

        # declare explicitly as get_object may be overriden
        application = Application.objects.filter(appUID=uuid.UUID(self.request.session['appUID'])).get()

        purpose, created = ApplicationPurposes.objects.get_or_create(application=application,
                                                                     category=purposeCategoryEnum.TOP_UP.value,
                                                                     intention=purposeIntentionEnum.REGULAR_DRAWDOWN.value)
        if created:
            self.set_initial_purpose()

        return purpose

    def get_bound_data(self):
        # returns form data dictionary. Enables manipulation of data in case where from invalid
        # as data returned as a string. Used when manually rendering forms

        form = self.get_form()
        boundData = {}
        for name, field in form.fields.items():
            boundData[name] = form[name].value()
            if boundData[name] == "True":
                boundData[name] = True
            if boundData[name] == "False":
                boundData[name] = False
        return boundData

    def set_initial_purpose(self):
        # Set defaults if purpose is blank
        obj = Application.objects.filter(appUID=uuid.UUID(self.request.session['appUID'])).get()
        purp_obj = self.get_purpose_object()

        purp_obj.category = purposeCategoryEnum.TOP_UP.value
        purp_obj.intention = purposeIntentionEnum.REGULAR_DRAWDOWN.value
        purp_obj.planPeriod = 10
        purp_obj.drawdownFrequency = incomeFrequencyEnum.MONTHLY.value
        purp_obj.drawdownAmount = obj.maxDrawdownMonthly
        purp_obj.save()

        # Populate purpose based on simple plan period
        purp_obj = populateDrawdownPurpose(purp_obj)
        purp_obj.save()

    def validateGetContext(self):
        # Updates application calculated amounts and returns dictionary with serialised purposes
        return validateApplicationGetContext(self.request.session['appUID'])

    def get_projection_object(self):

        combinedDict = self.validateGetContext()
        # Prepare dictionary for projection
        combinedDict['interestRate'] = ECONOMIC['interestRate']
        combinedDict['lendingMargin'] = ECONOMIC['lendingMargin']
        combinedDict['inflationRate'] = ECONOMIC['inflationRate']
        combinedDict['totalInterestRate'] = ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
        combinedDict['housePriceInflation'] = ECONOMIC['housePriceInflation']
        combinedDict['establishmentFeeRate'] = LOAN_LIMITS['establishmentFee']

        # create projection object
        loanProj = LoanProjection()
        result = loanProj.create(combinedDict)
        return loanProj

    def get_projection_results(self, scenarioList):
        context = self.validateGetContext()
        context.update(ECONOMIC)
        context['totalInterestRate'] = ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
        context['housePriceInflation'] = ECONOMIC['housePriceInflation']
        context['comparisonRate'] = context['totalInterestRate'] + ECONOMIC['comparisonRateIncrement']

        projectionResults = getProjectionResults(context,
                                                 scenarioList,
                                                 "img/icons/block_equity_{0}_icon.png")
        return projectionResults


class ValidateMixin(object):

    def validate(self, request, signed_payload, max_age, *args, **kwargs):

        try:
            payload = signing.loads(signed_payload, max_age=max_age)

            # set session variables
            request.session['appUID'] = payload['appUID']
            SessionLog.objects.create(
                description="Application session",
                referenceUID=uuid.UUID(payload['appUID'])
            )

            return {'status': 'Ok'}

        except signing.SignatureExpired:
            write_applog("INFO", 'ApplicationValidate', 'get',
                         "Expired Signature")
            return {'status': 'Error', 'responseText': "Expired Signature",
                    'data': {'url': reverse_lazy('application:validationError')}}

        except signing.BadSignature:
            write_applog("ERROR", 'ApplicationValidate', 'get',
                         "BAD Signature")
            return {'status': 'Error', 'responseText': "BAD Signature",
                    'data': {'url': reverse_lazy('application:validationError')}}


## UNAUTHENTICATED VIEWS

# API VIEWS
class CreateApplication(CreateAPIView):
    # Creates an application and returns a start URL
    serializer_class = IncomeApplicationSeraliser

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()

        if serializer.errors:
            write_applog("ERROR", 'CreateApplication', 'create', json.dumps(serializer.errors))
            raiseAdminError('Application Create Error', json.dumps(serializer.errors))
            return Response({'responseText': 'Application create error'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            headers={'content-type': 'application/json'})

        else:
            obj = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            payload = {'appUID': str(obj.appUID)}

            signed_payload = signing.dumps(payload)
            signedURL = settings.SITE_URL + str(reverse_lazy('application:validateStart',
                                                             kwargs={'signed_pk': signed_payload}))
            data = {'applicationURL': signedURL}

            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()


# Error Views
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


# Validation Process Views
class ValidateReturn(ValidateMixin, View):

    def get(self, request, *args, **kwargs):
        signed_payload = kwargs['signed_pk']
        max_age = 60 * 60 * 24 * 7

        result = self.validate(request, signed_payload, max_age)

        if result['status'] != "Ok":
            return HttpResponseRedirect(result['data']['url'])

        return HttpResponseRedirect(reverse_lazy('application:resume'))


class ValidateStart(ValidateMixin, View):
    # Validates a start URL received from website
    def get(self, request, *args, **kwargs):
        signed_payload = kwargs['signed_pk']
        max_age = 60 * 2

        result = self.validate(request, signed_payload, max_age)

        if result['status'] != "Ok":
            return HttpResponseRedirect(result['data']['url'])

        return HttpResponseRedirect(reverse_lazy('application:start'))


## SESSION VALIDATED VIEWS (ID ONLY)

class StartApplicationView(SessionIdOnlyMixin, ApplicationHelper, UpdateView):
    # Initiates Application
    template_name = 'application/interface/apply.html'
    model = Application
    form_class = InitiateForm
    success_url = reverse_lazy('application:consents')

    def get_context_data(self, **kwargs):
        context = super(StartApplicationView, self).get_context_data(**kwargs)
        context['title'] = 'Online Application'

        context['menuBarItems'] = {"data": [
            {"button": True,
             "text": "Next",
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'}
        ]}
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.appStatus = appStatusEnum.IN_PROGRESS.value
        obj.save()

        self.request.session['pin'] = True

        payload = {'appUID': str(obj.appUID)}

        signed_payload = signing.dumps(payload)
        signedURL = settings.SITE_URL + str(
            reverse_lazy('application:validateReturn', kwargs={'signed_pk': signed_payload}))

        app.send_task('Email_App_Link', kwargs={'appUID': str(obj.appUID), 'signedURL': signedURL})
        messages.success(self.request, "Application linked emailed to you")

        return super(StartApplicationView, self).form_valid(form)


class ResumeApplicationView(SessionIdOnlyMixin, FormView):
    # Resume Application
    template_name = 'application/interface/resume.html'
    form_class = TwoFactorForm
    success_url = reverse_lazy('application:consents')
    model = Application

    def get_object(self):
        obj = Application.objects.filter(appUID=uuid.UUID(self.request.session['appUID'])).get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(ResumeApplicationView, self).get_context_data(**kwargs)
        context['title'] = 'Resume Application'
        context['obj'] = self.get_object()
        return context

    def form_valid(self, form):
        pin = form.cleaned_data['pin']

        obj = self.get_object()
        if (pin == obj.pin) and (timezone.now() < obj.pinExpiry):
            self.request.session['pin'] = obj.pin
            self.request.session['appUID'] = str(obj.appUID)
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(self.request, "Pin does not match, please re-enter or send another")

            return HttpResponseRedirect(self.request.path_info)


class GeneratePin(SessionIdOnlyMixin, View):

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.pin = random.randint(1000, 9999)
        obj.pinExpiry = timezone.now() + timedelta(minutes=5)
        obj.save(update_fields=['pin', 'pinExpiry'])

        # SMS Customer
        sms = apiBurst()
        result = sms.sendSMS(obj.mobile,
                             "Hello {0}, you application pin is {1}".format(obj.firstname_1, obj.pin),
                             "Household")

        messages.success(request, "SMS text message sent")

        returnPage = kwargs['returnPage']

        return HttpResponseRedirect(reverse_lazy('application:' + returnPage))

    def get_object(self):
        obj = Application.objects.filter(appUID=uuid.UUID(self.request.session['appUID'])).get()
        return obj


class ConsentsView(SessionRequiredMixin, ApplicationHelper, UpdateView):
    template_name = 'application/interface/consents.html'
    form_class = ConsentsForm
    success_url = reverse_lazy('application:introduction')

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if (obj.consentPrivacy) and (obj.consentElectronic):
            return HttpResponseRedirect(reverse_lazy('application:introduction'))
        else:
            return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ConsentsView, self).get_context_data(**kwargs)
        context['title'] = 'Consents'
        obj = self.get_object()
        context['obj'] = obj

        context['menuBarItems'] = {"data": [
            {"button": True,
             "text": "Next",
             }]}

        return context


class IntroductionView(SessionRequiredMixin, ApplicationHelper, UpdateView):
    form_class = ObjectivesForm
    template_name = 'application/interface/introduction.html'
    model = Application

    def get_context_data(self, **kwargs):
        context = super(IntroductionView, self).get_context_data(**kwargs)
        context['title'] = 'Eligibility'
        obj = self.get_object()
        context['obj'] = obj

        context['menuBarItems'] = {"data": [
            {"button": True,
             "text": "Next",
             }]}

        context['formData'] = self.get_bound_data()

        return context

    def form_valid(self, form):
        obj = form.save(commit=True)

        if (obj.choiceIncome == False) or \
                (obj.choiceOtherNeeds == True) or \
                (obj.choiceMortgage == True):
            messages.error(self.request, "Multiple purposes")

            return HttpResponseRedirect(reverse_lazy('application:multiPurpose'))

        if (obj.choiceOwnership == False):
            messages.error(self.request, "Ownership")
            return HttpResponseRedirect(reverse_lazy('application:ownership'))

        return HttpResponseRedirect(reverse_lazy('application:applicant1'))


class MultiplePurposesView(SessionRequiredMixin, ApplicationHelper, TemplateView):
    template_name = 'application/interface/exit_multiple.html'

    def get_context_data(self, **kwargs):
        context = super(MultiplePurposesView, self).get_context_data(**kwargs)
        context['title'] = 'Introduction'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:introduction'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": False,
             "text": "Contact me",
             "href": reverse_lazy('application:contactMe'),
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}
        return context


class ContactView(SessionRequiredMixin, ApplicationHelper, TemplateView):
    template_name = 'application/interface/exit_contact.html'

    def get_context_data(self, **kwargs):
        context = super(ContactView, self).get_context_data(**kwargs)
        context['title'] = 'Thank you'

        obj = self.get_object()

        # Create a contact queue item
        message = "[# Income Product Application journey #] \n\r"
        message += "Client indicated that they had other funding requirements or an existing mortgage. \n\r"
        message += "Please contact to understand objectives and arrange a meeting with a Credit Representative. \n\r"
        message += ", ".join(filter(None, [obj.streetAddress, obj.suburb, obj.state, str(obj.postcode)]))

        enqObj = Enquiry.objects.create(
            name=obj.firstname_1 + " " + obj.surname_1,
            email=obj.email,
            phoneNumber=obj.mobile,
            enquiryNotes=message,
            postcode=obj.postcode,
            loanType=obj.loanType,
            age_1=obj.age_1,
            age_2=obj.age_2,
            dwellingType=obj.dwellingType,
            valuation=obj.valuation,
            referrer=directTypesEnum.WEB_ENQUIRY.value
        )

        obj.appStatus = appStatusEnum.CONTACT.value
        obj.save(update_fields=['appStatus'])
        self.request.session.flush()
        messages.info(self.request, "Application session ended")

        return context


class ExitView(TemplateView):
    template_name = 'application/interface/exit_exit.html'

    def get_context_data(self, **kwargs):
        context = super(ExitView, self).get_context_data(**kwargs)
        context['title'] = 'Thank you'

        self.request.session.flush()
        messages.info(self.request, "Application session ended")

        return context


class OwnershipView(SessionRequiredMixin, TemplateView):
    template_name = 'application/interface/exit_ownership.html'

    def get_context_data(self, **kwargs):
        context = super(OwnershipView, self).get_context_data(**kwargs)
        context['title'] = 'Introduction'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:introduction'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": False,
             "text": " Exit ",
             "href": reverse_lazy('application:exit'),
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}
        return context


class AgeView(SessionRequiredMixin, TemplateView):
    template_name = 'application/interface/exit_age.html'

    def get_context_data(self, **kwargs):
        context = super(AgeView, self).get_context_data(**kwargs)
        context['title'] = 'About you'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:applicant1'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": False,
             "text": " Exit ",
             "href": reverse_lazy('application:exit'),
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        context['minAge'] = LOAN_LIMITS['minSingleAge']
        return context


class MinimumView(SessionRequiredMixin, TemplateView):
    template_name = 'application/interface/exit_minimum.html'

    def get_context_data(self, **kwargs):
        context = super(MinimumView, self).get_context_data(**kwargs)
        context['title'] = 'About you'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:applicant1'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": False,
             "text": " Exit ",
             "href": reverse_lazy('application:exit'),
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        context['minIncomeDrawdown'] = LOAN_LIMITS['minIncomeDrawdown']
        return context


class Applicant1View(SessionRequiredMixin, ApplicationHelper, UpdateView):
    template_name = 'application/interface/applicant.html'
    form_class = ApplicantForm
    success_url = reverse_lazy('application:product')

    def get_context_data(self, **kwargs):
        context = super(Applicant1View, self).get_context_data(**kwargs)
        context['title'] = 'About you'
        context['subtitle'] = 'Please complete your details'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:introduction'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": True,
             "text": " Next ",
             "href": '',
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.age_1 = int((date.today() - obj.birthdate_1).days / 365.25)
        obj.save()
        if obj.age_1 < LOAN_LIMITS['minSingleAge']:
            messages.error(self.request, "Age restriction")
            return HttpResponseRedirect(reverse_lazy('application:age'))

        if obj.loanType == loanTypesEnum.JOINT_BORROWER.value:
            return HttpResponseRedirect(reverse_lazy('application:applicant2'))

        return super(Applicant1View, self).form_valid(form)


class Applicant2View(SessionRequiredMixin, ApplicationHelper, UpdateView):
    template_name = 'application/interface/applicant_second.html'
    form_class = ApplicantTwoForm
    success_url = reverse_lazy('application:product')

    def get_context_data(self, **kwargs):
        context = super(Applicant2View, self).get_context_data(**kwargs)
        context['title'] = 'About you'
        context['subtitle'] = 'Please complete '

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:applicant1'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": True,
             "text": " Next ",
             "href": '',
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}
        return context

    def form_valid(self, form):
        obj = form.save(commit=True)

        obj.age_2 = int((date.today() - obj.birthdate_2).days / 365.25)
        if obj.clientType2 == clientTypesEnum.PERMITTED_COHABITANT.value:
            obj.loanType = loanTypesEnum.SINGLE_BORROWER.value
        obj.save()

        if (obj.age_2 < LOAN_LIMITS['minSingleAge']) and (obj.loanType == loanTypesEnum.JOINT_BORROWER.value):
            messages.error(self.request, "Age restriction")
            return HttpResponseRedirect(reverse_lazy('application:age'))

        return super(Applicant2View, self).form_valid(form)


class ProductView(SessionRequiredMixin, ApplicationHelper, TemplateView):
    template_name = 'application/interface/product.html'

    def get(self, request, *args, **kwargs):
        # Validate loan before rendering

        obj = self.get_object()
        loanObj = LoanValidator(obj.__dict__)
        loanStatus = loanObj.getStatus()['data']
        if loanStatus['errors'] == True:
            if loanStatus['minloanAmountStatus'] != "Ok":
                messages.error(request, "Minimum loan size")
                return HttpResponseRedirect(reverse_lazy('application:minimum'))
            else:
                raiseAdminError("Application Error", "Loan validation errors -" + json.dumps(loanStatus))

        # Update Application
        obj.maxLoanAmount = loanStatus['maxLoanAmount']
        obj.maxDrawdownAmount = loanStatus['maxDrawdownAmount']
        obj.maxDrawdownMonthly = loanStatus['maxDrawdownMonthly']
        obj.maxLVR = loanStatus['maxLVR']
        obj.status = 1
        obj.save()

        return super(ProductView, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProductView, self).get_context_data(**kwargs)
        context['title'] = 'Your objectives '
        context['subtitle'] = 'How does a Home Income Loan work?'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:applicant1'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": False,
             "text": " Next ",
             "href": reverse_lazy('application:objectives'),
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        # Get Loan Data
        obj = self.get_object()
        loanObj = LoanValidator(obj.__dict__)
        context['obj'] = obj
        context.update(loanObj.getStatus()['data'])

        context["transfer_img"] = settings.STATIC_URL + "img/icons/transfer_%s_icon.png" % context['maxLVRPercentile']
        context['imgPath'] = settings.STATIC_URL + 'img/icons/block_equity_0_icon.png'
        context['transferImagePath'] = settings.STATIC_URL + 'img/icons/transfer_0_icon.png'

        return context


class ObjectivesView(SessionRequiredMixin, ApplicationHelper, UpdateView):
    template_name = 'application/interface/objectives.html'
    form_class = LoanObjectivesForm
    success_url = reverse_lazy("application:projections")

    def get_object(self, queryset=None):
        # Object in this class is the purposeObject
        return self.get_purpose_object()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Your objectives '
        context['subtitle'] = 'I would like to receive...'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:product'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": True,
             "text": " Next ",
             "href": reverse_lazy('application:objectives'),
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        # Loan Projection
        loanProj = self.get_projection_object()
        proj_data = loanProj.getFutureIncomeEquityArray(increment=50)['data']

        context['totalInterestRate'] = ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
        context['housePriceInflation'] = ECONOMIC['housePriceInflation']
        context['establishmentFeeRate'] = LOAN_LIMITS['establishmentFee']
        context['sliderData'] = json.dumps(proj_data['dataArray'])
        context['futHomeValue'] = proj_data['futHomeValue']
        context['sliderPoints'] = proj_data['intervals']
        context['imgPath'] = settings.STATIC_URL + 'img/icons/block_equity_0_icon.png'
        context['transferImagePath'] = settings.STATIC_URL + 'img/icons/transfer_0_icon.png'

        context['ajaxURL'] = reverse_lazy('application:sliderUpdate')

        return context

    def form_valid(self, form):
        # Save key loan choices and update application
        purp_obj = form.save()
        purp_obj.planPeriod = form.cleaned_data['planPeriod']
        purp_obj.drawdownFrequency = form.cleaned_data['drawdownFrequency']
        purp_obj.drawdownAmount = form.cleaned_data['drawdownAmount']
        purp_obj.save()

        # Update purpose fields
        purp_obj = populateDrawdownPurpose(purp_obj)
        purp_obj.save()

        # Update application fields
        self.validateGetContext()

        return super(ObjectivesView, self).form_valid(form)


class SliderUpdate(SessionRequiredMixin, ApplicationHelper, UpdateView):
    form_class = LoanObjectivesForm

    def get_object(self, queryset=None):
        return self.get_purpose_object()

    def form_valid(self, form):
        obj = form.save()

        # Update purpose fields
        purp_obj = populateDrawdownPurpose(obj)
        purp_obj.save()

        loanProj = self.get_projection_object()
        proj_data = loanProj.getFutureIncomeEquityArray(increment=50)['data']

        return HttpResponse(json.dumps(proj_data['dataArray']), content_type='application/json')

    def form_invalid(self, form):
        return HttpResponse(json.dumps({"error": "Form Invalid"}), content_type='application/json', status=400)


class ProjectionsView(SessionRequiredMixin, ApplicationHelper, TemplateView):
    template_name = 'application/interface/projections.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Your projections '
        context['subtitle'] = 'Home equity over time'

        # Check whether to re-send Loan Summary
        obj = self.get_object()
        context['obj'] = obj

        success_url = reverse_lazy('application:sendLoanSummary')
        context['success_url'] = success_url
        isButton = True
        isModal = True
        target = '#loanSummaryModal'

        if (obj.loanSummarySent) and (obj.totalPlanAmount <= obj.loanSummaryAmount):
            isButton = False
            isModal = False
            successUrl = reverse_lazy('application:assets')

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:objectives'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": isButton,
             "modal": isModal,
             "target": target,
             "text": " Next ",
             "href": success_url,
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        context['totalInterestRate'] = ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
        context['housePriceInflation'] = ECONOMIC['housePriceInflation']
        context['establishmentFeeRate'] = LOAN_LIMITS['establishmentFee']

        context['purp_obj'] = self.get_purpose_object()

        resultsDict = self.get_projection_results(['baseScenario'])

        context.update(resultsDict)

        return context


class PdfLoanSummary(ApplicationHelper, TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = 'application/documents/loanSummary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.request.session['appUID'] = str(kwargs['uid'])

        context['totalInterestRate'] = ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
        context['housePriceInflation'] = ECONOMIC['housePriceInflation']
        context['establishmentFeeRate'] = LOAN_LIMITS['establishmentFee']

        context.update(self.get_object().__dict__)
        context.update(self.get_purpose_object().__dict__)

        resultsDict = self.get_projection_results(['baseScenario', 'pointScenario', 'stressScenario'])
        context.update(resultsDict)

        return context


class SendLoanSummary(SessionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        messages.success(self.request, "Loan Summary emailed")
        app.send_task('Email_App_Summary', kwargs={'appUID': request.session['appUID']})
        return HttpResponseRedirect(reverse_lazy('application:assets'))


class AssestView(SessionRequiredMixin, ApplicationHelper, UpdateView):
    form_class = AssetsForm
    model = Application
    success_url = reverse_lazy('application:income')
    template_name = 'application/interface/assets.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Application'
        context['subtitle'] = 'Financial Information'

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:projections'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": True,
             "text": " Next ",
             "href": '',
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        return context


class IncomeView(SessionRequiredMixin, ApplicationHelper, UpdateView):
    form_class = IncomeForm
    model = Application
    template_name = 'application/interface/income.html'
    success_url = reverse_lazy('application:bank')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Application'
        context['subtitle'] = 'Income and expenses'

        context['menuBarItems'] = {"float": True,
                                   "data": [
                                       {"button": False,
                                        "text": "Back",
                                        "href": reverse_lazy('application:assets'),
                                        "btn_class": 'btn-outline-hhcBlue',
                                        "btn_id": 'btn_back'},
                                       {"button": True,
                                        "text": " Next ",
                                        "href": '',
                                        "btn_class": 'btn-hhcBlue',
                                        "btn_id": 'btn_submit'},
                                   ]}

        context['ajaxURL'] = reverse_lazy('application:incomeBackground')

        return context

    def form_valid(self, form):
        obj = form.save()

        if self.request.is_ajax():
            return HttpResponse(json.dumps({"success": "Form Saved"}), content_type='application/json', status=200)
        else:
            return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return HttpResponse(json.dumps({"error": "Form Invalid"}), content_type='application/json', status=400)
        else:
            return super().form_invalid(form)


class BankView(SessionRequiredMixin, ApplicationHelper, UpdateView):
    template_name = 'application/interface/bank_details.html'
    form_class = BankForm
    success_url = reverse_lazy('application:declarations')

    def get_context_data(self, **kwargs):
        context = super(BankView, self).get_context_data(**kwargs)
        context['title'] = 'Bank details'
        obj = self.get_object()
        context['obj'] = obj

        context['menuBarItems'] = {"data": [
            {"button": False,
             "text": "Back",
             "href": reverse_lazy('application:income'),
             "btn_class": 'btn-outline-hhcBlue',
             "btn_id": 'btn_back'},
            {"button": True,
             "text": "Next",
             }]}

        return context


class DeclarationsView(SessionRequiredMixin, ApplicationHelper, UpdateView):
    template_name = 'application/interface/declarations.html'
    form_class = SigningForm
    success_url = reverse_lazy('application:nextSteps')

    def get_context_data(self, **kwargs):
        context = super(DeclarationsView, self).get_context_data(**kwargs)
        context['title'] = 'Declarations'
        obj = self.get_object()
        context['obj'] = obj

        context['menuBarItems'] = {
            "float": True, "data": [
                {"button": False,
                 "text": "Back",
                 "href": reverse_lazy('application:income'),
                 "btn_class": 'btn-outline-hhcBlue',
                 "btn_id": 'btn_back'},
                {"button": True,
                 "text": "Next",
                 }]}

        return context

    def get_form_kwargs(self, **kwargs):
        kwargs = super(DeclarationsView, self).get_form_kwargs(**kwargs)
        obj = self.get_object()
        if obj.clientType2 == clientTypesEnum.BORROWER.value:
            kwargs.update({'jointSigning': True,
                           'customerName_1': obj.firstname_1 + " " + obj.surname_1,
                           'customerName_2': obj.firstname_2 + " " + obj.surname_2, })
        else:
            kwargs.update({'jointSigning': False,
                           'customerName_1': obj.firstname_1 + " " + obj.surname_1})

        return kwargs

    def form_valid(self, form):
        pin = form.cleaned_data['pin']

        obj = self.get_object()
        if (pin == obj.pin) and (timezone.now() < obj.pinExpiry):
            obj = form.save(commit=False)
            obj.signingDate = timezone.now()
            obj.ip_address = self.request.META['REMOTE_ADDR']
            obj.appStatus = appStatusEnum.SUBMITTED.value
            obj.save()

            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(self.request, "Pin does not match, please re-enter or send another")

            return HttpResponseRedirect(self.request.path_info)


class NextStepsView(SessionRequiredMixin, TemplateView):
    template_name = 'application/interface/nextSteps.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #end session
        self.request.session.flush()

        context['title'] = 'Thank you - application received'
        context['subtitle'] = 'Next steps'

        context['menuBarItems'] = {"data": [

            {"button": False,
             "text": " Exit ",
             "href": reverse_lazy('application:exit'),
             "btn_class": 'btn-hhcBlue',
             "btn_id": 'btn_submit'},
        ]}

        return context
