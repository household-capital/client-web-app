# Python Imports
import json

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.views.generic import UpdateView,  ListView, TemplateView, View
from django.urls import reverse_lazy


# Third-party Imports
from config.celery import app


# Local Application Imports
from apps.lib.site_Enums import caseStagesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.site_Utilities import updateNavQueue
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.enquiry.models import Enquiry

from .models import WebCalculator, WebContact
from .forms import WebContactDetail


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

        context['caseStagesEnum'] = caseStagesEnum
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
        context['resultsLoanBalance'] = loanProj.getResultsList('BOPLoanValue')['data']
        context['resultsHomeEquityPC'] = loanProj.getResultsList('BOPHomeEquityPC')['data']
        context['resultsHomeImages'] = \
            loanProj.getImageList('BOPHomeEquityPC', settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')['data']
        context['resultsHouseValue'] = loanProj.getResultsList('BOPHouseValue', imageSize=100, imageMethod='lin')[
            'data']

        return context

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

        # Update Nav Queues
        updateNavQueue(self.request)

        return context

class CalcCreateEnquiry(LoginRequiredMixin, UpdateView):
    # This view does not render it creates and enquiry, sends an email, updates the calculator
    # and redirects to the Enquiry ListView
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'calculator/email/email_cover_calculator.html'

    def get(self, request, *args, **kwargs):

        user = self.request.user
        if not user.profile.calendlyUrl:
            messages.error(self.request, "You are not set-up to action this type of enquiry")
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

            #Build context
            email_context = {}

            #  Strip name
            if obj.name:
                if " " in obj.name:
                    customerFirstName, surname = obj.name.split(" ", 1)
                else:
                    customerFirstName = obj.name
                if len(customerFirstName) < 2:
                    customerFirstName = None

            email_context['customerFirstName'] = customerFirstName

            #  Get Rates
            email_context['loanRate']= ECONOMIC['interestRate'] + ECONOMIC['lendingMargin']
            email_context['compRate'] = email_context['loanRate'] + ECONOMIC['comparisonRateIncrement']

            email_context['user'] = request.user
            email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
            email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

            subject, from_email, to, bcc = "Household Capital: Your Personal Summary", \
                                           self.request.user.email, \
                                           obj.email, \
                                           self.request.user.email
            text_content = "Text Message"
            attachFilename = 'HHC-CalculatorSummary.pdf'

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

        app.send_task('Create_SF_Lead', kwargs={'enqUID': str(enq_obj.enqUID)})

        return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))


# Calculator Delete View (Delete View)
class CalcDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        obj = WebCalculator.objects.filter(calcUID=kwargs['uid']).get()
        obj.actioned = 1
        obj.save(update_fields=['actioned'])
        messages.success(self.request, "Web Calculator Enquiry deleted")

        return HttpResponseRedirect(reverse_lazy('calculator:calcList'))

# Contact Queue
class ContactListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    template_name = 'calculator/contactList.html'
    context_object_name = 'object_list'
    model = WebContact

    def get_queryset(self, **kwargs):
        queryset = super(ContactListView, self).get_queryset()

        queryset = queryset.order_by('-timestamp')[:200]

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContactListView, self).get_context_data(**kwargs)
        context['title'] = 'Web Contact Queue'

        # Update Nav Queues
        updateNavQueue(self.request)

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

        obj = WebContact.objects.filter(contUID=kwargs['uid']).get()
        obj.actioned = 1
        obj.save(update_fields=['actioned'])
        messages.success(self.request, "Contact deleted")

        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))

# Convert Contact
class ContractConvertView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        contObj = WebContact.objects.filter(contUID=kwargs['uid']).get()

        #Check whether user can create enquiry
        if request.user.profile.isCreditRep:
            userRef = request.user
        else:
            userRef = None

        enquiryNotes = ''.join(filter(None,[contObj.message, chr(13), contObj.actionNotes]))

        #Create enquiry
        enq_obj = Enquiry.objects.create(user=userRef,
                                         referrer=directTypesEnum.WEB_ENQUIRY.value,
                                         name = contObj.name,
                                         email = contObj.email,
                                         phoneNumber = contObj.phone,
                                         enquiryNotes = enquiryNotes)
        enq_obj.save()

        # Mark contact as closed
        contObj.actioned = True
        contObj.actionedBy = request.user
        contObj.actionDate = timezone.now()
        contObj.actionNotes = ''.join(filter(None,[contObj.actionNotes, "** converted to enquiry"]))
        contObj.save(update_fields=['actioned', 'actionedBy','actionDate', 'actionNotes'])

        messages.success(self.request, "Contact converted")
        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))


