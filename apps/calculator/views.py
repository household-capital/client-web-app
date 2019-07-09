# Python Imports
import json

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.core.files import File
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView, CreateView, ListView, TemplateView, View
from django.urls import reverse_lazy


# Third-party Imports

# Local Application Imports
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.site_Enums import caseTypesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum
from apps.lib.site_Utilities import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.enquiry.models import Enquiry

from .models import WebCalculator, WebContact
from .forms import CalcInputForm, CalcOutputForm, WebContactForm, WebContactDetail



# NEW VIEWS

campaignURLs = ['/equity-mortgage-release/',
                '/centrelink-pension-information/',
                '/aged-care-financing/',
                '/reverse-mortgages/',
                '/superannuation-and-retirement/',
                '/retirement-planning/',
                '/refinance-existing-mortgage/',
                ]

campaignRedirectSuffix='-thank-you'


@method_decorator(csrf_exempt, name='dispatch')
class WebContactView(CreateView):
    template_name = 'calculator/contact.html'
    model = WebContact
    form_class = WebContactForm

    @xframe_options_exempt
    def get(self, request, *args, **kwargs):
        return super(WebContactView, self).get(self, request, *args, **kwargs)

    @xframe_options_exempt
    def post(self, request, *args, **kwargs):
        return super(WebContactView, self).post(self, request, *args, **kwargs)

    def form_valid(self, form):
        clientDict = form.cleaned_data
        sendFlag=True

        if clientDict['content']:
            sendFlag=False

        if '<a href' in clientDict['message']:
            sendFlag = False

        if sendFlag==True:
            obj = form.save(commit=True)

        context = {}
        context['submitted'] = True

        return self.render_to_response(context)


@method_decorator(csrf_exempt, name='dispatch')
class CalcStartView(CreateView):
    template_name = 'calculator/calc_input.html'
    model = WebCalculator
    form_class = CalcInputForm

    @xframe_options_exempt
    def get(self, request, *args, **kwargs):
        clientId = str(request.GET.get('clientId'))

        return super(CalcStartView, self).get(self, request, *args, **kwargs)

    @xframe_options_exempt
    def post(self, request, *args, **kwargs):
        return super(CalcStartView, self).post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CalcStartView, self).get_context_data(**kwargs)
        context['loanTypesEnum'] = loanTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum

        return context

    def get_object(self, queryset=None):
        uid = self.kwargs['uid']
        queryset = WebCalculator.objects.queryset_byUID(str(uid))
        obj = queryset.get()
        return obj

    def form_invalid(self, form):
        data = self.get_context_data(form=form)

        return self.render_to_response(data)

    def form_valid(self, form):
        clientDict = form.cleaned_data
        obj = form.save(commit=False)

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()

        obj.valuation = int(form.cleaned_data['valuation'])
        clientId = str(self.request.GET.get('clientId',None))
        clientStr = ""
        if clientId != None and clientId !='None':
            clientStr = "?clientId=" + clientId

        if chkOpp['status'] == "Error":
            obj.status = 0
            obj.errorText = chkOpp['responseText']
            obj.save()

            if 'Postcode' in chkOpp['responseText']:
                return HttpResponseRedirect(reverse_lazy('calculator:calcOutputPostcode',
                                                         kwargs={'uid': str(obj.calcUID)}) + clientStr)

            if 'Youngest' in chkOpp['responseText']:
                return HttpResponseRedirect(reverse_lazy('calculator:calcOutputAge',
                                                         kwargs={'uid': str(obj.calcUID)}) + clientStr)

            messages.error(self.request, self.clientText(chkOpp['responseText']))

            return self.render_to_response(self.get_context_data(form=form))

        else:
            obj.status = 1
            obj.maxLoanAmount = chkOpp['data']['maxLoan']
            obj.maxLVR = chkOpp['data']['maxLVR']
            obj.save()

            success = reverse_lazy('calculator:calcResults',
                                   kwargs={'uid': str(obj.calcUID)}) + clientStr
            return HttpResponseRedirect(success)

    def clientText(self, inputString):

        responseText = {
            'Invalid Postcode': 'Unfortunately, we do not operate in this postcode',
            'Youngest borrower must be 60': 'This product is designed for borrowers older than 60',
            'Youngest joint borrower must be 65': 'For couples, the youngest borrower must be at least 65',
            'Minimum Loan Size cannot be met': 'Unfortunately, our minimum loan size would not be met',
        }

        if inputString in responseText:
            return responseText[inputString]
        else:
            return "Calculation cannot be performed at this time."


@method_decorator(csrf_exempt, name='dispatch')
class CalcResultsView(UpdateView):
    template_name = 'calculator/calc_output.html'
    model = WebCalculator
    caseUID = ""
    form_class = CalcOutputForm
    email_template='calculator/email/email_calc_response.html'

    @xframe_options_exempt
    def get(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
            return super(CalcResultsView, self).get(self, request, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy("calculator:input"))

    @xframe_options_exempt
    def post(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
        return super(CalcResultsView, self).post(self, request, **kwargs)

    def get_object(self, queryset=None):
        queryset = WebCalculator.objects.queryset_byUID(self.caseUID)
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CalcResultsView, self).get_context_data(**kwargs)

        obj = self.get_object()
        clientDict = obj.__dict__
        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()
        loanStatus=loanObj.getStatus()['data']


        context['topUpMax']= min(chkOpp['data']['maxTopUp'], chkOpp['data']['maxLoan'])
        context['refiMax'] = min(chkOpp['data']['maxRefi'], chkOpp['data']['maxLoan'])
        context['liveMax']= min(chkOpp['data']['maxReno'], chkOpp['data']['maxLoan'])
        context['giveMax']= min(chkOpp['data']['maxGive'], chkOpp['data']['maxLoan'])
        context['careMax']= min(chkOpp['data']['maxCare'], chkOpp['data']['maxLoan'])
        context['loanRate']=ECONOMIC['interestRate']+ECONOMIC['lendingMargin']

        context["obj"] = obj
        context.update(loanStatus)

        context["transfer_img"] = settings.STATIC_URL + "img/icons/transfer_" + str(
            context['maxLVRPercentile']) + "_icon.png"

        return context

    def form_valid(self, form):
        obj = form.save(commit=True)

        clientId = str(self.request.GET.get('clientId', None))
        clientStr = ""
        if clientId != None and clientId != 'None':
            clientStr = "?clientId=" + clientId

        context = self.get_context_data(form=form)
        obj = self.get_object()

        #Send email on success
        email_context = {}
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL
        subject, from_email, to = "Household Capital: Calculator Enquiry", "info@householdcapital.com", obj.email
        text_content = "Calculator Enquiry Received"

        try:
            html = get_template(self.email_template)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            pass

        #Redirect on success
        context['redirect'] = True

        context['redirectURL'] = "https://householdcapital.com.au/" + clientStr
        context['redirectMessage'] = "Thank you - we'll be back to you shortly"

        if obj.referrer:
            for url in campaignURLs:
                if url in obj.referrer:
                    context['redirectURL'] = obj.referrer.replace(url, url[:-1] + campaignRedirectSuffix) + clientStr
                    context['redirectMessage'] = None

        return self.render_to_response(context)


@method_decorator(csrf_exempt, name='dispatch')
class CalcOutputPostcode(UpdateView):
    template_name = 'calculator/calc_output_postcode.html'
    model = WebCalculator
    caseUID = ""
    form_class = CalcOutputForm
    email_template='calculator/email/email_calc_response_invalid.html'


    @xframe_options_exempt
    def get(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
            return super(CalcOutputPostcode, self).get(self, request, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy("calculator:input"))

    @xframe_options_exempt
    def post(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
        return super(CalcOutputPostcode, self).post(self, request, **kwargs)

    def get_object(self, queryset=None):
        queryset = WebCalculator.objects.queryset_byUID(self.caseUID)
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CalcOutputPostcode, self).get_context_data(**kwargs)

        obj = self.get_object()
        context['obj'] = obj
        return context

    def form_valid(self, form):
        obj = form.save(commit=True)
        obj.save(update_fields=['email', 'name'])
        context = self.get_context_data(form=form)
        context['success'] = True

        clientId = str(self.request.GET.get('clientId', None))
        clientStr = ""
        if clientId != None:
            clientStr = "?clientId=" + clientId

        obj = self.get_object()

        #Send email on success
        email_context = {}
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL
        subject, from_email, to = "Household Capital: Calculator Enquiry", "info@householdcapital.com", obj.email
        text_content = "Calculator Enquiry Received"

        try:
            html = get_template(self.email_template)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            pass

        context['redirect'] = True
        context['redirectMessage'] = "Thank you - we'll be back to you shortly"

        if obj.referrer:
            for url in campaignURLs:
                if url in obj.referrer:
                    context['redirectURL'] = obj.referrer.replace(url, url[:-1] + campaignRedirectSuffix + clientStr)
        else:
            context['redirectURL'] = "https://householdcapital.com.au/" + clientStr

        return self.render_to_response(context)



@method_decorator(csrf_exempt, name='dispatch')
class CalcOutputAge(UpdateView):
    template_name = 'calculator/calc_output_age.html'
    model = WebCalculator
    caseUID = ""
    form_class = CalcOutputForm
    email_template='calculator/email/email_calc_response_invalid.html'

    @xframe_options_exempt
    def get(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
            return super(CalcOutputAge, self).get(self, request, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy("calculator:input"))

    @xframe_options_exempt
    def post(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID = str(kwargs['uid'])
        return super(CalcOutputAge, self).post(self, request, **kwargs)

    def get_object(self, queryset=None):
        queryset = WebCalculator.objects.queryset_byUID(self.caseUID)
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CalcOutputAge, self).get_context_data(**kwargs)
        # Override the loan object with mimimum age 60/65 couple

        obj = self.get_object()
        clientDict = obj.__dict__
        clientDict["age_1"] = 60
        if clientDict["age_2"]:
            context["isCouple"] = True
            context["minCoupleAge"] = LOAN_LIMITS['minCoupleAge']
            clientDict["age_2"] = LOAN_LIMITS['minCoupleAge']
            if clientDict["age_1"] < LOAN_LIMITS['minCoupleAge']:
                clientDict["age_1"] = LOAN_LIMITS['minCoupleAge']

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()
        loanStatus = loanObj.getStatus()['data']

        if chkOpp['status'] == "Error":
            # Even with correct age - loan may still be invalid
            context["isError"] = True
            context["errorText"] = self.clientText(chkOpp['responseText'])
            return context

        context['maxLoanAmount'] = chkOpp['data']['maxLoan']
        maxLVR = chkOpp['data']['maxLVR']
        context['valuation'] = obj.valuation

        context.update(loanStatus)

        context["transfer_img"] = settings.STATIC_URL + "img/icons/transfer_"+str(context['maxLVRPercentile'])+"_icon.png"

        return context

    def clientText(self, inputString):

        responseText = {
            'Invalid Postcode': 'Unfortunately, we do not operate in this postcode',
            'Youngest borrower must be 60': 'This product is designed for borrowers older than 60',
            'Youngest joint borrower must be 65': 'For couples, the youngest borrower must be at least 65',
            'Minimum Loan Size cannot be met': 'Unfortunately, our minimum loan size would not be met',
        }

        if inputString in responseText:
            return responseText[inputString]
        else:
            return "Calculation cannot be performed at this time."

    def form_valid(self, form):
        obj = form.save(commit=True)
        context = self.get_context_data(form=form)
        context['success'] = True

        clientId = str(self.request.GET.get('clientId'))
        clientId = ""
        if clientId != "None":
            clientId = "?clientId=" + clientId

        obj = self.get_object()

        context['redirect'] = True
        context['redirectMessage'] = "Thank you - we'll be back to you shortly"

        # Send email on success
        email_context = {}
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL
        subject, from_email, to = "Household Capital: Calculator Enquiry", "info@householdcapital.com", obj.email
        text_content = "Calculator Enquiry Received"

        try:
            html = get_template(self.email_template)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            pass

        if obj.referrer:
            for url in campaignURLs:
                if url in obj.referrer:
                    context['redirectURL'] = obj.referrer.replace(url, url[:-1] + "-thank-you" + clientId)
        else:
            context['redirectURL'] = "https://householdcapital.com.au/" + clientId

        return self.render_to_response(context)


class CalcSummaryNewPdf(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name = 'calculator/document/calculator_new_summary.html'

    def get_context_data(self, **kwargs):
        context = super(CalcSummaryNewPdf, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])

        obj = Enquiry.objects.queryset_byUID(enqUID).get()

        context["obj"] = obj

        clientDict = obj.__dict__
        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()
        loanStatus = loanObj.getStatus()['data']

        context.update(loanStatus)

        context["transfer_img"] = settings.STATIC_URL + "img/icons/transfer_" + str(
            context['maxLVRPercentile']) + "_icon.png"

        context['caseTypesEnum'] = caseTypesEnum
        context['loanTypesEnum'] = loanTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum
        context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL

        totalLoanAmount = 0
        if obj.calcTotal == None or obj.calcTotal == 0:
            totalLoanAmount = obj.maxLoanAmount
        else:
            totalLoanAmount = min(obj.maxLoanAmount, obj.calcTotal)
        context['totalLoanAmount'] = totalLoanAmount

        context['totalInterestRate'] = ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
        context['housePriceInflation'] = ECONOMIC['housePriceInflation']
        context['comparisonRate'] = context['totalInterestRate'] + ECONOMIC['comparisonRateIncrement']

        # Get Loan Projections
        clientDict = Enquiry.objects.dictionary_byUID(enqUID)
        clientDict.update(ECONOMIC)
        clientDict['totalLoanAmount'] = totalLoanAmount
        clientDict['maxNetLoanAmount'] = obj.maxLoanAmount
        loanProj = LoanProjection()
        result = loanProj.create(clientDict,frequency=12)

        if obj.payIntAmount:
            result = loanProj.calcProjections(makeIntPayment=True)
        else:
            result = loanProj.calcProjections()

        # Build results dictionaries

        # Check for no top-up Amount

        context['resultsAge'] = loanProj.getResultsList('BOPAge')['data']
        context['resultsHomeEquity'] = loanProj.getResultsList('BOPHomeEquity')['data']
        context['resultsHomeEquityPC'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages'] = \
            loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
        context['resultsHouseValue'] = loanProj.getResultsList('BOPHouseValue', imageSize=100, imageMethod='lin')[
            'data']

        return context


class Test(View):

    def get(self, request, *args, **kwargs):
        enqUID = str(kwargs['uid'])

        sourcePath = 'https://householdcapital.app/calculator/calcSummaryNewPdf/'
        targetPath = settings.MEDIA_ROOT + "/customerReports/"


        pdf = pdfGenerator(enqUID)
        pdf.createPdfFromUrl(sourcePath + enqUID, "",
                             targetPath + "test" + enqUID[-12:] + ".pdf")

        response = HttpResponse(pdf.getContent(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="LoanSummary.pdf"'
        return response


# Calculator Queue

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


class CalcListView(LoginRequiredMixin, ListView):
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

        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context


class CalcMarkSpam(LoginRequiredMixin, UpdateView):
    # This view does not render it updates the calculator and redirects to the ListView
    context_object_name = 'object_list'
    model = WebCalculator

    def get(self, request, *args, **kwargs):
        calcUID = str(kwargs['uid'])
        queryset = WebCalculator.objects.queryset_byUID(str(calcUID))
        obj = queryset.get()
        obj.actioned = -1
        obj.save(update_fields=['actioned'])
        return HttpResponseRedirect(reverse_lazy("calculator:calcList"))


class CalcCreateEnquiry(LoginRequiredMixin, UpdateView):
    # This view does not render it creates and enquiry, sends an email, updates the calculator
    # and redirects to the Enquiry ListView
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'calculator/email/email_cover_calculator.html'

    def get(self, request, *args, **kwargs):

        user = self.request.user
        if not user.profile.isCreditRep:
            messages.error(self.request, "You must be a Credit Representative to action this type of enquiry")
            return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

        calcUID = str(kwargs['uid'])
        queryset = WebCalculator.objects.queryset_byUID(str(calcUID))
        obj = queryset.get()

        calcDict = WebCalculator.objects.dictionary_byUID(str(calcUID))

        # Create enquiry using WebCalculator Data
        # Remove certain items from the dictionary
        referrer = calcDict['referrer']

        popList = ['calcUID', 'actionedBy', 'id', 'referrer', 'updated', 'timestamp', 'actioned']
        for item in popList:
            calcDict.pop(item)



        enq_obj = Enquiry.objects.create(user=user, referrer=directTypesEnum.WEB_CALCULATOR.value, referrerID=referrer,
                                         **calcDict)
        enq_obj.save()

        if enq_obj.status:

            # PRODUCE PDF REPORT
            sourceUrl = 'https://householdcapital.app/calculator/calcSummaryNewPdf/' + str(enq_obj.enqUID)
            targetFileName = settings.MEDIA_ROOT + "/enquiryReports/Enquiry-" + str(enq_obj.enqUID)[
                                                                                -12:] + ".pdf"

            pdf = pdfGenerator(calcUID)
            created, text = pdf.createPdfFromUrl(sourceUrl, 'CalculatorSummary.pdf', targetFileName)

            if not created:
                messages.error(self.request, "Enquiry created - but email not sent")

                obj.actioned = 1  # Actioned=1, Spam=-1
                obj.save(update_fields=['actioned'])

                return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

            try:
                # SAVE TO DATABASE (Enquiry Model)
                localfile = open(targetFileName, 'rb')

                qsCase = Enquiry.objects.queryset_byUID(str(enq_obj.enqUID))
                qsCase.update(summaryDocument=File(localfile), )

                pdf_contents = localfile.read()
            except:
                write_applog("ERROR", 'calcCreateEnquiry', 'get',
                             "Failed to save Calc Summary in Database: " + str(enq_obj.enqUID))

            email_context = {}
            email_context['user'] = request.user
            email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
            email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

            subject, from_email, to, bcc = "Household Capital: Personal Summary", \
                                           self.request.user.email, \
                                           obj.email, \
                                           self.request.user.email
            text_content = "Text Message"
            attachFilename = 'HHC-CalculatorSummary'

            sent = pdf.emailPdf(self.template_name, email_context, subject, from_email, to, bcc, text_content,
                                    attachFilename)

            if sent:
                messages.success(self.request, "Client has been emailed and enquiry created")
            else:
                messages.error(self.request, "Enquiry created - but email not sent")

        else:
                messages.error(self.request, "Age or Postcode Restriction - please respond to customer")

        obj.actioned = 1  # Actioned=1, Spam=-1
        obj.save(update_fields=['actioned'])

        return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))


# Contact Queue
class ContactListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    template_name = 'calculator/contactList.html'
    context_object_name = 'object_list'
    model = WebContact

    def get_queryset(self, **kwargs):
        queryset = super(ContactListView, self).get_queryset()

        queryset = queryset.order_by('-timestamp')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContactListView, self).get_context_data(**kwargs)
        context['title'] = 'Web Contact Queue'

        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context


# Contact Detail View
class ContactDetailView(LoginRequiredMixin, UpdateView):
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


class ContactActionView(LoginRequiredMixin, View):

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
class ContactDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            WebContact.objects.filter(contUID=kwargs['uid']).delete()
            messages.success(self.request, "Contact deleted")

        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))


