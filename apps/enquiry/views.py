# Python Imports
import datetime
from datetime import timedelta
import io
import csv
import os
import json
import pathlib
from urllib.parse import urljoin

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.template.loader import get_template
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, TemplateView, View, FormView
from django.utils.dateparse import parse_date

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
from apps.lib.site_Utilities import parse_api_name, parse_api_names
from .forms import EnquiryForm, EnquiryDetailForm, EnquiryCallForm, \
    AddressForm, PartnerForm, EnquiryAssignForm
from .models import Enquiry
from apps.lib.site_Utilities import cleanPhoneNumber, cleanValuation, calcAge, validate_loan
from apps.lib.site_ViewUtils import updateNavQueue
from apps.lib.site_LoanUtils import validateEnquiry, getEnquiryProjections
from apps.lib.mixins import HouseholdLoginRequiredMixin, AddressLookUpFormMixin
from .util import assign_enquiry_leads, updateCreatePartnerEnquiry


from urllib.parse import urljoin
from apps.base.model_utils import address_model_fields

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
        queryset = queryset.filter(actioned=0, deleted_on__isnull=True, closeDate__isnull=True, updated__gte=windowDate)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = super(EnquiryListView, self).get_queryset()
            queryset = queryset.annotate(
                fullname=Concat(
                    F('firstname'),
                    Value(' '),
                    F('lastname'),
                    output_field=CharField()
                )
            ).filter(
                Q(fullname__icontains=search) | 
                Q(email__icontains=search) |
                Q(phoneNumber__icontains=search) |
                Q(postcode__icontains=search) #|
                #Q(enquiryNotes__icontains=search) # FIX ME - how to search in django comments?
            ).exclude(actioned=-1)

        # ...and for open my items
        if self.request.GET.get('myEnquiries') == "True":
            queryset = super(EnquiryListView, self).get_queryset().filter(user=self.request.user)

        if self.request.GET.get('action') == "True":
            queryset = super(EnquiryListView, self).get_queryset().filter(user__isnull=True)

        queryset = queryset.filter(deleted_on__isnull=True).order_by('-updated')[:160]

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
        obj.submissionOrigin = 'Client App'
        obj.origin_timestamp = timezone.now()
        obj.origin_id = obj.enqUID

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

        if obj.user == None and self.request.user.profile.calendlyUrl:
            obj.user = self.request.user

        obj.save()

        # Background task to update SF

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
                Q(postcode__icontains=search) #|
                #Q(enquiryNotes__icontains=search) # FIX ME - how to search in django comments?
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
class EnquiryUpdateView(HouseholdLoginRequiredMixin, AddressLookUpFormMixin, UpdateView):
    template_name = "enquiry/enquiry.html"
    form_class = EnquiryDetailForm
    model = Enquiry

    def get(self, request, *args, **kwargs):

        # Check for closed object and redirect
        obj = self.get_object()
        if obj.actioned != 0:
            if obj.sfLeadID:
                try:
                    caseObj = Case.objects.filter(deleted_on__isnull=True, sfLeadID=obj.sfLeadID).get()
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
        
        chkOpp = validate_loan(clientDict, obj.product_type) 
        context['status'] = chkOpp

        # Check for duplicates
        # Validate requirement amounts (if present)
        if obj.calcLumpSum or obj.calcIncome:
            try:
                loanStatus = validateEnquiry(str(self.kwargs['uid']))
                if loanStatus['status'] == "Ok":
                    if loanStatus['data']['errors']:
                        context['requirementError'] = 'Invalid requirement amounts'
            except:
                context['requirementError'] = 'API Error. Please ensure all required fields are entered'
                
        # Validate Address
        mappify  = apiMappify()
        address_fields = [
            'streetAddress',
            'suburb',
            'base_specificity',
            'street_number',
            'street_name',
            'street_type'
        ]
        should_validate = any(
            getattr(obj, x)
            for x in address_fields
        )
        if should_validate: 
            result = mappify.setAddress(
                {
                    "streetAddress": obj.streetAddress,
                    "suburb": obj.suburb,
                    "postcode": obj.postcode,
                    "state": dict(Enquiry.stateTypes).get(obj.state),
                    "unit": obj.base_specificity,
                    "streetnumber": obj.street_number,
                    "streetname": obj.street_name,
                    "streettype": obj.street_type
                }
            )
            if result['status'] != 'Ok':
                messages.error(self.request, "Address error. Please check address fields")
            else:
                result = mappify.checkPostalAddress()
                if result['status'] == 'Error':
                    messages.error(self.request, "Address validation. Please check address fields, or set address fields with find widget")
        context['obj'] = obj
        context['isUpdate'] = True
        context['productTypesEnum'] = productTypesEnum
        context['leadClosed'] = obj.case.caseStage == caseStagesEnum.CLOSED.value

        # Pass Calendly information
        paramStr = "?name=" + obj.name + "&email=" + (obj.email if obj.email else '')
        if obj.user:
            if obj.user.profile.calendlyUrl:
                context['calendlyUrl'] = obj.user.profile.calendlyUrl + paramStr
        else:
            context['calendlyUrl'] = ""
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

        if obj.user == None and self.request.user.profile.calendlyUrl:
            obj.user = self.request.user

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
        
        obj.closeDate = None
        obj.closeReason = None
        obj.save()

        # Background task to update SF
        app.send_task('Update_SF_Enquiry', kwargs={'enqUID': str(obj.enqUID)})

        messages.success(self.request, "Enquiry Saved")

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': str(obj.enqUID)}))


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
                qs = Enquiry.objects.filter(phoneNumber=form.cleaned_data['phoneNumber'], deleted_on__isnull=True).exclude(actioned=-1).order_by(
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
        obj.submissionOrigin = 'Client App'
        obj.origin_timestamp = timezone.now()
        obj.origin_id = obj.enqUID

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

        if self.request.user.profile.calendlyUrl:
            obj.user = self.request.user

        obj.save()

        lead = obj.case
        lead.lead_needs_action = False
        lead.save()

        # Background task to update SF

        if 'submit' in form.data:
            # Continue to enquiry
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': str(obj.case.caseUID)}))
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
            enq = Enquiry.objects.get(enqUID=kwargs['uid'])
            enq.soft_delete()
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
        sourceUrl = urljoin(
            settings.SITE_URL,
            reverse('enquiry:enqSummaryPdf', kwargs={'uid': enqUID})
        )

        targetFileName = "enquiryReports/Enquiry-" + enqUID[-12:] + ".pdf"

        pdf = pdfGenerator(enqUID)
        # UNCOMMENT THIS 
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
            app.send_task('Upload_Enquiry_Files', kwargs={'enqUID': enqUID})

        except:
            write_applog("ERROR", 'SendEnquirySummary', 'get',
                         "Failed to save PDF in Database: " + str(enq_obj.enqUID))

        email_context = {}
        email_context['user'] = enq_obj.user
        email_context['firstname'] = enq_obj.firstname
        email_context['max_loan'] = enq_obj.maxLoanAmount
        email_context['monthly_drawdown'] = enq_obj.maxDrawdownMonthly
        projectionContext = getEnquiryProjections(enqUID)
        email_context['loan_text'] = "Household Loan of ${:,}".format(enq_obj.maxLoanAmount)
        
        if enq_obj.productType == productTypesEnum.CONTINGENCY_20K.value:
            email_context['loan_text'] = "Household Loan of $20,000"
        
        if enq_obj.productType == productTypesEnum.INCOME.value: 
            email_context['loan_text'] = "Household Loan of ${:,}/month".format(enq_obj.maxDrawdownMonthly)
            if enq_obj.calcIncome:
                email_context['loan_text'] = "Household Loan of ${:,}/month".format(enq_obj.calcIncome)

        if enq_obj.productType == productTypesEnum.REFINANCE.value:
            email_context['loan_text'] = "Household Loan of ${:,}".format(projectionContext['totalLoanAmount'])

        if enq_obj.productType == productTypesEnum.LUMP_SUM.value:
            if enq_obj.calcLumpSum: 
                email_context['loan_text'] = "Household Loan of ${:,}".format(enq_obj.calcLumpSum)

        if enq_obj.productType == productTypesEnum.COMBINATION.value:
            calc_income = enq_obj.maxDrawdownMonthly
            if enq_obj.calcIncome:
                calc_income = enq_obj.calcIncome
            
            calc_lump_sum = enq_obj.maxLoanAmount
            if enq_obj.calcLumpSum:
                calc_lump_sum = enq_obj.calcLumpSum
            email_context['loan_text'] = "Household Loan of ${:,} and ${:,}/month".format(
                calc_lump_sum,
                calc_income
            )

        subject, from_email, to, bcc = "Household Loan Enquiry", \
                                       enq_obj.user.email, \
                                       enq_obj.email, \
                                       enq_obj.user.email

        text_content = "Text Message"
        attachFilename = 'HHC-Summary.pdf'
        sent = pdf.emailPdf(
            self.template_name, 
            email_context, 
            subject, 
            from_email, 
            to, 
            bcc,
            text_content, 
            attachFilename,
            other_attachments=[
                {
                    'name': "HHC-Brochure.pdf",
                    'type': 'application/pdf',
                    'content': staticfiles_storage.open('img/document/brochure.pdf', 'rb').read()
                }
            ]
        )
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
        sourceUrl = urljoin(
            settings.SITE_URL,
            reverse('enquiry:enqSummaryPdf', kwargs={'uid': enqUID})
        )

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
            app.send_task('Upload_Enquiry_Files', kwargs={'enqUID': enqUID})
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
        email_context['eligibility'] = validate_loan(clientDict, obj.product_type)
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
            self.template_name = 'enquiry/document/calculator_summary_single_20K.html'

        elif obj.productType == productTypesEnum.COMBINATION.value:
            self.template_name = 'enquiry/document/calculator_combination_summary.html'

        elif obj.productType == productTypesEnum.REFINANCE.value:
            self.template_name = 'enquiry/document/calculator_refinance_summary.html'

        else:
            self.template_name = 'enquiry/document/calculator_summary.html'

        return super(EnqSummaryPdfView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EnqSummaryPdfView, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])
        
        # Projection Results (site.utilities)
        projectionContext = getEnquiryProjections(enqUID)
        context.update(projectionContext)
        obj = Enquiry.objects.get(enqUID=enqUID)
        context['product_type'] = obj.product_type 

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
        enquiries_to_assign = []
        try:
            result = self._form_valid(form, enquiries_to_assign)
        except Exception as ex:
            try:
                assign_enquiry_leads(enquiries_to_assign, force=True)
            except Exception as ex:
                write_applog("ERROR", 'Enquiry', 'EnquiryPartnerUpload', 'Error in auto assignments', is_exception=True)
            raise
        else:
            assign_enquiry_leads(enquiries_to_assign, force=True)
            return result

    def _form_valid(self, form, enquiries_to_assign):

        fileWrapper = io.TextIOWrapper(form.cleaned_data['uploadFile'], encoding='utf-8')
        reader = csv.reader(fileWrapper)
        header = next(reader)

        write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'Commencing upload')
        partner_value = int(form.cleaned_data['partner'])
        marketing_campaign = form.cleaned_data.get('marketing_campaign')
        if partner_value == marketingTypesEnum.STARTS_AT_60.value:

            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'STARTS_AT_60')

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
                    enquiryString += "\r\nCustomer Date of birth: " + datetime.datetime.strptime(row[9], '%m/%d/%Y').strftime('%d/%m/%Y')

                    firstname, lastname, _ignore = parse_api_names(row[0], row[5])
                    payload = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "postcode": row[2],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": cleanValuation(row[6]),
                        "age_1": calcAge(row[9]),
                        "marketingSource": marketingTypesEnum.STARTS_AT_60.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user,
                        # FIX ME - do they have timestamps?
                        "enquiryNotes": enquiryString,
                    }

                    updateCreatePartnerEnquiry(payload, enquiries_to_assign)

            messages.success(self.request, "Success - enquiries imported")

        elif partner_value == marketingTypesEnum.CARE_ABOUT.value:

            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'CARE_ABOUT')

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

                    firstname, lastname, _ignore = parse_api_names(row[3], row[2])
                    payload = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "postcode": cleanValuation(row[15]),
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.CARE_ABOUT.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user,
                        # FIX ME - do they have timestamps?
                        "enquiryNotes": enquiryString,
                    }

                    updateCreatePartnerEnquiry(payload, enquiries_to_assign)

            messages.success(self.request, "Success - enquiries imported")

        elif partner_value == marketingTypesEnum.NATIONAL_SENIORS.value:
            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'NATIONAL_SENIORS')

            print(str(header))
            
            if header[0] != "Timestamp":
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            processed_count = 0 
            for row in reader: 
                firstname, lastname, _ignore = parse_api_name(row[2])

                write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'processing %s %s' % (firstname, lastname))
                email = row[3]  
                phonenumber = cleanPhoneNumber(row[5])
                if email and email != "Email": 
                    processed_count += 1
                    
                    enquiryString = "[# Updated from Partner Upload #]"
                    enquiryString += "\r\nPartner: {}".format("National Seniors")
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nCreate Date: " + row[0]
                    enquiryString += "\r\nCustomer Date of birth: " + row[9]
                    
                    payload = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "postcode": row[4],
                        "email": email,
                        "phoneNumber": phonenumber,
                        "valuation": None,
                        "age_1": calcAge(row[9]),
                        "marketingSource": partner_value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "state":  None ,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user,
                        # FIX ME - IS THE BELOW UTC?
                        #'origin_timestamp': datetime.datetime.strptime(row[0], '%m/%d/%y, %I:%M %p') if row[0] else None,
                        "enquiryNotes": enquiryString,
                    }

                    updateCreatePartnerEnquiry(payload, enquiries_to_assign)

            messages.success(self.request, "Success - enquiries imported") 

        elif partner_value == marketingTypesEnum.YOUR_LIFE_CHOICES.value:

            marketing_source_value = 'YOUR_LIFE_CHOICES' 
            marketing_source_string = 'Your Life Choices'
            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', marketing_source_value)

            # Check file format - Your Life Choices

            if header[11] != 'Create Date':
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            processed_count = 0

            for row in reader:
                firstname, lastname, _ignore = parse_api_names(row[0], row[1])

                write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'processing %s %s' % (firstname, lastname))

                email = row[2]
                phoneNumber = cleanPhoneNumber(row[5])

                if (email != "") and (email != "Email"):
                    processed_count += 1

                    enquiryString = "[# Updated from Partner Upload #]"
                    enquiryString += "\r\nPartner: {}".format(marketing_source_string)
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nOwnership: " + row[7]
                    enquiryString += "\r\nCreate Date: " + row[11]

                    payload = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "postcode": row[6],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": cleanValuation(row[9]) if row[9] else None,
                        "age_1": None,
                        "marketingSource": partner_value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "state": stateTypesEnum[row[10]].value if row[10] else None ,
                        'dwellingType': dwellingTypesEnum.APARTMENT.value if row[8] == "Strata Property" else dwellingTypesEnum.HOUSE.value,
                        "enquiryStage": enquiryStagesEnum.GENERAL_INFORMATION.value if row[4] == "Closed Lost" else enquiryStagesEnum.FOLLOW_UP_NO_ANSWER.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user,
                        #'origin_timestamp': datetime.datetime.strptime(row[0], '%d/%m/%y') if row[0] else None,
                        "enquiryNotes": enquiryString,
                    }

                    updateCreatePartnerEnquiry(payload, enquiries_to_assign)
                else:
                    write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'ignoring - NO EMAIL ADDRESS')

            messages.success(self.request, "Success - %s enquiries imported" % processed_count)

        elif partner_value == marketingTypesEnum.FACEBOOK_INTERACTIVE.value: # pseudo facebook source 
            # pseudo fb source with different file schema 
            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'FACEBOOK INTERACTIVE')
            if header[6] != 'Est. Property value':
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)
            
            for row in reader: 
                email = row[3]
                phoneNumber = cleanPhoneNumber(row[5])
                if email:
                    enquiryString = "[# Updated from Social Upload #]"
                    enquiryString += "\r\nSocial: Facebook Interactive"
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nOver 60?: " + row[1]
                    enquiryString += "\r\nValuation: " + row[6]

                    firstname, lastname, _ignore = parse_api_name(row[2])
                    payload = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "postcode": row[4],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.FACEBOOK_INTERACTIVE.value,
                        "referrer": directTypesEnum.SOCIAL.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user,
                        # FIX ME - is this UTC?
                        #'origin_timestamp': parse_date(row[0]) if row[0] else None,
                        "enquiryNotes": enquiryString,
                    }

                    updateCreatePartnerEnquiry(payload, enquiries_to_assign)

            messages.success(self.request, "Success - enquiries imported")


        elif partner_value == marketingTypesEnum.FACEBOOK.value:

            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'FACEBOOK')

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

                    firstname, lastname, _ignore = parse_api_name(row[2])
                    payload = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.FACEBOOK.value,
                        "referrer": directTypesEnum.SOCIAL.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user,
                        # FIX ME - I CAN'T FIND WHERE TO SOURCE TIMESTAMP - IT LOOKS LIKE THE DOC FORMAT MIGHT HAVE CHANGED
                        "enquiryNotes": enquiryString,
                    }

                    updateCreatePartnerEnquiry(payload, enquiries_to_assign)

            messages.success(self.request, "Success - enquiries imported")

        elif partner_value == marketingTypesEnum.LINKEDIN.value:

            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'LINKEDIN')

            # Check file format - LinkedIn

            if header[11] != 'Year of birth or Age':
                messages.warning(
                    self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            for row in reader:
                email = row[4]
                phoneNumber = cleanPhoneNumber(row[6])

                if email:
                    enquiryString = "[# Updated from Social Upload #]"
                    enquiryString += "\r\nSocial: LinkedIn"
                    enquiryString += "\r\nUpdated: " + datetime.date.today().strftime('%d/%m/%Y')
                    enquiryString += "\r\nMonth of Birth: " + row[10]
                    enquiryString += "\r\nYear of Birth: " + row[11]

                    firstname, lastname, _ignore = parse_api_names(row[2], row[3])

                    payload = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "postcode": row[5],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.LINKEDIN.value,
                        "referrer": directTypesEnum.SOCIAL.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user,
                        # FIX ME - is this UTC?
                        #'origin_timestamp': parse_date(row[0]) if row[0] else None,
                        "enquiryNotes": enquiryString,
                    }

                    updateCreatePartnerEnquiry(payload, enquiries_to_assign)

            messages.success(self.request, "Success - enquiries imported")

        return HttpResponseRedirect(self.request.path_info)


class EnquiryNotesView(HouseholdLoginRequiredMixin, TemplateView):
    template_name = "site/comments.html"

    def get_object(self):
        enqUID = str(self.kwargs['uid'])
        queryset = Enquiry.objects.queryset_byUID(str(enqUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(EnquiryNotesView, self).get_context_data(**kwargs)
        context['obj'] = self.get_object()
        return context


class EnquiryAssignView(HouseholdLoginRequiredMixin, UpdateView):
    template_name = 'enquiry/enquiryOther.html'
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
        preObj = Enquiry.objects.queryset_byUID(str(self.kwargs['uid'])).get()
        enq_obj = form.save()
        enq_obj.save(should_sync=True)

        lead = enq_obj.case 
        lead.enquiries.filter(user__isnull=True, timestamp__lte=enq_obj.timestamp).update(
            user=enq_obj.user
        )   
        # NB: we must send down the "preObj" so the user switch gets documented correctly in the enquiry notes
        # during reassignment.

        messages.success(self.request, "Enquiry assigned to " + enq_obj.user.username)
        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enq_obj.enqUID}))


class EnquiryOwnView(HouseholdLoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        enqUID = str(kwargs['uid'])
        enqObj = Enquiry.objects.queryset_byUID(enqUID).get()

        if not self.request.user.profile.calendlyUrl:

            messages.error(self.request, "You are not set-up to action this type of enquiry")

        else:
            enqObj.user = self.request.user
            enqObj.save(should_sync=True)
            lead = enqObj.case 
            lead.enquiries.filter(user__isnull=True, timestamp__lte=enqObj.timestamp).update(
                user=enqObj.user
            )
        
            messages.success(self.request, "Ownership Changed")

            # Background task to update SF

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))
