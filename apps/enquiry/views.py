# Python Imports
import datetime
from datetime import timedelta
import io
import csv
import os
import json
import pathlib

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.template.loader import get_template
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, TemplateView, View, FormView

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case
from apps.lib.api_Mappify import apiMappify
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.site_Enums import *
from apps.lib.site_Logging import write_applog
from apps.lib.api_Pdf import pdfGenerator
from .forms import EnquiryForm, EnquiryDetailForm, EnquiryCloseForm, EnquiryAssignForm, EnquiryCallForm, \
    AddressForm, PartnerForm
from .models import Enquiry
from apps.lib.site_Utilities import HouseholdLoginRequiredMixin, getEnquiryProjections, updateNavQueue, \
    cleanPhoneNumber, validateEnquiry


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
        queryset = queryset.filter(actioned=0, closeDate__isnull=True, updated__gte=windowDate)

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
            queryset = super(EnquiryListView, self).get_queryset().filter(user=self.request.user)

        if self.request.GET.get('action') == "True":
            queryset = super(EnquiryListView, self).get_queryset().filter(user__isnull=True)

        queryset = queryset.order_by('-updated')[:160]

        if self.request.GET.get('recent') == "True":
            queryset = super(EnquiryListView, self).get_queryset().order_by('-updated')[:100]

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
            context['action'] = True

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

        # Pass address form
        context['address_form'] = AddressForm()
        # Ajax URl
        context['ajaxURL'] = reverse_lazy("enquiry:addressComplete")

        return context

    def form_valid(self, form):
        clientDict = form.cleaned_data
        obj = form.save()

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

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
            obj.maxDrawdownAmount = chkOpp['data']['maxDrawdown']
            obj.maxDrawdownMonthly = chkOpp['data']['maxDrawdownMonthly']
            obj.save()

        # Background task to update SF
        app.send_task('Create_SF_Lead', kwargs={'enqUID': str(obj.enqUID)})

        messages.success(self.request, "Enquiry Saved")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))


# Partner List View
class EnquiryPartnerList(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'enquiry/enquiryPartnerList.html'
    context_object_name = 'object_list'
    model = Enquiry

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search paramater

        queryset = super(EnquiryPartnerList, self).get_queryset()
        queryset = queryset.filter(actioned=0, closeDate__isnull=True,
                                   referrer=directTypesEnum.PARTNER.value)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = super(EnquiryPartnerList, self).get_queryset()
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phoneNumber__icontains=search) |
                Q(postcode__icontains=search) |
                Q(enquiryNotes__icontains=search)
            ).filter(referrer=directTypesEnum.PARTNER.value).exclude(actioned=-1)

        queryset = queryset.order_by('-updated')[:160]

        return queryset

    def get_context_data(self, **kwargs):
        context = super(EnquiryPartnerList, self).get_context_data(**kwargs)
        context['title'] = 'Partner leads'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        # Update Nav Queues
        updateNavQueue(self.request)

        return context


# Enquiry Detail View
class EnquiryUpdateView(HouseholdLoginRequiredMixin, UpdateView):
    template_name = "enquiry/enquiry.html"
    form_class = EnquiryDetailForm
    model = Enquiry

    def get(self, request, *args, **kwargs):

        # Check for closed object and redirect
        obj = self.get_object()
        if obj.actioned != 0:
            if obj.sfLeadID:
                try:
                    caseObj = Case.objects.filter(sfLeadID=obj.sfLeadID).get()
                    messages.warning(self.request, "Enquiry previously converted to case")
                    return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': str(caseObj.caseUID)}))
                except Case.DoesNotExist:
                    messages.warning(self.request, "Enquiry no longer exists or has been converted to a case")
                    return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))
                except Case.MultipleObjectsReturned:
                    messages.warning(self.request, "Enquiry no longer exists or has been converted to a case")
                    return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))
            else:
                messages.warning(self.request, "Enquiry no longer exists or has been converted to a case")
                return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))
        return super(EnquiryUpdateView, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        enqUID = str(self.kwargs['uid'])
        queryset = Enquiry.objects.queryset_byUID(str(enqUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryUpdateView, self).get_context_data(**kwargs)
        context['title'] = 'Enquiry'

        obj = self.get_object()
        clientDict = Enquiry.objects.dictionary_byUID(str(self.kwargs['uid']))

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()
        context['status'] = chkOpp

        # Check for duplicates
        if obj.email:
            if Enquiry.objects.filter(email=obj.email).count() > 1:
                messages.error(self.request, "Email exists - avoid duplicates")

        if obj.phoneNumber:
            if Enquiry.objects.filter(phoneNumber=obj.phoneNumber).count() > 1:
                messages.error(self.request, "Phone number exists - avoid duplicates")

        # Validate requirement amounts (if present)
        if obj.calcLumpSum or obj.calcIncome:
            loanStatus = validateEnquiry(str(self.kwargs['uid']))
            if loanStatus['status'] == "Ok":
                if loanStatus['data']['errors']:
                    context['requirementError'] = 'Invalid requirement amounts'

        context['obj'] = obj
        context['isUpdate'] = True
        context['productTypesEnum'] = productTypesEnum

        # Pass Calendly information
        paramStr = "?name=" + (obj.name if obj.name else '') + "&email=" + \
                   (obj.email if obj.email else '')
        if obj.user:

            if obj.user.profile.calendlyUrl:
                context['calendlyUrl'] = obj.user.profile.calendlyUrl + paramStr
        else:
            context['calendlyUrl'] = ""

        # Pass address form
        context['address_form'] = AddressForm()
        # Ajax URl
        context['ajaxURL'] = reverse_lazy("enquiry:addressComplete")

        return context

    def form_valid(self, form):
        clientDict = form.cleaned_data
        obj = form.save(commit=False)

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()

        if obj.user == None and self.request.user.profile.calendlyUrl:
            obj.user = self.request.user

        # Simple validation
        if chkOpp['status'] == "Error":
            obj.status = 0
            obj.errorText = chkOpp['responseText']
            obj.save()
        else:
            obj.status = 1
            obj.maxLoanAmount = chkOpp['data']['maxLoan']
            obj.maxLVR = chkOpp['data']['maxLVR']
            obj.maxDrawdownAmount = chkOpp['data']['maxDrawdown']
            obj.maxDrawdownMonthly = chkOpp['data']['maxDrawdownMonthly']
            obj.save()

        # Renames and moves the autoVal file if present
        if 'valuationDocument' in self.request.FILES:
            path, filename = obj.valuationDocument.name.split("/")
            ext = pathlib.Path(obj.valuationDocument.name).suffix
            newFilename = path + "/autoVal-" + str(obj.enqUID)[-12:] + ext

            try:
                originalFilename = obj.valuationDocument.name
                movable_file = default_storage.open(originalFilename)
                actualFilename = default_storage.save(newFilename, movable_file)
                obj.valuationDocument = actualFilename
                obj.save(update_fields=['valuationDocument'])
                movable_file.close()
                default_storage.delete(originalFilename)
            except:
                pass

        # Check Close Case
        if obj.enquiryStage in [enquiryStagesEnum.DID_NOT_QUALIFY.value,
                                enquiryStagesEnum.NOT_PROCEEDING.value,
                                enquiryStagesEnum.FUTURE_CALL.value,
                                enquiryStagesEnum.DUPLICATE.value]:
            return HttpResponseRedirect(reverse_lazy('enquiry:enqMarkFollowUp', kwargs={'uid': str(obj.enqUID)}))
        else:
            obj.closeDate = None
            obj.closeReason = None
            obj.save()

        # Background task to update SF
        if obj.sfLeadID:
            app.send_task('Update_SF_Lead', kwargs={'enqUID': str(obj.enqUID)})
        else:
            app.send_task('Create_SF_Lead', kwargs={'enqUID': str(obj.enqUID)})

        messages.success(self.request, "Enquiry Saved")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))

# Refer Postcode Request
class EnquiryReferView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        enqUID = str(self.kwargs['uid'])
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Enquiry', 'EnquiryReferView', result['responseText'])
            messages.error(request, "Could not update Salesforce")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))

        # Get object
        qs = Enquiry.objects.queryset_byUID(enqUID)
        enquiry = qs.get()

        if not enquiry.sfLeadID:
            messages.error(request, "There is no Salesforce Lead for this enquiry")
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))

        payload = {"IsReferPostCode__c": True}
        result = sfAPI.updateLead(enquiry.sfLeadID, payload)

        if result['status'] != 'Ok':
            messages.error(request, "Could not set status in Salesforce")
            write_applog("ERROR", 'Enquiry', 'EnquiryReferView', result['responseText'])
        else:
            messages.success(request, "Refer postcode review requested")
            # save Enquiry Field
            enquiry.isReferPostcode = True
            enquiry.save()

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))


# Enquiry Call View
class EnquiryCallView(HouseholdLoginRequiredMixin, CreateView):
    template_name = "enquiry/enquiryCall.html"
    form_class = EnquiryCallForm
    model = Enquiry

    def get_context_data(self, **kwargs):
        context = super(EnquiryCallView, self).get_context_data(**kwargs)
        context['title'] = 'New Call'
        context['isUpdate'] = False

        return context

    def form_valid(self, form):

        if self.request.is_ajax():
            phoneNumberExists = None
            postcodeStatus = None
            existingUrl = None

            if form.cleaned_data['phoneNumber']:
                qs = Enquiry.objects.filter(phoneNumber=form.cleaned_data['phoneNumber']).exclude(actioned=-1).order_by(
                    "-updated")
                if qs.count() == 1:
                    # url to single enquiry detail page
                    phoneNumberExists = True
                    obj = qs.get()
                    existingUrl = str(obj.get_absolute_url)
                elif qs.count() > 1:
                    # url to enquiry list page with search on number
                    phoneNumberExists = True
                    existingUrl = str(reverse_lazy("enquiry:enquiryList")) + '?search=' + str(
                        form.cleaned_data['phoneNumber'])

            if form.cleaned_data['postcode']:
                obj = LoanValidator({})
                postcodeStatus = obj.checkPostcode(form.cleaned_data['postcode'])

            payload = {"success": {'phoneNumberExists': phoneNumberExists,
                                   'postcodeStatus': postcodeStatus,
                                   'existingUrl': existingUrl}}

            return HttpResponse(json.dumps(payload), content_type='application/json', status=200)

        obj = form.save(commit=False)
        obj.status = 0
        obj.referrer = directTypesEnum.PHONE.value

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

        if self.request.user.profile.calendlyUrl:
            obj.user = self.request.user

        obj.save()

        # Background task to update SF
        app.send_task('Create_SF_Lead', kwargs={'enqUID': str(obj.enqUID)})

        if 'submit' in form.data:
            # Continue to enquiry
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))
        else:
            # Mark enquiry closed
            obj.closeReason = closeReasonEnum.CALL_ONLY.value
            obj.closeDate = timezone.now()
            obj.save()
            return HttpResponseRedirect(reverse_lazy('enquiry:enquiryCall'))


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
        sourceUrl = settings.SITE_URL + reverse('enquiry:enqSummaryPdf',
                                                kwargs={'uid': enqUID})

        targetFileName = "enquiryReports/Enquiry-" + enqUID[-12:] + ".pdf"

        pdf = pdfGenerator(enqUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'CalculatorSummary.pdf', targetFileName)

        if not created:
            messages.error(self.request, "PDF not created - email could not be sent")
            write_applog("ERROR", 'SendEnquirySummary', 'get',
                         "PDF not created: " + str(enq_obj.enqUID))
            return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

        try:
            # SAVE TO DATABASE (Enquiry Model)

            enq_obj.summaryDocument = targetFileName
            enq_obj.enquiryStage = enquiryStagesEnum.SUMMARY_SENT.value
            enq_obj.save(update_fields=['summaryDocument', 'enquiryStage'])

        except:
            write_applog("ERROR", 'SendEnquirySummary', 'get',
                         "Failed to save PDF in Database: " + str(enq_obj.enqUID))

        email_context = {}
        email_context['user'] = enq_obj.user
        subject, from_email, to, bcc = "Household Loan Enquiry", \
                                       enq_obj.user.email, \
                                       enq_obj.email, \
                                       enq_obj.user.email

        text_content = "Text Message"
        attachFilename = 'HHC-Summary.pdf'

        sent = pdf.emailPdf(self.template_name, email_context, subject, from_email, to, bcc,
                            text_content, attachFilename)
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
        sourceUrl = settings.SITE_URL + reverse('enquiry:enqSummaryPdf',
                                                kwargs={'uid': enqUID})

        targetFileName = "enquiryReports/Enquiry-" + enqUID[-12:] + ".pdf"

        pdf = pdfGenerator(enqUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'CalculatorSummary.pdf', targetFileName)

        if not created:
            messages.error(self.request, "PDF not created")
            write_applog("ERROR", 'CreateEnquirySummary', 'get',
                         "PDF not created: " + str(enq_obj.enqUID))
            return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

        try:
            # SAVE TO DATABASE (Enquiry Model)

            enq_obj.summaryDocument = targetFileName
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
    template_name = 'enquiry/enquiryOther.html'
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
        context['title'] = 'Enquiry Close or Follow-Up'

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
            obj.closeDate = timezone.now()
        obj.save(update_fields=['followUp', 'closeDate', 'user'])

        app.send_task('Update_SF_Lead', kwargs={'enqUID': str(obj.enqUID)})

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
        caseDict['enqUID'] = enq_obj.enqUID
        caseDict['enquiryCreateDate'] = enq_obj.timestamp
        caseDict['street'] = enq_obj.streetAddress
        caseDict['channelDetail'] = enq_obj.marketingSource

        salesChannelMap = {
            directTypesEnum.PARTNER.value: channelTypesEnum.PARTNER.value,
            directTypesEnum.ADVISER.value: channelTypesEnum.ADVISER.value,
            directTypesEnum.BROKER.value: channelTypesEnum.BROKER.value
        }

        if enq_obj.referrer in salesChannelMap:
            caseDict['salesChannel'] = salesChannelMap[enq_obj.referrer]
        else:
            caseDict['salesChannel'] = channelTypesEnum.DIRECT_ACQUISITION.value

        user = self.request.user

        copyFields = ['loanType', 'age_1', 'age_2', 'dwellingType', 'valuation', 'postcode', 'suburb', 'state', 'email',
                      'phoneNumber', 'mortgageDebt',
                      'sfLeadID', 'productType', 'isReferPostcode', 'referPostcodeStatus', 'valuationDocument']

        for field in copyFields:
            caseDict[field] = enqDict[field]

        # Create and save new Case
        case_obj = Case.objects.create(owner=enq_obj.user, **caseDict)
        case_obj.save()

        # Set enquiry to actioned
        enq_obj.actioned = -1
        enq_obj.enquiryStage = enquiryStagesEnum.LOAN_INTERVIEW.value
        enq_obj.save()
        app.send_task('Update_SF_Lead', kwargs={'enqUID': enqUID})

        # Copy enquiryReport across to customerReport and add to the database
        self.moveDocument("enquiryDocument", "summaryDocument", 'customerReports', caseDict, enqDict, case_obj)

        # Copy valuationReport across to customerReport and add to the database
        self.moveDocument("valuationDocument", "valuationDocument", 'customerDocuments', caseDict, enqDict, case_obj)

        messages.success(self.request, "Enquiry converted to a new Case")

        return HttpResponseRedirect(reverse_lazy("case:caseList"))

    def moveDocument(self, caseField, enqField, caseFolder, caseDict, enqDict, case_obj):

        if caseDict[caseField] != None and caseDict[caseField] != "":

            try:
                old_file = enqDict[enqField]
                new_file = old_file.replace('enquiryReports', caseFolder)

                movable_file = default_storage.open(old_file)
                default_storage.save(new_file, movable_file)
                getattr(case_obj, caseField).name = new_file
                case_obj.save()
                movable_file.close()
                default_storage.delete(old_file)

            except:
                messages.error(self.request, "Not all documents moved from Enquiry")

        return


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

            # Background task to update SF
            app.send_task('Update_SF_Lead', kwargs={'enqUID': enqUID})

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))


class EnquiryAssignView(HouseholdLoginRequiredMixin, UpdateView):
    template_name = 'enquiry/enquiryOther.html'
    email_template_name = 'enquiry/email/email_assign.html'
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
        email_context = {}
        email_context['obj'] = enq_obj
        email_context['base_url'] = settings.SITE_URL

        try:
            html = get_template(self.email_template_name)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            pass

        messages.success(self.request, "Enquiry assigned to " + enq_obj.user.username)
        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enq_obj.enqUID}))


# UNAUTHENTICATED VIEWS
class EnqSummaryPdfView(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name = None

    def get(self, request, *args, **kwargs):
        enqUID = str(kwargs['uid'])
        obj = Enquiry.objects.queryset_byUID(enqUID).get()

        if obj.productType == productTypesEnum.INCOME.value:
            self.template_name = 'enquiry/document/calculator_income_summary.html'

        elif obj.productType == productTypesEnum.CONTINGENCY_20K.value:
            self.template_name = 'enquiry/document/calculator_summary_single_20k.html'

        elif obj.productType == productTypesEnum.COMBINATION.value:
            self.template_name = 'enquiry/document/calculator_combination_summary.html'

        else:
            self.template_name = 'enquiry/document/calculator_summary.html'

        return super(EnqSummaryPdfView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EnqSummaryPdfView, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])

        # Projection Results (site.utilities)
        projectionContext = getEnquiryProjections(enqUID)
        context.update(projectionContext)
        return context


# AJAX Views

class AddressComplete(HouseholdLoginRequiredMixin, View):
    form_class = AddressForm

    def post(self, request, *args, **kwargs):
        # Ajax View - provides auto address complete list using Mappify

        form = self.form_class(request.POST)

        if form.is_valid():
            address = form.cleaned_data['lookup_address']

            api = apiMappify()
            result = api.autoComplete(address)
            # Split street address component
            for item in result:
                item['streetComponent'], remainder = item['streetAddress'].rsplit(",", 1)
                item['stateCode'] = stateTypesEnum[item['state']].value

            return HttpResponse(json.dumps(result), content_type='application/json')
        else:
            return HttpResponse(json.dumps({"error": "Form Invalid"}), content_type='application/json', status=400)


class EnquiryPartnerUpload(HouseholdLoginRequiredMixin, FormView):
    """Load bulk enquiries from Partners"""
    form_class = PartnerForm
    template_name = 'enquiry/enquiryPartner.html'

    def get_context_data(self, **kwargs):
        context = super(EnquiryPartnerUpload, self).get_context_data(**kwargs)
        context['title'] = 'Upload partner file'

        return context

    def form_valid(self, form):

        fileWrapper = io.TextIOWrapper(form.cleaned_data['uploadFile'], encoding='utf-8')
        reader = csv.reader(fileWrapper)
        header = next(reader)

        if int(form.cleaned_data['partner']) == marketingTypesEnum.STARTS_AT_60.value:

            # Check file format - starts at 60
            if header[11] != 'Token':
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            for row in reader:

                email = row[1]
                phoneNumber = cleanPhoneNumber(row[8])

                if email:
                    enquiryString = "[# Updated from Partner Upload #]"
                    enquiryString += "\r\nPartner: Starts at 60"
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nCustomer Date of birth: " + datetime.datetime.strptime(row[9],
                                                                                                 '%m/%d/%Y').strftime(
                        '%d/%m/%Y')

                    payload = {
                        "name": (row[0] + " " + row[5]).title(),
                        "postcode": row[2],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": self.cleanValuation(row[6]),
                        "age_1": self.calcAge(row[9]),
                        "marketingSource": marketingTypesEnum.STARTS_AT_60.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "user": None
                    }

                    self.updateCreateEnquiry(email, phoneNumber, payload,
                                             enquiryString, marketingTypesEnum.STARTS_AT_60.value, False)

            messages.success(self.request, "Success - enquiries imported")


        elif int(form.cleaned_data['partner']) == marketingTypesEnum.CARE_ABOUT.value:

            # Check file format - Care About

            if header[15] != 'Customer Postal Code':
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            for row in reader:
                email = row[6]
                phoneNumber = cleanPhoneNumber(row[7])

                if email:
                    enquiryString = "[# Updated from Partner Upload #]"
                    enquiryString += "\r\nPartner: Care About"
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nWho needs help: " + row[16]

                    payload = {
                        "name": (row[3] + " " + row[2]).title(),
                        "postcode": self.cleanValuation(row[15]),
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.CARE_ABOUT.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "user": None
                    }

                    self.updateCreateEnquiry(email, phoneNumber, payload,
                                             enquiryString, marketingTypesEnum.CARE_ABOUT.value, False)

            messages.success(self.request, "Success - enquiries imported")

        elif int(form.cleaned_data['partner']) == marketingTypesEnum.YOUR_LIFE_CHOICES.value:

            # Check file format - Your Life Choices

            if header[11] != 'Create Date':
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            for row in reader:
                email = row[2]
                phoneNumber = cleanPhoneNumber(row[5])

                if (email != "") and (email != "Email"):
                    enquiryString = "[# Updated from Partner Upload #]"
                    enquiryString += "\r\nPartner: Your Life Choices"
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nOwnership: " + row[7]
                    enquiryString += "\r\nCreate Date: " + row[11]


                    name = row[0].title()
                    if row[1]:
                        name += " " + row[1].title()

                    payload = {
                        "name": name,
                        "postcode": row[6],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": self.cleanValuation(row[9]),
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.YOUR_LIFE_CHOICES.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "user": self.request.user,
                        "state": stateTypesEnum[row[10]].value,
                        'dwellingType': dwellingTypesEnum.APARTMENT.value if row[8] == "Strata Property" else dwellingTypesEnum.HOUSE.value,
                        "enquiryStage": enquiryStagesEnum.GENERAL_INFORMATION.value if row[4] == "Closed Lost" else enquiryStagesEnum.FOLLOW_UP_NO_ANSWER.value
                    }

                    self.updateCreateEnquiry(email, phoneNumber, payload,
                                             enquiryString, marketingTypesEnum.YOUR_LIFE_CHOICES.value, False)

            messages.success(self.request, "Success - enquiries imported")

        elif int(form.cleaned_data['partner']) == marketingTypesEnum.FACEBOOK.value:

            # Check file format - Your Life Choices

            if header[10] != 'Year of birth':
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            for row in reader:
                email = row[3]
                phoneNumber = cleanPhoneNumber(row[5])
                
                if email:
                    enquiryString = "[# Updated from Social Upload #]"
                    enquiryString += "\r\nSocial: Facebook"
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nMonth of Birth: " + row[9]
                    enquiryString += "\r\nYear of Birth: " + row[10]

                    payload = {
                        "name": row[2].title(),
                        "postcode": row[4],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.FACEBOOK.value,
                        "referrer": directTypesEnum.SOCIAL.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "user": None
                    }

                    self.updateCreateEnquiry(email, phoneNumber, payload,
                                             enquiryString, marketingTypesEnum.FACEBOOK.value, False)

            messages.success(self.request, "Success - enquiries imported")

        return HttpResponseRedirect(self.request.path_info)

    def updateCreateEnquiry(self, email, phoneNumber, payload, enquiryString, marketingSource, updateNonDirect=True):

        nonDirectTypes = [directTypesEnum.PARTNER.value, directTypesEnum.BROKER.value,
                          directTypesEnum.ADVISER.value]

        # Try find existing enquiry
        existingUID = self.findEnquiry(email, phoneNumber)

        if existingUID:
            qs = Enquiry.objects.queryset_byUID(existingUID)
            obj = qs.get()

            if (obj.marketingSource != marketingSource) and (obj.actioned == 0):
                # Only update if a new marketing source and not converted

                if (updateNonDirect == False) and (obj.referrer in nonDirectTypes):
                    # Don't update non-direct items (if specified)
                    pass
                else:
                    qs.update(**payload)
                    obj = qs.get()
                    updateNotes = "".join(filter(None, (obj.enquiryNotes, "\r\n\r\n" + enquiryString)))
                    obj.enquiryNotes = updateNotes
                    obj.save()
        else:
            payload["enquiryNotes"] = enquiryString
            Enquiry.objects.create(**payload)

    def findEnquiry(self, email, phoneNumber):

        obj = Enquiry.objects.filter((Q(email__iexact=email) | Q(phoneNumber=phoneNumber))).order_by("-updated").first()
        if obj:
            return str(obj.enqUID)

    def cleanValuation(self, valString):

        val = valString.replace("$", "").replace(",", "").replace("Million", "M"). \
            replace("m", "M").replace("k", "K").replace("M", "000000").replace("K", "000")
        try:
            val = int(val)
            if val > 5000000:
                return None
            elif val < 1000:
                return val * 1000
            else:
                return val
        except:
            return None

    def calcAge(self, DOBString):

        age = int((datetime.date.today() - datetime.datetime.strptime(DOBString, '%m/%d/%Y').date()).days / 365.25)
        if age > 50 and age < 100:
            return age
