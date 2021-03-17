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
from .forms import EnquiryForm, EnquiryDetailForm, EnquiryAssignForm, EnquiryCallForm, \
    AddressForm, PartnerForm
from .models import Enquiry
from apps.lib.site_Utilities import getEnquiryProjections, updateNavQueue, \
    cleanPhoneNumber, validateEnquiry, cleanValuation, calcAge
from apps.lib.mixins import HouseholdLoginRequiredMixin, AddressLookUpFormMixin
from .util import assign_enquiry_leads, updateCreateEnquiry


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
        # Validate requirement amounts (if present)
        if obj.calcLumpSum or obj.calcIncome:
            loanStatus = validateEnquiry(str(self.kwargs['uid']))
            if loanStatus['status'] == "Ok":
                if loanStatus['data']['errors']:
                    context['requirementError'] = 'Invalid requirement amounts'

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
        paramStr = "?name=" + (obj.name if obj.name else '') + "&email=" + \
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
        
        obj.closeDate = None
        obj.closeReason = None
        obj.save()

        # Background task to update SF
        app.send_task('Update_SF_Enquiry', kwargs={'enqUID': str(obj.enqUID)})

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
        sourceUrl = urljoin(
            settings.SITE_URL,
            reverse('enquiry:enqSummaryPdf', kwargs={'uid': enqUID})
        )

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

class SummaryMove(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            try:
                enquiry = Enquiry.objects.get(enqUID=kwargs['uid'])
            except Enquiry.DoesNotExist: 
                messages.error(self.request, "Enquiry Doesnt exist")
                return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))
            
            case = enquiry.case
            if case is None: 
                messages.error(self.request, "Enquiry has no lead")
                return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enquiry.enqUID}))

            case.enquiryDocument = enquiry.summaryDocument
            case.save()
            messages.success(self.request, "Enquiry Summary Doccument Successfully Moved To Lead")
            return HttpResponseRedirect(
                reverse_lazy(
                    'case:caseDetail', 
                    kwargs={'uid': case.caseUID}
                )
            )
        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryList'))

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


## DEPRECATED 
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
        caseDict['propensityCategory'] = enq_obj.propensityCategory

        # address split 
        for field in address_model_fields: 
            caseDict[field] = getattr(enq_obj, field)

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
        app.send_task('Update_SF_Enquiry', kwargs={'enqUID': enqUID})

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
            app.send_task('Update_SF_Enquiry', kwargs={'enqUID': enqUID})

        return HttpResponseRedirect(reverse_lazy('enquiry:enquiryDetail', kwargs={'uid': enqUID}))

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
                    enquiryString += "\r\nCustomer Date of birth: " + datetime.datetime.strptime(row[9],
                                                                                                 '%m/%d/%Y').strftime(
                        '%d/%m/%Y')

                    payload = {
                        "name": (row[0] + " " + row[5]),
                        "postcode": row[2],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": cleanValuation(row[6]),
                        "age_1": calcAge(row[9]),
                        "marketingSource": marketingTypesEnum.STARTS_AT_60.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user
                    }

                    updateCreateEnquiry(
                        email,
                        phoneNumber,
                        payload,
                        enquiryString,
                        marketingTypesEnum.STARTS_AT_60.value,
                        enquiries_to_assign 
                    )

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

                    payload = {
                        "name": (row[3] + " " + row[2]),
                        "postcode": cleanValuation(row[15]),
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.CARE_ABOUT.value,
                        "referrer": directTypesEnum.PARTNER.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user
                    }

                    updateCreateEnquiry(
                        email,
                        phoneNumber,
                        payload,
                        enquiryString,
                        marketingTypesEnum.CARE_ABOUT.value,
                        enquiries_to_assign
                    )

            messages.success(self.request, "Success - enquiries imported")

        elif partner_value == marketingTypesEnum.NATIONAL_SENIORS.value:
            write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'NATIONAL_SENIORS')

            print(str(header))
            
            if header[0] != "Timestamp":
                messages.warning(self.request, "Unrecognised file structure - could not load")
                return HttpResponseRedirect(self.request.path_info)

            processed_count = 0 
            for row in reader: 
                name = row[2]
                write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'processing %s' % name)
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
                        "name": name,
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
                        "user": self.request.user
                    }
                    
                    updateCreateEnquiry(
                        email, 
                        phonenumber, 
                        payload,
                        enquiryString, 
                        partner_value,
                        enquiries_to_assign
                    )

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
                name = row[0]
                if row[1]:
                    name += " " + row[1]

                write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'processing %s' % name)

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
                        "name": name,
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
                        "user": self.request.user
                    }

                    updateCreateEnquiry(
                        email,
                        phoneNumber,
                        payload,
                        enquiryString,
                        partner_value,
                        enquiries_to_assign
                    )
                else:
                    write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'ignoring - NO EMAIL ADDRESS')

            messages.success(self.request, "Success - %s enquiries imported" % processed_count)

        elif partner_value == -1: # pseudo facebook source 
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

                    payload = {
                        "name": row[2],
                        "postcode": row[4],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.FACEBOOK.value,
                        "referrer": directTypesEnum.SOCIAL.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user
                    }
                    updateCreateEnquiry(
                        email,
                        phoneNumber,
                        payload,
                        enquiryString,
                        marketingTypesEnum.FACEBOOK.value,
                        enquiries_to_assign
                    )

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

                    payload = {
                        "name": row[2],
                        "postcode": row[4],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.FACEBOOK.value,
                        "referrer": directTypesEnum.SOCIAL.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user
                    }

                    updateCreateEnquiry(
                        email,
                        phoneNumber,
                        payload,
                        enquiryString,
                        marketingTypesEnum.FACEBOOK.value,
                        enquiries_to_assign
                    )

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

                    payload = {
                        "name": row[2] + " " + row[3],
                        "postcode": row[5],
                        "email": email,
                        "phoneNumber": phoneNumber,
                        "valuation": None,
                        "age_1": None,
                        "marketingSource": marketingTypesEnum.LINKEDIN.value,
                        "referrer": directTypesEnum.SOCIAL.value,
                        "productType": productTypesEnum.LUMP_SUM.value,
                        "marketing_campaign": marketing_campaign,
                        "user": self.request.user
                    }

                    updateCreateEnquiry(
                        email,
                        phoneNumber,
                        payload,
                        enquiryString,
                        marketingTypesEnum.LINKEDIN.value,
                        enquiries_to_assign
                    )

            messages.success(self.request, "Success - enquiries imported")

        return HttpResponseRedirect(self.request.path_info)

