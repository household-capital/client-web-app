# Python Imports
import os

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.core.files import File
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.template.loader import get_template
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, TemplateView, View

# Local Application Imports
from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case
from apps.lib.api_Salesforce import apiSalesforce

from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_Enums import caseTypesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import pdfGenerator
from .forms import EnquiryForm, EnquiryDetailForm, ReferrerForm, EnquiryCloseForm
from .models import Enquiry


# VIEWS

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


class ReferrerRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(ReferrerRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)


# ENQUIRY

# Enquiry List View
class EnquiryListView(LoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'enquiry/enquiryList.html'
    context_object_name = 'object_list'
    model = Enquiry

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search paramater
        queryset = super(EnquiryListView, self).get_queryset()
        queryset = queryset.filter(actioned=0, followUp__isnull=True)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = super(EnquiryListView, self).get_queryset()
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phoneNumber__icontains=search) |
                Q(postcode__icontains=search) |
                Q(enquiryNotes__icontains=search)
            ).exclude(actioned=-1)

        # ...and for open my items
        if self.request.GET.get('myEnquiries') == "True":
            queryset = super(EnquiryListView, self).get_queryset().filter(user=self.request.user).exclude(actioned=-1)

        queryset = queryset.order_by('-updated')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(EnquiryListView, self).get_context_data(**kwargs)
        context['title'] = 'Enquiries'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        if self.request.GET.get('myEnquiries'):
            context['myEnquiries'] = self.request.GET.get('myEnquiries')
        else:
            context['myEnquiries'] = False

        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context


# Enquiry Create View
class EnquiryCreateView(LoginRequiredMixin, CreateView):
    template_name = "enquiry/enquiry.html"
    form_class = EnquiryForm
    model = Enquiry

    def get_object(self, queryset=None):
        enqUID = str(self.kwargs['uid'])
        queryset = Enquiry.objects.queryset_byUID(str(enqUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryCreateView, self).get_context_data(**kwargs)
        context['title'] = 'New Enquiry'

        return context

    def form_valid(self, form):
        clientDict = form.cleaned_data
        obj = form.save(commit=False)

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()

        if obj.user == None and self.request.user.profile.isCreditRep == True:
            obj.user = self.request.user

        if chkOpp['status'] == "Error":
            obj.status = 0
            obj.errorText = chkOpp['responseText']
            obj.save()
        else:
            obj.status = 1
            obj.maxLoanAmount = chkOpp['data']['maxLoan']
            obj.maxLVR = chkOpp['data']['maxLVR']
            obj.save()

        messages.success(self.request, "Enquiry Saved")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))


# Enquiry Detail View
class EnquiryUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "enquiry/enquiry.html"
    form_class = EnquiryDetailForm
    model = Enquiry

    def get_object(self, queryset=None):
        enqUID = str(self.kwargs['uid'])
        queryset = Enquiry.objects.queryset_byUID(str(enqUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryUpdateView, self).get_context_data(**kwargs)
        context['title'] = 'Enquiry'

        clientDict = Enquiry.objects.dictionary_byUID(str(self.kwargs['uid']))
        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()
        context['status'] = chkOpp
        queryset = Enquiry.objects.queryset_byUID(str(self.kwargs['uid']))
        obj = queryset.get()
        context['obj'] = obj
        context['isUpdate'] = True

        print(chkOpp)

        return context

    def form_valid(self, form):
        clientDict = form.cleaned_data
        obj = form.save(commit=False)

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()

        calcTotal = 0
        purposeList = ['calcTopUp', 'calcRefi', 'calcLive', 'calcGive', 'calcCare']

        for purpose in purposeList:
            if form.cleaned_data[purpose]:
                setattr(obj, purpose, form.cleaned_data[purpose])
                setattr(obj, purpose.replace('calc', 'is'), True)
                calcTotal += int(form.cleaned_data[purpose])

        obj.calcTotal = calcTotal

        if obj.user == None and self.request.user.profile.isCreditRep == True:
            obj.user = self.request.user

        if chkOpp['status'] == "Error":
            obj.status = 0
            obj.errorText = chkOpp['responseText']
            obj.save()
        else:
            obj.status = 1
            obj.maxLoanAmount = chkOpp['data']['maxLoan']
            obj.maxLVR = chkOpp['data']['maxLVR']
            obj.save()

        messages.success(self.request, "Enquiry Saved")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))


# Enquiry Delete View (Delete View)
class EnquiryDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            Enquiry.objects.filter(enqUID=kwargs['uid']).delete()
            messages.success(self.request, "Enquiry deleted")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))


class SendEnquirySummary(LoginRequiredMixin, UpdateView):
    # This view does not render it creates and enquiry, sends an email, updates the calculator
    # and redirects to the Enquiry ListView
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'enquiry/email/email_cover_enquiry.html'

    def get(self, request, *args, **kwargs):
        enqUID = str(kwargs['uid'])
        queryset = Enquiry.objects.queryset_byUID(enqUID)
        enq_obj = queryset.get()

        if self.nullOrZero(enq_obj.calcTotal):
            messages.error(self.request, "No funding requirements - cannot send summary")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enq_obj.enqUID}))

        enqDict = Enquiry.objects.dictionary_byUID(enqUID)

        # PRODUCE PDF REPORT
        sourceUrl = 'https://householdcapital.app/enquiry/enquirySummaryPdf/' + enqUID
        targetFileName = settings.MEDIA_ROOT + "/enquiryReports/Enquiry-" + enqUID[
                                                                            -12:] + ".pdf"

        pdf = pdfGenerator(enqUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'CalculatorSummary.pdf', targetFileName)

        if not created:
            messages.error(self.request, "PDF not created - email could not be sent")
            write_applog("ERROR", 'SendEnquirySummary', 'get',
                         "PDF not created: " + str(enq_obj.enqUID))
            return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

        try:
            # SAVE TO DATABASE (Enquiry Model)
            localfile = open(targetFileName, 'rb')

            enq_obj.summaryDocument = File(localfile)
            enq_obj.save(update_fields=['summaryDocument'])

        except:
            write_applog("ERROR", 'SendEnquirySummary', 'get',
                         "Failed to save PDF in Database: " + str(enq_obj.enqUID))

        email_context = {}
        email_context['user'] = request.user
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

        subject, from_email, to, bcc = "Household Loan Enquiry", \
                                       self.request.user.email, \
                                       enq_obj.email, \
                                       self.request.user.email
        text_content = "Text Message"
        attachFilename = 'HHC-Summary'

        sent = pdf.emailPdf(self.template_name, email_context, subject, from_email, to, bcc, text_content,
                            attachFilename)
        if sent:
            messages.success(self.request, "Client has been emailed")
        else:
            messages.error(self.request, "Could not send email")
            write_applog("ERROR", 'SendEnquirySummary', 'get',
                         "Could not send email" + str(enq_obj.enqUID))

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enq_obj.enqUID}))

    def nullOrZero(self, arg):
        if arg:
            if arg != 0:
                return False
        return True


class EnqSummaryPdfView(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name = 'calculator/document/calculator_new_summary.html'

    def get_context_data(self, **kwargs):
        context = super(EnqSummaryPdfView, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])

        obj = Enquiry.objects.queryset_byUID(enqUID).get()

        loanObj = LoanValidator(obj.__dict__)
        loanStatus = loanObj.getStatus()['data']

        context["obj"] = obj
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
        result = loanProj.create(clientDict, frequency=12)

        print(obj.payIntAmount)

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


class EnquiryEmailEligibility(LoginRequiredMixin, TemplateView):
    template_name = 'enquiry/email/email_eligibility_summary.html'
    model = Enquiry

    def get(self, request, *args, **kwargs):
        email_context = {}
        enqUID = str(kwargs['uid'])

        queryset = Enquiry.objects.queryset_byUID(enqUID)
        obj = queryset.get()

        clientDict = queryset.values()[0]
        loanObj = LoanValidator(clientDict)
        email_context['eligibility'] = loanObj.validateLoan()
        email_context['obj'] = obj

        subject, from_email, to = "Eligibility Summary", settings.DEFAULT_FROM_EMAIL, self.request.user.email
        text_content = "Text Message"

        html = get_template(self.template_name)
        html_content = html.render(email_context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        messages.success(self.request, "A summary email has been sent to you")
        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': obj.enqUID}))


class EnquiryCloseFollowUp(LoginRequiredMixin, UpdateView):
    template_name = 'enquiry/enquiry.html'
    form_class = EnquiryCloseForm
    model = Enquiry

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            enqUID = str(self.kwargs['uid'])
            queryset = Enquiry.objects.queryset_byUID(str(enqUID))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryCloseFollowUp, self).get_context_data(**kwargs)
        context['title'] = 'Enquiry Close or Mark Follow-Up'

        if "uid" in self.kwargs:
            clientDict = Enquiry.objects.dictionary_byUID(str(self.kwargs['uid']))
            loanObj = LoanValidator(clientDict)
            chkOpp = loanObj.validateLoan()
            context['status'] = chkOpp
            obj = self.get_object()
            context['obj'] = obj
            context['isUpdate'] = False
        return context

    def form_valid(self, form):
        obj = form.save()
        obj.followUp = timezone.now()
        obj.status = 1
        obj.save(update_fields=['followUp', 'status'])

        messages.success(self.request, "Enquiry closed or marked as followed-up")
        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))


class EnquiryConvert(LoginRequiredMixin, View):
    # This view does not render it creates a case from an enquiry and marks it actioned
    context_object_name = 'object_list'
    model = WebCalculator

    def get(self, request, *args, **kwargs):

        enqUID = str(kwargs['uid'])

        # get Enquiry object and dictionary
        queryset = Enquiry.objects.queryset_byUID(enqUID)
        enq_obj = queryset.get()
        enqDict = Enquiry.objects.dictionary_byUID(enqUID)

        if enqDict['name'] == None:
            enqDict['name'] = "Unknown"

        # Create dictionary of Case fields from Enquiry fields
        if ' ' in enqDict['name']:
            firstname, surname = enqDict['name'].split(' ', 1)
        else:
            firstname = ""
            surname = enqDict['name']

        caseDict = {}
        caseDict['caseType'] = caseTypesEnum.LEAD.value
        caseDict['caseDescription'] = surname + " - " + str(enqDict['postcode'])
        caseDict['enquiryDocument'] = enqDict['summaryDocument']
        caseDict['caseNotes'] = enqDict['enquiryNotes']
        caseDict['firstname_1'] = firstname
        caseDict['surname_1'] = surname
        caseDict['adviser'] = enq_obj.enumReferrerType()
        user = self.request.user

        copyFields = ['loanType', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode', 'email', 'phoneNumber',
                      'sfLeadID']
        for field in copyFields:
            caseDict[field] = enqDict[field]

        # Create and save new Case
        case_obj = Case.objects.create(user=user, **caseDict)
        case_obj.save()

        # Set enquiry to actioned
        enq_obj.actioned = -1
        enq_obj.save()

        # Copy enquiryReport across to customerReport and add to the database
        try:
            if caseDict['enquiryDocument'] != None:
                old_file = enqDict["summaryDocument"]
                new_file = enqDict["summaryDocument"].replace('enquiryReports', 'customerReports')

                os.rename(old_file, new_file)
                case_obj.enquiryDocument.name = new_file
                case_obj.save()
        except:
            pass

        messages.success(self.request, "Enquiry converted to a new Case")

        return HttpResponseRedirect(reverse_lazy("case:caseList"))


class EnquiryOwnView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        enqUID = str(kwargs['uid'])
        enqObj = Enquiry.objects.queryset_byUID(enqUID).get()

        if self.request.user.profile.isCreditRep == True:
            enqObj.user = self.request.user
            enqObj.save(update_fields=['user'])
            messages.success(self.request, "Ownership Changed")

        else:
            messages.error(self.request, "You must be a Credit Representative to take ownership")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))


# Follow Up Email
class FollowUpEmail(LoginRequiredMixin, TemplateView):
    template_name = 'enquiry/email/email_followup.html'
    model = Enquiry

    def get(self, request, *args, **kwargs):
        email_context = {}
        enqID = str(kwargs['uid'])

        enqObj = Enquiry.objects.queryset_byUID(enqID).get()

        email_context['obj'] = enqObj
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

        if not enqObj.user:
            messages.error(self.request, "This enquiry is not assigned to a user. Please take ownership")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqObj.enqUID}))

        bcc = enqObj.user.email
        subject, from_email, to = "Household Capital: Follow-up", enqObj.user.email, enqObj.email
        text_content = "Text Message"

        enqObj.followUp = timezone.now()
        enqObj.save(update_fields=['followUp'])
        try:
            html = get_template(self.template_name)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            messages.success(self.request, "Follow-up emailed to client")

            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqObj.enqUID}))

        except:
            write_applog("ERROR", 'FollowUpEmail', 'get',
                         "Failed to email follow-up:" + enqID)
            messages.error(self.request, "Follow-up could not be emailed")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqObj.enqUID}))


# Referrer Views

# Referrer Detail View
class ReferrerView(ReferrerRequiredMixin, UpdateView):
    template_name = "enquiry/referrer.html"
    form_class = ReferrerForm
    model = Enquiry

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            enqUID = str(self.kwargs['uid'])
            queryset = Enquiry.objects.queryset_byUID(str(enqUID))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(ReferrerView, self).get_context_data(**kwargs)
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
        obj.referrer = directTypesEnum.REFERRAL.value
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

        messages.success(self.request, "Referral Captured or Updated")

        return HttpResponseRedirect(reverse_lazy('enquiry:enqReferrerUpdate', kwargs={'uid': str(obj.enqUID)}))


class ReferralEmail(LoginRequiredMixin, TemplateView):
    template_name = 'enquiry/email/email_referral.html'
    model = Enquiry

    def get(self, request, *args, **kwargs):
        email_context = {}
        enqID = str(kwargs['uid'])

        enqObj = Enquiry.objects.queryset_byUID(enqID).get()

        email_context['obj'] = enqObj
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

        if not enqObj.user:
            messages.error(self.request, "This enquiry is not assigned to a user. Please take ownership")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqObj.enqUID}))

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

            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqObj.enqUID}))

        except:
            write_applog("ERROR", 'FollowUpEmail', 'get',
                         "Failed to email introduction:" + enqID)
            messages.error(self.request, "Introduction could not be emailed")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqObj.enqUID}))


# Temporary Functionality
class DataLoad(LoginRequiredMixin, View):
    SF_LEAD_MAPPING = {'phoneNumber': 'Phone',
                       'email': 'Email',
                       'age_1': 'Age_of_1st_Applicant__c',
                       'age_2': 'Age_of_2nd_Applicant__c',
                       'dwellingType': 'Dwelling_Type__c',
                       'valuation': 'Estimated_Home_Value__c',
                       'postcode': 'PostalCode',
                       'isTopUp': 'IsTopUp__c',
                       'isRefi': 'IsRefi__c',
                       'isLive': 'IsLive__c',
                       'isGive': 'IsGive__c',
                       'isCare': 'IsCare__c',
                       'calcTopUp': 'CalcTopUp__c',
                       'calcRefi': 'CalcRefi__c',
                       'calcLive': 'CalcLive__c',
                       'calcGive': 'CalcGive__c',
                       'calcCare': 'CalcCare__c',
                       'calcTotal': 'CalcTotal__c',
                       'enquiryNotes': 'External_Notes__c',
                       'payIntAmount': 'payIntAmount__c',
                       'payIntPeriod': 'payIntPeriod__c',
                       'status': 'HCC_Loan_Eligible__c',
                       'maxLoanAmount': 'Maximum_Loan__c',
                       'maxLVR': 'Maximum_LVR__c',
                       'errorText': 'Ineligibility_Reason__c',
                       'referrerID': 'Referrer_ID__c'
                       }

    BooleanList = ['isTopUp', 'isRefi', 'isLive', 'isGive', 'isCare']

    def get(self, request, *args, **kwargs):

        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': "Could not connect to Salesforce"}

        qs = Enquiry.objects.filter(sfLeadID__isnull=True)
        for enquiry in qs:
            if (enquiry.email or enquiry.phoneNumber) and enquiry.user:
                enquiryDict = enquiry.__dict__

                payload = {}
                for app_field, sf_field in self.SF_LEAD_MAPPING.items():
                    payload[sf_field] = enquiryDict[app_field]
                    if app_field in self.BooleanList and not enquiryDict[app_field]:
                        payload[sf_field] = False

                if not enquiryDict['name']:
                    payload['Lastname'] = 'Unknown'
                elif " " in enquiryDict['name']:
                    payload['Firstname'], payload['Lastname'] = enquiryDict['name'].split(" ", 1)
                else:
                    payload['Lastname'] = enquiryDict['name']

                payload['External_ID__c'] = str(enquiryDict['enqUID'])
                payload['OwnerID'] = enquiry.user.profile.salesforceID
                payload['Loan_Type__c'] = enquiry.enumLoanType()
                payload['Dwelling_Type__c'] = enquiry.enumDwellingType()
                payload['LeadSource'] = enquiry.enumReferrerType()

                if enquiry.referralUser:
                    payload['Referral_UserID__c'] = enquiry.referralUser.last_name

                payload['CreatedDate'] = enquiry.timestamp.strftime("%Y-%m-%d")

                if enquiry.followUp:
                    payload['Last_External_Followup_Date__c'] = enquiry.followUp.strftime("%Y-%m-%d")

                if enquiry.followUpDate:
                    payload['Scheduled_Followup_Date_External__c'] = enquiry.followUpDate.strftime("%Y-%m-%d")

                if enquiry.name:
                    write_applog("INFO", 'Enquiry', 'dataLoad', enquiry.name)
                else:
                    write_applog("INFO", 'Enquiry', 'dataLoad', 'unknown')

                result = sfAPI.createLead(payload)

                write_applog("INFO", 'Enquiry', 'dataLoad', result['status'])

                if result['status'] == "Ok":
                    enquiry.sfLeadID = result['data']['id']
                    write_applog("INFO", 'Enquiry', 'dataLoad', enquiry.sfLeadID)
                    enquiry.save(update_fields=['sfLeadID'])
                else:
                    if isinstance(result['responseText'], dict):
                        write_applog("INFO", 'Enquiry', 'dataLoad', result['responseText']['message'])
                        if 'existing' in result['responseText']['message']:
                            if enquiry.email:
                                write_applog("INFO", 'Enquiry', 'SF!', enquiry.email)
                                result = sfAPI.qryToDict('LeadByEmail', enquiry.email, 'result')
                                if len(result['data']) == 0:
                                    write_applog("INFO", 'Enquiry', 'SF!', 'No id returned')
                                else:
                                    enquiry.sfLeadID = result['data']['result.Id']
                                    enquiry.save(update_fields=['sfLeadID'])
                            elif enquiry.phoneNumber:
                                write_applog("INFO", 'Enquiry', 'SF!', enquiry.phoneNumber)
                                result = sfAPI.qryToDict('LeadByPhone', enquiry.phoneNumber, 'result')
                                if len(result['data']) == 0:
                                    write_applog("INFO", 'Enquiry', 'SF!', 'No id returned')
                                else:
                                    enquiry.sfLeadID = result['data']['result.Id']
                                    enquiry.save(update_fields=['sfLeadID'])


class DataLoadCase(LoginRequiredMixin, View):
    SF_LEAD_MAPPING = {'phoneNumber': 'Phone',
                       'email': 'Email',
                       'age_1': 'Age_of_1st_Applicant__c',
                       'age_2': 'Age_of_2nd_Applicant__c',
                       'dwellingType': 'Dwelling_Type__c',
                       'valuation': 'Estimated_Home_Value__c',
                       'postcode': 'PostalCode',
                       'caseNotes': 'External_Notes__c',
                       }

    def get(self, request, *args, **kwargs):

        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            return {'status': "Error", 'responseText': "Could not connect to Salesforce"}

        qs = Case.objects.filter(sfLeadID__isnull=True)
        for case in qs:
            if (case.email or case.phoneNumber) and case.user:
                caseDict = case.__dict__

                payload = {}
                for app_field, sf_field in self.SF_LEAD_MAPPING.items():
                    payload[sf_field] = caseDict[app_field]

                if not caseDict['surname_1']:
                    payload['Lastname'] = 'Unknown'
                else:
                    payload['Firstname'] = caseDict['firstname_1']
                    payload['Lastname'] = caseDict['surname_1']

                payload['External_ID__c'] = str(caseDict['caseUID'])
                payload['OwnerID'] = case.user.profile.salesforceID
                payload['Loan_Type__c'] = case.enumLoanType()
                payload['Dwelling_Type__c'] = case.enumDwellingType()

                payload['CreatedDate'] = case.timestamp.strftime("%Y-%m-%d")

                if case.caseDescription:
                    write_applog("INFO", 'case', 'dataLoad', case.caseDescription)
                else:
                    write_applog("INFO", 'case', 'dataLoad', 'unknown')

                result = sfAPI.createLead(payload)

                write_applog("INFO", 'case', 'dataLoad', result['status'])

                if result['status'] == "Ok":
                    case.sfLeadID = result['data']['id']
                    write_applog("INFO", 'case', 'dataLoad', case.sfLeadID)
                    case.save(update_fields=['sfLeadID'])
                else:
                    if isinstance(result['responseText'], dict):
                        write_applog("INFO", 'case', 'dataLoad', result['responseText']['message'])
                        if 'existing' in result['responseText']['message']:
                            if case.email:
                                write_applog("INFO", 'Enquiry', 'SF!', case.email)
                                result = sfAPI.qryToDict('LeadByEmail', case.email, 'result')
                                if len(result['data']) == 0:
                                    write_applog("INFO", 'Enquiry', 'SF!', 'No id returned')
                                else:
                                    case.sfLeadID = result['data']['result.Id']
                                    case.save(update_fields=['sfLeadID'])
                            elif case.phoneNumber:
                                write_applog("INFO", 'Enquiry', 'SF!', case.phoneNumber)
                                result = sfAPI.qryToDict('LeadByPhone', case.phoneNumber, 'result')
                                if len(result['data']) == 0:
                                    write_applog("INFO", 'Enquiry', 'SF!', 'No id returned')
                                else:
                                    case.sfLeadID = result['data']['result.Id']
                                    case.save(update_fields=['sfLeadID'])
