# Python Imports
import os
import json
from datetime import timedelta

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

# Third-party Imports
from config.celery import app


# Local Application Imports
from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_Enums import caseStagesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.site_Logging import write_applog
from apps.lib.api_Pdf import pdfGenerator
from .forms import EnquiryForm, EnquiryDetailForm, EnquiryCloseForm, EnquiryAssignForm, EnquiryCallForm
from .models import Enquiry
from apps.lib.site_Utilities import HouseholdLoginRequiredMixin, getEnquiryProjections, updateNavQueue



# AUTHENTICATED VIEWS

# Enquiry List View
class EnquiryListView(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'enquiry/enquiryList.html'
    context_object_name = 'object_list'
    model = Enquiry

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search paramater

        delta = timedelta(weeks=4)
        windowDate = timezone.now() - delta

        queryset = super(EnquiryListView, self).get_queryset()
        queryset = queryset.filter(actioned=0, followUp__isnull=True, closeDate__isnull=True, updated__gte = windowDate)

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
            queryset = super(EnquiryListView, self).get_queryset().filter(user=self.request.user)\
                .exclude(actioned=-1).exclude(closeDate__isnull=False).exclude(followUp__isnull=False)

        if self.request.GET.get('action')=="True":
            queryset=super(EnquiryListView, self).get_queryset().filter(user__isnull=True)

        queryset = queryset.order_by('-updated')

        if self.request.GET.get('recent')=="True":
            queryset=super(EnquiryListView, self).get_queryset().order_by('-updated')[:100]

        return queryset

    def get_context_data(self, **kwargs):
        context = super(EnquiryListView, self).get_context_data(**kwargs)
        context['title'] = 'Enquiries'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        if self.bool_convert(self.request.GET.get('myEnquiries')):
            context['myEnquiries'] = self.request.GET.get('myEnquiries')
        else:
            context['myEnquiries'] = False

        if self.bool_convert(self.request.GET.get('action')):
            context['action']=True

        if self.bool_convert(self.request.GET.get('recent')):
            context['recent'] = True

        # Update Nav Queues
        updateNavQueue(self.request)

        return context

    def bool_convert(self, str):
        return str == "True"


# Enquiry Create View
class EnquiryCreateView(HouseholdLoginRequiredMixin, CreateView):
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
        context['newEnquiry'] = True
        return context

    def form_valid(self, form):
        clientDict = form.cleaned_data
        obj = form.save(commit=False)

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()

        if obj.user == None and self.request.user.profile.calendlyUrl:
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

        #Background task to update SF
        app.send_task('Create_SF_Lead', kwargs={'enqUID':str(obj.enqUID)})

        messages.success(self.request, "Enquiry Saved")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))


# Enquiry Detail View
class EnquiryUpdateView(HouseholdLoginRequiredMixin, UpdateView):
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

        paramStr = "?name="+(obj.name if obj.name else '') + "&email=" + \
                   (obj.email if obj.email else '')

        if obj.user:
            if obj.user.profile.calendlyUrl:
                context['calendlyUrl'] = obj.user.profile.calendlyUrl + paramStr
        else:
            context['calendlyUrl'] = ""

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

        if obj.user == None and self.request.user.profile.calendlyUrl:
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

        #Background task to update SF
        app.send_task('Update_SF_Lead', kwargs={'enqUID':str(obj.enqUID)})

        messages.success(self.request, "Enquiry Saved")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))


# Enquiry Detail View
class EnquiryCallView(HouseholdLoginRequiredMixin, CreateView):
    template_name = "enquiry/enquiry.html"
    form_class = EnquiryCallForm
    model = Enquiry

    def get_context_data(self, **kwargs):
        context = super(EnquiryCallView, self).get_context_data(**kwargs)
        context['title'] = 'New Call'
        context['isUpdate'] = False

        return context





# Enquiry Delete View (Delete View)
class EnquiryDeleteView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            Enquiry.objects.filter(enqUID=kwargs['uid']).delete()
            messages.success(self.request, "Enquiry deleted")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))


class SendEnquirySummary(HouseholdLoginRequiredMixin, UpdateView):
    # This view does not render it creates and enquiry, sends an email, updates the calculator
    # and redirects to the Enquiry ListView
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'enquiry/email/email_cover_enquiry.html'

    def get(self, request, *args, **kwargs):

        enqUID = str(kwargs['uid'])
        queryset = Enquiry.objects.queryset_byUID(enqUID)
        enq_obj = queryset.get()

        if not enq_obj.user:
            messages.error(self.request, "No Credit Representative assigned")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))

        if not enq_obj.email:
            messages.error(self.request, "No client email")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))

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
        email_context['user'] = enq_obj.user
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

        subject, from_email, to, bcc = "Household Loan Enquiry", \
                                       enq_obj.user.email, \
                                       enq_obj.email, \
                                       enq_obj.user.email

        text_content = "Text Message"
        attachFilename = 'HHC-Summary.pdf'

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

class CreateEnquirySummary(HouseholdLoginRequiredMixin, UpdateView):
    # This view does not render it creates an enquiry

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
            messages.error(self.request, "PDF not created")
            write_applog("ERROR", 'CreateEnquirySummary', 'get',
                         "PDF not created: " + str(enq_obj.enqUID))
            return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

        try:
            # SAVE TO DATABASE (Enquiry Model)
            localfile = open(targetFileName, 'rb')

            enq_obj.summaryDocument = File(localfile)
            enq_obj.save(update_fields=['summaryDocument'])
            messages.success(self.request, "Summary has been created")

        except:
            write_applog("ERROR", 'CreateEnquirySummary', 'get',
                         "Failed to save PDF in Database: " + str(enq_obj.enqUID))

            messages.error(self.request, "Could not create summary")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enq_obj.enqUID}))

    def nullOrZero(self, arg):
        if arg:
            if arg != 0:
                return False
        return True


class EnquiryEmailEligibility(HouseholdLoginRequiredMixin, TemplateView):
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


class EnquiryCloseFollowUp(HouseholdLoginRequiredMixin, UpdateView):
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

        if obj.user == None:
            obj.user = self.request.user

        if form.cleaned_data['closeReason']:
            obj.closeDate=timezone.now()
        obj.save(update_fields=['followUp','closeDate','user'])

        app.send_task('Update_SF_Lead', kwargs={'enqUID':str(obj.enqUID)})

        messages.success(self.request, "Enquiry closed or marked as followed-up")
        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))


class EnquiryConvert(HouseholdLoginRequiredMixin, View):
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
        caseDict['caseStage'] = caseStagesEnum.DISCOVERY.value
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
        case_obj = Case.objects.create(owner=user, **caseDict)
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


class EnquiryOwnView(HouseholdLoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        enqUID = str(kwargs['uid'])
        enqObj = Enquiry.objects.queryset_byUID(enqUID).get()

        if not self.request.user.profile.calendlyUrl:

            messages.error(self.request, "You are not set-up to action this type of enquiry")

        else:
            enqObj.user = self.request.user
            enqObj.save(update_fields=['user'])
            messages.success(self.request, "Ownership Changed")

            #Background task to update SF
            app.send_task('Update_SF_Lead', kwargs={'enqUID':enqUID})

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))


class EnquiryAssignView(HouseholdLoginRequiredMixin, UpdateView):
    template_name = 'enquiry/enquiry.html'
    email_template_name='enquiry/email/email_assign.html'
    form_class = EnquiryAssignForm
    model = Enquiry

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            enqUID = str(self.kwargs['uid'])
            queryset = Enquiry.objects.queryset_byUID(str(enqUID))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryAssignView, self).get_context_data(**kwargs)
        context['title'] = 'Assign Enquiry'

        return context

    def form_valid(self, form):
        preObj = queryset = Enquiry.objects.queryset_byUID(str(self.kwargs['uid'])).get()

        enq_obj = form.save(commit=False)
        if preObj.user:
            enq_obj.enquiryNotes += '\r\n[# Enquiry assigned from ' + preObj.user.username + ' #]'
        elif preObj.referrer == directTypesEnum.REFERRAL.value:
            enq_obj.enquiryNotes += '\r\n[# Enquiry assigned from ' + preObj.referralUser.profile.referrer.companyName + ' #]'

        enq_obj.save()

        # Email recipient
        subject, from_email, to = "Enquiry Assigned to You", "noreply@householdcapital.app", enq_obj.user.email
        text_content = "Text Message"
        email_context={}
        email_context['obj'] = enq_obj

        try:
            html = get_template(self.email_template_name)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            pass

        messages.success(self.request, "Enquiry assigned to " + enq_obj.user.username )
        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enq_obj.enqUID}))


# UNAUTHENTICATED VIEWS
class EnqSummaryPdfView(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name = 'enquiry/document/calculator_summary.html'

    def get_context_data(self, **kwargs):
        context = super(EnqSummaryPdfView, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])

        # Projection Results (site.utilities)
        projectionContext = getEnquiryProjections(enqUID)
        context.update(projectionContext)

        return context

class EnqIncomeSummaryPdfView(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name =  'enquiry/document/calculator_income_summary.html'

    def get_context_data(self, **kwargs):
        context = super(EnqIncomeSummaryPdfView, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])

        # Projection Results (site.utilities)
        projectionContext = getEnquiryProjections(enqUID)
        context.update(projectionContext)

        return context
