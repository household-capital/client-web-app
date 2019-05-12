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
from django.views.generic import UpdateView, ListView, TemplateView, View

# Local Application Imports
from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case
from apps.lib.loanValidator import LoanValidator
from apps.lib.enums import caseTypesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum
from apps.lib.utilities import pdfGenerator
from apps.logging import write_applog
from .forms import EnquiryForm, ReferrerForm, EnquiryFollowupForm
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
        queryset = queryset.filter(actioned=0, followUp__isnull=True).exclude(status=False, user__isnull=False)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = super(EnquiryListView, self).get_queryset().filter(actioned=0)
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phoneNumber__icontains=search) |
                Q(postcode__icontains=search) |
                Q(enquiryNotes__icontains=search)

            )

        # ...and for open my items
        if self.request.GET.get('myEnquiries') == "True":
            queryset = super(EnquiryListView, self).get_queryset().filter(user=self.request.user, actioned=0)

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


# Enquiry Detail View
class EnquiryView(LoginRequiredMixin, UpdateView):
    template_name = "enquiry/enquiry.html"
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
        context['title'] = 'Enquiry'

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

        loanObj = LoanValidator( clientDict)
        chkOpp = loanObj.validateLoan()

        if obj.user == None and self.request.user.profile.isCreditRep == True:
            obj.user = self.request.user

        if chkOpp['status'] == "Error":
            obj.status = 0
            obj.errorText = chkOpp['details']
            obj.save()
        else:
            obj.status = 1
            obj.maxLoanAmount = chkOpp['restrictions']['maxLoan']
            obj.maxLVR = chkOpp['restrictions']['maxLVR']
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

        enqDict = Enquiry.objects.dictionary_byUID(enqUID)

        # PRODUCE PDF REPORT
        sourceUrl = 'https://householdcapital.app/enquiry/enquirySummaryPdf/' + enqUID
        targetFileName = settings.MEDIA_ROOT + "/enquiryReports/Enquiry-" + enqUID[
                                                                            -12:] + ".pdf"

        pdf = pdfGenerator(enqUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'CalculatorSummary.pdf', targetFileName)

        if not created:
            messages.error(self.request, "Email could not be sent")
            return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

        try:
            # SAVE TO DATABASE (Enquiry Model)
            localfile = open(targetFileName, 'rb')

            enq_obj.summaryDocument = File(localfile)
            enq_obj.save(update_fields=['summaryDocument'])

        except:
            write_applog("ERROR", 'SendEnquirySummary', 'get',
                         "Failed to save Enquiry Summary  in Database: " + str(enq_obj.enqUID))

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

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enq_obj.enqUID}))


class EnqSummaryPdfView(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name = 'enquiry/document/enquiry_summary.html'

    def get_context_data(self, **kwargs):
        context = super(EnqSummaryPdfView, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])

        obj = Enquiry.objects.dictionary_byUID(enqUID)

        context["obj"] = obj
        if obj["maxLVR"] < 18:
            img = 'transfer_15.png'
        elif obj["maxLVR"] < 22:
            img = 'transfer_20.png'
        elif obj["maxLVR"] < 27:
            img = 'transfer_25.png'
        elif obj["maxLVR"] < 32:
            img = 'transfer_30.png'
        else:
            img = 'transfer_35.png'
        context["transfer_img"] = img

        context['caseTypesEnum'] = caseTypesEnum
        context['loanTypesEnum'] = loanTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum
        context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
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
        loanObj = LoanValidator( clientDict)
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


class EnquiryMarkFollowUp(LoginRequiredMixin, UpdateView):
    template_name = 'enquiry/enquiry.html'
    form_class = EnquiryFollowupForm
    model = Enquiry

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            enqUID = str(self.kwargs['uid'])
            queryset = Enquiry.objects.queryset_byUID(str(enqUID))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryMarkFollowUp, self).get_context_data(**kwargs)
        context['title'] = 'Enquiry Mark Follow-Up'

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
        obj.save(update_fields=['followUp'])

        messages.success(self.request, "Enquiry marked as followed-up")
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

        copyFields = ['loanType', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode', 'email', 'phoneNumber']
        for field in copyFields:
            caseDict[field] = enqDict[field]

        # Create and save new Case
        case_obj = Case.objects.create(user=user, **caseDict)
        case_obj.save()

        # Set enquiry to actioned
        enq_obj.actioned = 1
        enq_obj.save()

        # Copy enquiryReport across to customerReport and add to the database
        try:
            if caseDict['enquiryDocument'] != None:
                old_file = enqDict["summaryDocument"]
                new_file = enqDict["summaryDocument"].replace('enquiryReports', 'customerReports')

                os.rename(old_file, new_file)
                print(new_file)
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
            obj.errorText = chkOpp['details']
            obj.save()
        else:
            obj.status = 1
            obj.maxLoanAmount = chkOpp['restrictions']['maxLoan']
            obj.maxLVR = chkOpp['restrictions']['maxLVR']
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


