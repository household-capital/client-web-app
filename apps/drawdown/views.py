# Python Imports
import datetime
import json
import urllib.parse
from urllib.parse import urljoin

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import get_template
from django.views.generic import UpdateView, CreateView, TemplateView, View
from django.urls import reverse_lazy

# Local Application Imports
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection

from apps.lib.site_Logging import write_applog
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.site_Enums import caseStagesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum


from apps.application.models import IncomeCalculator
from .forms import CalcInputIncomeForm, CalcOutputIncomeForm


class CalculatorHelper:

    def send_success_email(self, email_template, email_address, name):

        customer_first_name = None
        if name:
            if " " in name:
                customer_first_name, surname = name.split(" ", 1)
            else:
                customer_first_name = name
            if len(customer_first_name) < 2:
                customer_first_name = None

        # Send email on success
        email_context = {
            'absolute_url': urljoin(settings.SITE_URL, settings.STATIC_URL),
            'absolute_media_url': urljoin(settings.SITE_URL, settings.MEDIA_URL),
            'customerFirstName': customer_first_name
        }
        subject, from_email, to = "Household Capital: Calculator Enquiry", settings.INFO_EMAIL, email_address
        text_content = "Calculator Enquiry Received"

        try:
            html = get_template(email_template)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            pass


class IncomeInputView(CreateView):
    template_name = 'drawdown/input/income_input.html'
    form_class = CalcInputIncomeForm
    url_location = 'drawdown:incomeOutput'

    model = IncomeCalculator
    form_name = 'calculator-data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loanTypesEnum'] = loanTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum

        # Add specifically named form to context
        if self.form_name not in context:
            context[self.form_name] = self.form_class()

        return context

    def get_object(self, queryset=None):
        uid = self.kwargs['uid']
        queryset = IncomeCalculator.objects.queryset_byUID(str(uid))
        obj = queryset.get()
        return obj

    def form_invalid(self, form):
        data = self.get_context_data(form=form)
        return self.render_to_response(data)

    def form_valid(self, form):
        client_dict = form.cleaned_data
        obj = form.save(commit=False)

        # Loan validation
        loan_obj = LoanValidator(client_dict)
        chk_opp = loan_obj.validateLoan()


        obj.valuation = int(form.cleaned_data['valuation'])

        if chk_opp['status'] == "Error":
            obj.status = 0
            obj.errorText = chk_opp['responseText']
            obj.save()

            if 'Postcode' in chk_opp['responseText']:
                return HttpResponseRedirect(
                    reverse_lazy('drawdown:incomeOutputPostcode', kwargs={'uid': str(obj.calcUID)})
                )

            if 'Youngest' in chk_opp['responseText']:
                return HttpResponseRedirect(
                    reverse_lazy('drawdown:incomeOutputAge', kwargs={'uid': str(obj.calcUID)})
                )

            messages.error(self.request, self.client_text(chk_opp['responseText']))

            return self.render_to_response(self.get_context_data(form=form))

        else:
            obj.status = 1
            obj.maxLoanAmount = chk_opp['data']['maxLoan']
            obj.maxLVR = chk_opp['data']['maxLVR']
            obj.maxDrawdownAmount = chk_opp['data']['maxDrawdown']
            obj.maxDrawdownMonthly = chk_opp['data']['maxDrawdownMonthly']
            obj.save()

            success = reverse_lazy(self.url_location, kwargs={'uid': str(obj.calcUID)})
            return HttpResponseRedirect(success)

    def client_text(self, input_string):

        response_text = {
            'Minimum Loan Size cannot be met': 'Unfortunately, our minimum loan size would not be met',
        }

        if input_string in response_text:
            return response_text[input_string]
        else:
            return "Calculation cannot be performed at this time."


class IncomeOutputView(UpdateView):
    template_name = 'drawdown/output/income_output.html'
    form_class = CalcOutputIncomeForm

    model = IncomeCalculator
    caseUID = ""
    email_template = 'calculator/email/email_calc_response.html'
    success_url = '/thank-you'

    def get(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
            return super().get(self, request, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy("calculator:input"))

    def post(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
        return super().post(self, request, **kwargs)

    def get_object(self, queryset=None):
        queryset = IncomeCalculator.objects.queryset_byUID(self.caseUID)
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


#### TEMP

        obj = self.get_object()
        client_dict = obj.__dict__
        loanObj = LoanValidator(client_dict)
        chkOpp = loanObj.validateLoan()
        loanStatus = loanObj.getStatus()['data']

        combinedDict ={}
        combinedDict.update(client_dict)
        combinedDict['totalLoanAmount'] = client_dict['maxLoanAmount']
        combinedDict['interestRate'] = ECONOMIC['interestRate']
        combinedDict['lendingMargin']  = ECONOMIC['lendingMargin']
        combinedDict['inflationRate'] = ECONOMIC['inflationRate']
        combinedDict['housePriceInflation'] = ECONOMIC['housePriceInflation']

        loanProj = LoanProjection()
        result = loanProj.create(combinedDict)
        print(result)
        proj_data = loanProj.getFutureIncomeEquityArray(increment=100)['data']
        context['sliderData'] = json.dumps(proj_data['dataArray'])
        context['futHomeValue'] = proj_data['futHomeValue']
        context['sliderPoints'] = proj_data['intervals']
        print(context['sliderData'])

        context["obj"] = obj
        context.update(loanStatus)

        context["transfer_img"] = settings.STATIC_URL + "img/icons/transfer_%s_icon.png" % context['maxLVRPercentile']


        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        #Fail safe in case interaction has been retrieved (very long time before leave details)
        obj.retrieved = 0
        obj.retrievedDate = None
        obj.save()

        context = self.get_context_data(form=form)
        obj = self.get_object()

        # Send email on success
        #self.send_success_email(self.email_template, obj.email, obj.name)

        return HttpResponseRedirect(self.success_url + '?calcUID=' + urllib.parse.quote(str(obj.calcUID), safe="~"))


from apps.lib.api_Mappify import apiMappify

class AddressComplete(View):

    def post(self, request, *args, **kwargs):
        #Apex View - provides auto address complete list using Mappify

        address = request.POST['address']

        api = apiMappify()
        result = api.autoComplete(address)
        # Split street address component
        for item in result:
            item['streetComponent'], remainder = item['streetAddress'].rsplit(",", 1)

        return HttpResponse(json.dumps(result), content_type='application/json')


class IncomeOutputPostcode(TemplateView):
    """ Invalid postcode view"""
    template_name = 'drawdown/output/income_output_postcode.html'

    def get_object(self, queryset=None):
        queryset = IncomeCalculator.objects.queryset_byUID(str(self.kwargs['uid']))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["obj"] = obj
        return context

class IncomeOutputAge(CalculatorHelper, UpdateView):
    """ Invalid age view - provides results as if 60 and an opportunity to leave an email"""

    template_name = 'drawdown/output/income_output_age.html'
    model = IncomeCalculator
    caseUID = ""
    form_class = CalcOutputIncomeForm
    email_template = 'drawdown/email/email_calc_response_invalid.html'


    def get(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
            return super().get(self, request, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy("drawdown:incomeInput"))

    def post(self, request, **kwargs):
        self.caseUID = str(kwargs['uid'])
        return super().post(self, request, **kwargs)

    def get_object(self, queryset=None):
        queryset = IncomeCalculator.objects.queryset_byUID(self.caseUID)
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Override the loan object with minimum age 60/65 couple


        # override age and recalculate results
        obj = self.get_object()
        client_dict = obj.__dict__
        client_dict["age_1"] = 60
        if client_dict["age_2"]:
            context["isCouple"] = True
            context["minCoupleAge"] = LOAN_LIMITS['minCoupleAge']
            client_dict["age_2"] = LOAN_LIMITS['minCoupleAge']
            if client_dict["age_1"] < LOAN_LIMITS['minCoupleAge']:
                client_dict["age_1"] = LOAN_LIMITS['minCoupleAge']

        loan_obj = LoanValidator(client_dict)
        chk_opp = loan_obj.validateLoan()
        loan_status = loan_obj.getStatus()['data']

        # Even with correct age - loan may still be invalid
        if chk_opp['status'] == "Error":
            context["isError"] = True
            context["errorText"] = self.client_text(chk_opp['responseText'])
            return context

        context['maxLoanAmount'] = chk_opp['data']['maxLoan']
        context['valuation'] = obj.valuation
        context.update(loan_status)
        context["transfer_img"] = settings.STATIC_URL + 'img/icons/transfer_%s_icon.png' % context['maxLVRPercentile']

        return context

    def client_text(self, input_string):

        response_text = {
            'Invalid Postcode': 'Unfortunately, we do not operate in this postcode',
            'Minimum Loan Size cannot be met': 'Unfortunately, our minimum loan size would not be met',
        }

        if input_string in response_text:
            return response_text[input_string]
        else:
            return "Calculation cannot be performed at this time."

    def form_valid(self, form):
        obj = form.save(commit=True)
        context = self.get_context_data(form=form)
        context['success'] = True

        obj = self.get_object()

        # Send email on success
        self.send_success_email(self.email_template, obj.email, obj.name)

        context['redirectURL'] = settings.SITE_URL
        context['redirect'] = True
        context['redirectMessage'] = "Thank you - we'll be back to you shortly"

        return self.render_to_response(context)
