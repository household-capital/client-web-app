# Python Imports
import datetime
import json
import base64
import os
import pathlib

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.calculator.models import WebCalculator
from apps.enquiry.models import Enquiry
from apps.lib.api_BurstSMS import apiBurst
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.site_DataMapping import serialisePurposes
from apps.lib.site_Enums import caseStagesEnum, EDITABLE_STAGES, PRE_MEETING_STAGES, loanTypesEnum, appTypesEnum, purposeCategoryEnum, \
    purposeIntentionEnum, incomeFrequencyEnum, productTypesEnum, clientTypesEnum, closeReasonEnumUpdated
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC
from apps.lib.site_Logging import write_applog
from apps.lib.lixi.lixi_CloudBridge import CloudBridge
from apps.lib.site_Utilities import validateLoanGetContext, \
    updateNavQueue, getProjectionResults, cleanPhoneNumber, sendTemplateEmail
from apps.lib.mixins import HouseholdLoginRequiredMixin, AddressLookUpFormMixin
from .forms import CaseDetailsForm, LossDetailsForm, SFPasswordForm, CaseAssignForm, \
    lumpSumPurposeForm, drawdownPurposeForm, purposeAddForm, smsForm
from .models import Case, LossData, Loan, ModelSetting, LoanPurposes
from apps.application.models import ApplicationDocuments
from apps.lib.api_Mappify import apiMappify
from urllib.parse import urljoin

# // UTILITIES

class SFHelper():

    def getSFids(self, sfAPI, caseObj):
        # Get SF information from generated leads

        oppID = None
        loanID = None
        # get related OpportunityID from Lead
        resultsTable = sfAPI.execSOQLQuery('OpportunityRef', caseObj.sfLeadID)
        if resultsTable['status'] == "Ok":
            oppID = resultsTable['data'].iloc[0]["ConvertedOpportunityId"]
        if oppID == None:
            return False, "Opportunity"

        # get related LoanID from Opportunity
        resultsTable = sfAPI.execSOQLQuery('LoanRef', oppID)
        if resultsTable['status'] == "Ok":
            loanID = resultsTable['data'].iloc[0]["Loan_Number__c"]
        if loanID == None:
            return False, "Loan"

        # save OpportunityID and LoanID
        caseObj.sfOpportunityID = oppID
        caseObj.sfLoanID = loanID
        caseObj.save(update_fields=['sfOpportunityID', 'sfLoanID'])

        return True, "Success"


# //MIXINS

# //CLASS BASED VIEWS

# Case List View
class CaseListView(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 8
    template_name = 'case/caseList.html'
    context_object_name = 'object_list'
    model = Case

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = super(CaseListView, self).get_queryset()

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(caseDescription__icontains=search) |
                Q(adviser__icontains=search) |
                Q(email__icontains=search) |
                Q(phoneNumber__icontains=search) |
                Q(owner__last_name__icontains=search) |
                Q(caseNotes__icontains=search) |
                Q(street__icontains=search) |
                Q(postcode__icontains=search) |
                Q(surname_1__icontains=search) |
                Q(sfLoanID__icontains=search)
            )

        # ...and for open or closed cases
        if self.request.GET.get('filter') == "Closed":
            queryset = queryset.filter(
                Q(caseStage=caseStagesEnum.CLOSED.value))

        elif self.request.GET.get('filter') == "Documentation":
            queryset = queryset.filter(
                Q(caseStage=caseStagesEnum.DOCUMENTATION.value))

        elif self.request.GET.get('filter') == "Apply":
            queryset = queryset.filter(
                Q(caseStage=caseStagesEnum.APPLICATION.value))

        elif self.request.GET.get('filter') == "Meet":
            queryset = queryset.filter(
                Q(caseStage=caseStagesEnum.MEETING_HELD.value))

        elif self.request.GET.get('filter') == "Me":
            queryset = queryset.filter(owner=self.request.user)

        elif not self.request.GET.get('search'):
            queryset = queryset.filter(
                Q(caseStage=caseStagesEnum.DISCOVERY.value))

        # ...and orderby.....
        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            orderBy = ['-updated']
        else:
            orderBy = [self.request.GET.get('order'), '-updated']

        queryset = queryset.order_by(*orderBy)[:160]

        # Temporary hidden filter
        if self.request.GET.get('filter') == "Funded":
            queryset = super(CaseListView, self).get_queryset().filter(
                Q(caseStage=caseStagesEnum.FUNDED.value)).exclude(appType=appTypesEnum.VARIATION.value).order_by(
                'surname_1')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(CaseListView, self).get_context_data(**kwargs)
        context['title'] = 'Leads'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        if self.request.GET.get('filter'):
            context['filter'] = self.request.GET.get('filter')
        else:
            context['filter'] = ""

        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            context['order'] = '-updated'
        else:
            context['order'] = self.request.GET.get('order')

        # Update Nav Queues
        updateNavQueue(self.request)

        return context


# Case Detail View (UpdateView)
class CaseDetailView(HouseholdLoginRequiredMixin, AddressLookUpFormMixin, UpdateView):
    template_name = 'case/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm
    context_object_name = 'obj'

    def get_object(self, queryset=None):
        caseUID = str(self.kwargs['uid'])
        queryset = Case.objects.queryset_byUID(str(caseUID))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Lead Detail'
        context['isUpdate'] = True
        context['caseStagesEnum'] = caseStagesEnum
        context['preMeetingStages'] = [caseStagesEnum[_stage].value for _stage in  PRE_MEETING_STAGES]
        context['appTypesEnum'] = appTypesEnum
        context['productTypesEnum'] = productTypesEnum

        clientDict = {}
        caseObj = self.object

        # Revalidate Loan
        caseLoanObj = Loan.objects.filter(case=self.object).get()
        context['isLowLVR'] = caseLoanObj.isLowLVR

        # Basic Validation only
        clientDict = caseObj.__dict__
        loanObj = LoanValidator(clientDict)
        context['status'] = loanObj.validateLoan()

        if (context['status']['status'] == 'Ok') and (caseLoanObj.totalLoanAmount != 0):
            # Undertake full validation
            context['status'].update(validateLoanGetContext(str(caseObj.caseUID)))
            if context['status']['errors']:
                messages.error(self.request, "Loan validation error")

        # Calendly
        context['calendlyUrl'] = ""

        paramStr = "?name=" + (caseObj.firstname_1 if caseObj.firstname_1 else '') + " " + \
                   (caseObj.surname_1 if caseObj.surname_1 else '') + "&email=" + \
                   (caseObj.email if caseObj.email else '')

        if self.object.owner:
            if self.object.owner.profile.calendlyInterviewUrl:
                name = "{} {}".format(
                    self.object.firstname_1 or '',
                    self.object.surname_1 or ''
                )
                paramStr = "?name=" + (name or '') + "&email=" + \
                   (self.object.email or '')
                context['calendlyDiscoveryUrl'] = self.object.owner.profile.calendlyUrl + paramStr
                context['calendlyUrl'] = self.object.owner.profile.calendlyInterviewUrl + paramStr
                context['calendlyMainUrl'] = self.object.owner.profile.calendlyUrl[
                                             :len(self.object.owner.profile.calendlyUrl) - 24]  # Refactor

        # Application Documents
        if caseObj.appUID:
            try:
                context['docList'] = ApplicationDocuments.objects.filter(application__appUID=caseObj.appUID)
            except ApplicationDocuments.DoesNotExist:
                pass
                # Validate Address
        mappify  = apiMappify()
        address_fields = [
            'street',
            'suburb',
            'base_specificity',
            'street_number',
            'street_name',
            'street_type'
        ]
        should_validate = any(
            getattr(caseObj, x)
            for x in address_fields
        )
        if should_validate: 
            result = mappify.setAddress(
                {
                    "streetAddress": caseObj.street,
                    "suburb": caseObj.suburb,
                    "postcode": caseObj.postcode,
                    "state": dict(Case.stateTypes).get(caseObj.state),
                    "unit": caseObj.base_specificity,
                    "streetnumber": caseObj.street_number,
                    "streetname": caseObj.street_name,
                    "streettype": caseObj.street_type
                }
            )
            if result['status'] != 'Ok':
                messages.error(self.request, "Address error. Please check address fields")
            else:
                result = mappify.checkPostalAddress()
                if result['status'] == 'Error':
                    messages.error(self.request, "Address validation. Please check address fields, or set address fields with find widget")
        return context

    def form_valid(self, form):

        # Get pre-save object and check whether we can change
        pre_obj = Case.objects.filter(caseUID=self.kwargs.get('uid')).get()
        initialcaseStage = pre_obj.caseStage
        loan_obj = Loan.objects.queryset_byUID(str(self.kwargs['uid'])).get()

        # Don't allow later stages to be updated in the GUI
        if initialcaseStage not in [
            caseStagesEnum[stage_].value
            for stage_ in EDITABLE_STAGES
        ]:
            messages.error(self.request, "You can no longer update this Case ")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': self.kwargs.get('uid')}))

        obj = form.save(commit=False)

        # Prior Nullable field
        if not obj.pensionAmount:
            obj.pensionAmount = 0

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

        # Update age if birthdate present and owner
        if obj.birthdate_1 != None:
            obj.age_1 = int((datetime.date.today() - obj.birthdate_1).days / 365.25)
        if obj.birthdate_2 != None:
            obj.age_2 = int((datetime.date.today() - obj.birthdate_2).days / 365.25)

        obj.save()

        # Renames and moves the image file if present
        if 'propertyImage' in self.request.FILES:
            path, filename = obj.propertyImage.name.split("/")
            ext = pathlib.Path(obj.propertyImage.name).suffix
            newFilename = path + "/property-" + str(obj.enqUID)[-12:] + ext

            try:
                originalFilename = obj.propertyImage.name
                movable_file = default_storage.open(originalFilename)
                actualFilename = default_storage.save(newFilename, movable_file)
                obj.propertyImage = actualFilename
                obj.save(update_fields=['propertyImage'])
                movable_file.close()
                default_storage.delete(originalFilename)

            except:
                pass

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

        # Check Loan Type
        if obj.clientType2 != None:
            if (
                    obj.clientType2 == clientTypesEnum.BORROWER.value or obj.clientType2 == clientTypesEnum.NOMINATED_OCCUPANT.value) and (
                    obj.loanType == loanTypesEnum.SINGLE_BORROWER.value):
                messages.error(self.request, "Warning: Loan Type should be Joint, not Single")

        # Case Field Validation
        isValid = self.checkFields(obj)

        if not isValid:
            messages.info(self.request,
                          "Saved - but not synched. Case will be synched when all required fields are completed")
        else:
            # Salesforce Synch
            self.salesforceSynch(obj)
            messages.success(self.request, "Lead has been updated")

        return super(CaseDetailView, self).form_valid(form)

    def salesforceSynch(self, caseObj):
        if caseObj.caseStage == caseStagesEnum.MEETING_HELD.value and caseObj.sfOpportunityID is None:
            # Background task to update SF and synch
            app.send_task('SF_Lead_Convert', kwargs={'caseUID': str(caseObj.caseUID)})

        elif not caseObj.sfLeadID:
            app.send_task('Create_SF_Case_Lead', kwargs={'caseUID': str(caseObj.caseUID)})

        elif not caseObj.sfOpportunityID:
            # Background task to update Lead
            app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(caseObj.caseUID)})

        else:
            # Synch with Salesforce
            app.send_task('SF_Opp_Synch', kwargs={'caseUID': str(caseObj.caseUID)})
            app.send_task('SF_Doc_Synch', kwargs={'caseUID': str(caseObj.caseUID)})

        return

    def checkFields(self, caseObj):
        requiredFields = ['loanType', 'clientType1', 'salutation_1', 'maritalStatus_1', 'surname_1',
                          'firstname_1', 'birthdate_1', 'sex_1', 'street', 'suburb', 'state',
                          'valuation', 'dwellingType']

        additionalFields = ['clientType2', 'salutation_2', 'maritalStatus_2', 'surname_2',
                            'firstname_2', 'birthdate_2', 'sex_2']

        caseDict = caseObj.__dict__

        if caseObj.loanType == None:
            return False

        if caseObj.clientType2 != None:
            requiredFields += additionalFields

        for field in requiredFields:
            if caseDict[field] == None:
                return False

        return True


# Case Create View (Create View)
class CaseCreateView(HouseholdLoginRequiredMixin, AddressLookUpFormMixin, CreateView):
    template_name = 'case/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm

    def get_context_data(self, **kwargs):
        context = super(CaseCreateView, self).get_context_data(**kwargs)
        context['title'] = 'New Lead'

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Prior Nullable field
        if not obj.pensionAmount:
            obj.pensionAmount = 0

        # Update age if birthdate present
        if obj.birthdate_1 != None:
            obj.age_1 = datetime.date.today().year - obj.birthdate_1.year

        if obj.birthdate_2 != None:
            obj.age_2 = datetime.date.today().year - obj.birthdate_2.year

        if obj.phoneNumber:
            obj.phoneNumber = cleanPhoneNumber(form.cleaned_data['phoneNumber'])

        # Set fields manually
        obj.caseStage = caseStagesEnum.UNQUALIFIED_CREATED.value
        obj.owner = self.request.user

        obj.save()
        messages.success(self.request, "Lead Created")

        # Background task to update SF
        app.send_task('Create_SF_Case_Lead', kwargs={'caseUID': str(obj.caseUID)})

        return super(CaseCreateView, self).form_valid(form)


# Case Delete View (Delete View)
class CaseDeleteView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            Case.objects.filter(caseUID=kwargs['uid']).delete()
            messages.success(self.request, "Lead deleted")

        return HttpResponseRedirect(reverse_lazy('case:caseList'))


# Refer Postcode Request
class CaseReferView(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        caseUID = str(self.kwargs['uid'])
        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)
        if result['status'] != "Ok":
            write_applog("ERROR", 'Case', 'CaseReferView', result['responseText'])
            messages.error(request, "Could not update Salesforce")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseUID}))

        # Get object
        qs = Case.objects.queryset_byUID(caseUID)
        caseObj = qs.get()

        if not caseObj.sfLeadID:
            messages.error(request, "There is no Salesforce Lead for this case")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseUID}))

        payload = {"IsReferPostCode__c": True}
        result = sfAPI.updateLead(caseObj.sfLeadID, payload)

        if result['status'] != 'Ok':
            messages.error(request, "Could not set status in Salesforce")
            write_applog("ERROR", 'Case', 'CaseReferView', result['responseText'])
        else:
            messages.success(request, "Refer postcode review requested")
            # save Enquiry Field
            caseObj.isReferPostcode = True
            caseObj.save()

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseUID}))


# Case Close View (Update View)
class CaseCloseView(HouseholdLoginRequiredMixin, UpdateView):
    model = LossData
    template_name = 'case/caseLoss.html'
    form_class = LossDetailsForm
    context_object_name = 'obj'
    success_url = reverse_lazy('case:caseList')

    def get_object(self, queryset=None):
        queryset = LossData.objects.filter(case__caseUID=str(self.kwargs.get('uid')))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CaseCloseView, self).get_context_data(**kwargs)
        context['title'] = 'Close Lead'
        context['not_proceeding_value'] = closeReasonEnumUpdated.NOT_PROCEEDING.value
        return context

    def form_valid(self, form):
        should_realign = False
        reason = form['closeReason'].value() 
        not_proceeding = form['notProceedingReason'].value()
        if reason and int(reason) != closeReasonEnumUpdated.NOT_PROCEEDING.value and not_proceeding:
            should_realign = True
        obj = form.save(commit=False)
        if form.cleaned_data['closeReason']:
            obj.closeDate = timezone.now()
        if should_realign: 
            obj.notProceedingReason = None
        obj.save()

        caseObj = Case.objects.filter(caseUID=str(self.kwargs.get('uid'))).get()
        caseObj.caseStage = caseStagesEnum.CLOSED.value
        caseObj.save(update_fields=['caseStage'])

        messages.success(self.request, "Lead closed or marked as followed-up")

        try:
            caseObj = Case.objects.filter(caseUID=str(self.kwargs.get('uid'))).get()
            if caseObj.sfOpportunityID:
                messages.info(self.request, "Please close Opportunity in Salesforce also")
        except Case.DoesNotExist:
            pass

        # Background task to update SF
        app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(obj.case.caseUID)})
        return super(CaseCloseView, self).form_valid(form)


class CaseUncloseView(HouseholdLoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        obj = Case.objects.filter(caseUID=kwargs['uid']).get()
        obj.caseStage = caseStagesEnum.UNQUALIFIED_CREATED.value
        obj.save(update_fields=['caseStage'])
        messages.success(self.request, "Lead restored")
        return HttpResponseRedirect(reverse_lazy('case:caseList'))


class CaseAnalysisView(HouseholdLoginRequiredMixin, TemplateView):
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'case/caseAnalysis.html'

    def get_context_data(self, **kwargs):
        context = super(CaseAnalysisView, self).get_context_data(**kwargs)
        context['title'] = 'Loan Analysis'
        return context


# Loan Summary Email
class CaseEmailLoanSummary(HouseholdLoginRequiredMixin, TemplateView):
    template_name = None
    model = Case

    def get(self, request, *args, **kwargs):

        caseUID = str(kwargs['uid'])
        action = int(kwargs['pk'])

        if action == 0:
            self.template_name = 'case/email/loanSummary/email.html'
        else:
            self.template_name = 'case/email/loanSummary/update-email.html'

        caseObj = Case.objects.queryset_byUID(caseUID).get()

        # Background task to email
        app.send_task('Email_Loan_Summary',
                      kwargs={'caseUID': str(caseObj.caseUID), 'template_name': self.template_name})

        messages.success(self.request, "Loan Summary emailed to client")
        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))


class CaseMailLoanSummary(HouseholdLoginRequiredMixin, TemplateView):
    '''Physically Mail Loan Summary'''

    def get(self, request, *args, **kwargs):
        email_context = {}
        caseUID = str(kwargs['uid'])

        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if caseObj.summarySentRef:
            messages.info(self.request, "Loan Summary has already been sent")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))

        ## Mail via docsaway
        app.send_task('Mail_Loan_Summary',
                      kwargs={'caseUID': str(caseObj.caseUID)})

        messages.success(self.request, "Loan Summary mailed to client")

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))


class CaseOwnView(HouseholdLoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        caseUID = str(kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if self.request.user.profile.isCreditRep == True:
            caseObj.owner = self.request.user
            caseObj.save(update_fields=['owner'])
            messages.success(self.request, "Ownership Changed")

        else:
            messages.error(self.request, "You must be a Credit Representative to take ownership")

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))


class CaseAssignView(HouseholdLoginRequiredMixin, AddressLookUpFormMixin, UpdateView):
    template_name = 'case/caseDetail.html'
    email_template_name = 'case/email/assignEmail.html'
    form_class = CaseAssignForm
    model = Enquiry

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            caseUID = str(self.kwargs['uid'])
            queryset = Case.objects.queryset_byUID(str(caseUID))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(CaseAssignView, self).get_context_data(**kwargs)
        context['title'] = 'Assign Case'

        return context

    def form_valid(self, form):
        preObj = queryset = Case.objects.queryset_byUID(str(self.kwargs['uid'])).get()

        caseObj = form.save(commit=False)
        caseObj.caseNotes += '\r\n[# Case assigned from ' + preObj.owner.username + ' #]'
        caseObj.save()

        # Email recipient
        subject, from_email, to = "Case Assigned to You", "noreply@householdcapital.app", caseObj.owner.email
        text_content = "Text Message"
        email_context = {}
        email_context['obj'] = caseObj
        email_context['base_url'] = settings.SITE_URL

        try:
            html = get_template(self.email_template_name)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except:
            pass

        messages.success(self.request, "Case assigned to " + caseObj.owner.username)
        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))


class CaseDataExtract(HouseholdLoginRequiredMixin, SFHelper, FormView):
    # This view creates a data file (.csv) for use in creating the on-boarding pack
    # The data is sourced from Salesforce
    # This is a temporary solution only

    template_name = 'case/caseData.html'
    form_class = SFPasswordForm

    def get(self, request, *args, **kwargs):
        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if not caseObj.sfLeadID:
            messages.error(self.request, "No Salesforce lead associated with this case")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))
        else:
            return super(CaseDataExtract, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CaseDataExtract, self).get_context_data(**kwargs)
        context['title'] = "Create Document Data File"
        return context

    def form_valid(self, form):
        caseObj = Case.objects.filter(caseUID=self.kwargs['uid']).get()
        sfAPI = apiSalesforce()
        statusResult = sfAPI.openAPI(True)

        if statusResult['status'] == "Ok":

            result, message = self.getSFids(sfAPI, caseObj)

            if result == False and message == "Opportunity":
                messages.error(self.request, "Could not find Opportunity in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))

            if result == False and message == "Loan":
                messages.error(self.request, "Could not find Loan in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))

            # generate dictionary from Salesforce
            loanDict = sfAPI.getOpportunityExtract(caseObj.sfOpportunityID)['data']

            # enrich SOQL based dictionary
            # parse purposes from SF and enrich SOQL dictionary

            appLoanList = ['topUpAmount', 'refinanceAmount', 'giveAmount', 'renovateAmount',
                           'travelAmount', 'careAmount', 'giveDescription', 'renovateDescription', 'travelDescription',
                           'careDescription', 'annualPensionIncome', 'topUpIncomeAmount', 'topUpFrequency',
                           'topUpPeriod',
                           'topUpBuffer', 'careRegularAmount', 'careFrequency', 'carePeriod', 'topUpContingencyAmount',
                           'topUpContingencyDescription', 'topUpDrawdownAmount', 'careDrawdownAmount',
                           'careDrawdownDescription',
                           'futureEquityAmount', 'topUpPlanAmount', 'carePlanAmount', 'planEstablishmentFee',
                           'establishmentFee']

            for fieldName in appLoanList:
                loanDict['app_' + fieldName] = ""

            # validation
            if loanDict['Brwr.Number'] == 0:
                messages.error(self.request, "Validation Error: There are no borrowers associated with the Loan")
                return HttpResponseRedirect(reverse_lazy('case:caseData', kwargs={'uid': str(caseObj.caseUID)}))

            if loanDict['Purp.NoPurposes'] == 0:
                messages.error(self.request,
                               "Validation Error: There are no purposes associated with the Opportunity")
                return HttpResponseRedirect(reverse_lazy('case:caseData', kwargs={'uid': str(caseObj.caseUID)}))

            validationFields = ['Prop.Street_Address__c', 'Prop.Suburb_City__c', 'Prop.State__c',
                                'Prop.Postcode__c', 'Prop.Property_Type__c',
                                'Prop.Home_Value_AVM__c', 'Loan.Establishment_Fee__c',
                                'Loan.Protected_Equity_Percent__c',
                                'Brwr1.Role', 'Brwr1.FirstName', 'Brwr1.LastName', 'Brwr1.Birthdate__c',
                                'Brwr1.Age__c',
                                'Brwr1.Gender__c', 'Brwr1.Permanent_Resident__c', 'Brwr1.Salutation',
                                'Brwr1.Marital_Status__c']

            if loanDict['Brwr.Number'] == 2:
                validationFields.extend(
                    ['Brwr2.Role', 'Brwr2.FirstName', 'Brwr2.LastName', 'Brwr2.Birthdate__c', 'Brwr2.Age__c',
                     'Brwr2.Gender__c', 'Brwr2.Permanent_Resident__c', 'Brwr2.Salutation',
                     'Brwr2.Marital_Status__c'])

            errorList = ['Salesforce Validation Errors: ']
            for field in validationFields:
                if loanDict[field] == None:
                    errorList.append(field + " ")

            if len(errorList) != 1:
                messages.error(self.request, "".join(errorList))
                return HttpResponseRedirect(reverse_lazy('case:caseData', kwargs={'uid': str(caseObj.caseUID)}))

            # enrich using app data
            appLoanDict = Loan.objects.dictionary_byUID(str(self.kwargs['uid']))
            appLoanobj = Loan.objects.queryset_byUID(str(self.kwargs['uid'])).get()
            appCaseObj = Case.objects.queryset_byUID(str(self.kwargs['uid'])).get()

            # Data Enrichment / Purposes - Change Purposes back

            purposeMap = ['topUpAmount', 'refinanceAmount', 'giveAmount', 'renovateAmount', 'travelAmount',
                          'careAmount', 'giveDescription',
                          'renovateDescription', 'travelDescription', 'careDescription', 'topUpDescription',
                          'topUpIncomeAmount',
                          'topUpPeriod', 'topUpBuffer', 'careRegularAmount',
                          'carePeriod', 'topUpContingencyAmount', 'topUpContingencyDescription', 'topUpDrawdownAmount',
                          'careDrawdownAmount', 'careDrawdownDescription',
                          'topUpPlanAmount', 'carePlanAmount']

            for purpose in purposeMap:
                loanDict['app_' + purpose] = appLoanDict[purpose]

            loanDict['app_topUpFrequency'] = appLoanobj.enumDrawdownFrequency()
            loanDict['app_careFrequency'] = appLoanobj.enumCareFrequency()

            if appCaseObj.superFund:
                loanDict['app_SuperFund'] = appCaseObj.superFund.fundName
            else:
                loanDict['app_SuperFund'] = "Super Fund"

            loanDict['app_SuperAmount'] = appCaseObj.superAmount
            loanDict['app_MaxLoanAmount'] = round(appLoanDict['maxLVR'] * appCaseObj.valuation / 100, 0)

            loanDict['app_annualPensionIncome'] = int(appCaseObj.pensionAmount) * 26

            loanDict['app_futureEquityAmount'] = max(
                int(loanDict['app_MaxLoanAmount']) - int(loanDict['Loan.Total_Plan_Amount__c']), 0)

            loanDict['Loan.Default_Rate__c'] = loanDict['Loan.Interest_Rate__c'] + 2

            # synch check
            if abs((appLoanDict['totalLoanAmount'] - loanDict['Loan.Total_Household_Loan_Amount__c'])) > 1:
                if loanDict['Opp.Establishment_Fee_Percent__c'] != str(LOAN_LIMITS['establishmentFee'] * 100):
                    messages.warning(self.request, "Warning: Non standard establishment fee")
                else:
                    messages.warning(self.request, "Warning: ClientApp and SF have different data")

            # write to csv file and save
            targetFile = "customerReports/data-" + str(caseObj.caseUID)[-12:] + ".csv"

            with default_storage.open(targetFile, 'w') as f:
                for key in loanDict.keys():
                    f.write("%s," % key)
                f.write("EOL\n")

                for key in loanDict.keys():
                    f.write("%s," % str(loanDict[key]).replace(",", "").replace("None", ""))
                f.write("EOL\n")
                f.close()

            caseObj.dataCSV = targetFile
            caseObj.save(update_fields=['dataCSV'])

            messages.success(self.request, "Document Data File Created")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseObj.caseUID}))

        else:
            messages.error(self.request, "Could not log-in to Salesforce API")
            return HttpResponseRedirect(reverse_lazy('case:caseData', kwargs={'uid': str(caseObj.caseUID)}))


class CloudbridgeView(HouseholdLoginRequiredMixin, TemplateView):
    template_name = 'case/caseCloudbridge.html'

    def get(self, request, *args, **kwargs):

        return super(CloudbridgeView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CloudbridgeView, self).get_context_data(**kwargs)
        context['title'] = "LIXI Submission"

        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if not caseObj.sfOpportunityID:
            messages.error(self.request, "There is no Salesforce Opportunity ID for this Case")
            return context

        if caseObj.lixiFile:
            context['isLixiFile'] = True

        logStr = ""
        if self.request.GET.get('action') == 'generate':

            # Generate and Save File Only
            CB = CloudBridge(caseObj.sfOpportunityID, False, True, True)
            result = CB.openAPIs()

            logStr = result['responseText']
            if result['status'] == "Error":
                messages.error(self.request, logStr)
                return context

            # Cursory data check
            result = CB.checkSFData()
            if result['status'] != "Ok":
                messages.error(self.request, 'SF Data Error: ' + result['responseText'])
                return context

            result = CB.createLixi()
            if result['status'] != "Ok":
                messages.error(self.request, 'Creation Error')
                context['log'] = result['log']
                return context

            caseObj.lixiFile = result['data']['filename']
            caseObj.save(update_fields=["lixiFile"])
            context['isLixiFile'] = True

            messages.success(self.request, "Successfully generated and validated")
            context['log'] = result['log']

        if self.request.GET.get('action') == 'development':

            # Send Generated File to AMAL Development

            if not caseObj.lixiFile:
                messages.error(self.request, 'No Lixi file saved for this opportunity')
                return context

            CB = CloudBridge(caseObj.sfOpportunityID, True, True, False)
            result = CB.openAPIs()

            logStr = result['responseText']
            if result['status'] == "Error":
                messages.error(self.request, logStr)
                return context

            result = CB.submitLixiFiles(caseObj.lixiFile.name)
            if result['status'] != "Ok":
                messages.error(self.request, 'Could not send file to Development - refer log')
                context['log'] = result['log']
                return context

            context['log'] = result['log']
            messages.success(self.request, "Successfully sent to AMAL Development")

        if self.request.GET.get('action') == 'production':

            # Send Generated File to AMAL Production

            if not caseObj.lixiFile:
                messages.error(self.request, 'No Lixi file saved for this opportunity')
                return context

            CB = CloudBridge(caseObj.sfOpportunityID, True, True, True)
            result = CB.openAPIs()

            logStr = result['responseText']
            if result['status'] == "Error":
                messages.error(self.request, logStr)
                return context

            result = CB.submitLixiFiles(caseObj.lixiFile.name)
            if result['status'] != "Ok":
                messages.error(self.request, 'Could not send file to Production - refer log')
                context['log'] = result['log']
                return context

            # Save AMAL submission data
            caseObj.amalIdentifier = result['data']['identifier']
            caseObj.amalLoanID = result['data']['AMAL_LoanId']
            caseObj.caseStage = caseStagesEnum.FUNDED.value
            caseObj.save(update_fields=['amalLoanID', 'amalIdentifier', 'caseStage'])

            context['log'] = result['log']
            messages.success(self.request, "Successfully sent to AMAL Production. Documents being sent in background")

            app.send_task('AMAL_Send_Docs', kwargs={'caseUID': str(caseObj.caseUID)})

        return context


# Variation Views

class ContextHelper():
    # Most of the views require the same validation and context information (uses site utility)

    def validate_and_get_context(self):

        if 'uid' in self.kwargs:
            caseUID = str(self.kwargs['uid'])
        else:
            obj = self.get_object()
            caseUID = str(obj.loan.case.caseUID)

        context = validateLoanGetContext(caseUID)

        return context


class CaseVariation(HouseholdLoginRequiredMixin, ContextHelper, ListView):
    paginate_by = 10
    template_name = 'case/variationList.html'
    context_object_name = 'object_list'
    model = LoanPurposes

    def get_queryset(self, **kwargs):
        caseUID = str(self.kwargs['uid'])
        loanObj = Loan.objects.queryset_byUID(caseUID).get()
        queryset = LoanPurposes.objects.filter(loan=loanObj)
        queryset = queryset.order_by('category')

        return queryset

    def get_context_data(self, **kwargs):
        self.extra_context = self.validate_and_get_context()

        context = super(CaseVariation, self).get_context_data(**kwargs)

        context['title'] = 'Loan Variation'

        context['caseObj'] = Case.objects.queryset_byUID(str(self.kwargs['uid'])).get()
        context['loanObj'] = Loan.objects.queryset_byUID(str(self.kwargs['uid'])).get()

        return context


class CaseVariationLumpSum(HouseholdLoginRequiredMixin, ContextHelper, UpdateView):
    template_name = "case/variationDetail.html"
    form_class = lumpSumPurposeForm

    def get_object(self, queryset=None):
        obj = LoanPurposes.objects.filter(purposeUID=self.kwargs['purposeUID']).get()
        return obj

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(CaseVariationLumpSum, self).get_context_data(**kwargs)
        context['title'] = 'Change purpose amount'

        obj = self.get_object()
        context['obj'] = obj

        return context

    def form_valid(self, form):
        obj = form.save()
        caseUID = str(obj.loan.case.caseUID)

        return HttpResponseRedirect(reverse_lazy('case:caseVariation', kwargs={'uid': caseUID}))


class CaseVariationDrawdown(HouseholdLoginRequiredMixin, ContextHelper, UpdateView):
    template_name = "case/variationDetail.html"
    form_class = drawdownPurposeForm

    def get_object(self, queryset=None):
        obj = LoanPurposes.objects.filter(purposeUID=self.kwargs['purposeUID']).get()
        return obj

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(CaseVariationDrawdown, self).get_context_data(**kwargs)
        context['title'] = 'Change purpose amount'

        obj = self.get_object()
        context['obj'] = obj

        return context

    def form_valid(self, form):
        obj = form.save()

        # Update Amounts
        if obj.drawdownFrequency == incomeFrequencyEnum.FORTNIGHTLY.value:
            freqMultiple = 26
        else:
            freqMultiple = 12

        obj.planAmount = obj.drawdownAmount * obj.planDrawdowns
        obj.amount = obj.drawdownAmount * obj.contractDrawdowns

        # if not active plan amount = contract amount
        if not obj.active:
            obj.planAmount = obj.drawdownAmount * obj.contractDrawdowns

        obj.save()

        return HttpResponseRedirect(
            reverse_lazy('case:caseVariationDrawdown', kwargs={'purposeUID': str(obj.purposeUID)}))


class CaseVariationAdd(HouseholdLoginRequiredMixin, ContextHelper, CreateView):
    template_name = "case/variationAdd.html"
    form_class = purposeAddForm
    model = LoanPurposes

    def form_valid(self, form):
        category = form.cleaned_data['category']
        intention = form.cleaned_data['intention']

        loan = Loan.objects.filter(case__caseUID=str(self.kwargs['uid'])).get()
        try:
            obj = LoanPurposes.objects.filter(loan=loan, category=category, intention=intention, active=True).get()
            messages.error(self.request, "Purpose already exists")
            return self.form_invalid(form)
        except:
            pass
        obj = form.save(commit=False)
        obj.loan = loan
        obj.save()
        return HttpResponseRedirect(reverse_lazy('case:caseVariation', kwargs={'uid': str(self.kwargs['uid'])}))

    def get_context_data(self, **kwargs):
        context = super(CaseVariationAdd, self).get_context_data(**kwargs)

        context['title'] = 'Create new purpose'

        return context


class PdfLoanVariationSummary(ContextHelper, TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "case/documents/loanVariation.html"

    def get_context_data(self, **kwargs):
        context = super(PdfLoanVariationSummary, self).get_context_data(**kwargs)

        caseUID = str(kwargs['uid'])

        # Validate the loan and generate combined context
        context = validateLoanGetContext(caseUID)

        # Get projection results (site utility using Loan Projection)
        projectionContext = getProjectionResults(context, ['baseScenario', 'intPayScenario',
                                                           'pointScenario', 'stressScenario'])
        context.update(projectionContext)

        return context


class CreateLoanVariationSummary(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        dateStr = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S%z')
        caseUID = str(self.kwargs['uid'])

        sourceUrl = urljoin(
            settings.SITE_URL, 
            reverse('case:pdfLoanVariationSummary', kwargs={'uid': caseUID})
        )
        

        targetFileName = "customerReports/VariationSummary-" + caseUID[-12:] + "-" + dateStr + ".pdf"

        pdf = pdfGenerator(caseUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'HHC-LoanVariationSummary.pdf', targetFileName)

        if not created:
            write_applog("ERROR", 'PdfProduction', 'get',
                         "Failed to generate pdf: " + caseUID)
            messages.error(self.request, "Could not generate Loan Variation Summary")

        try:
            # SAVE TO DATABASE
            qsCase = Case.objects.queryset_byUID(caseUID)
            qsCase.update(summaryDocument=targetFileName)
            messages.success(self.request, "Loan Variation Summary generated")

        except:
            write_applog("ERROR", 'PdfProduction', 'get',
                         "Failed to save Summary Report in Database: " + caseUID)
            messages.error(self.request, "Could not save Loan Variation Summary")

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseUID}))
