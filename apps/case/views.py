# Python Imports
import datetime
import json
import base64
import os
import pathlib

# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView

# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.calculator.models import WebCalculator, WebContact
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.site_Enums import caseTypesEnum
from apps.lib.site_Utilities import pdfGenerator
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.api_Mappify import apiMappify
from apps.lib.site_Logging import write_applog
from apps.lib.lixi.lixi_CloudBridge import CloudBridge
from apps.enquiry.models import Enquiry
from .forms import CaseDetailsForm, LossDetailsForm, SFPasswordForm, SolicitorForm, ValuerForm
from .models import Case, LossData, Loan


# // UTILITIES

class SFHelper():

    def getSFids(self, sfAPI, caseObj):
        # Get SF information from generated leads

        oppID=None
        loanID=None
        # get related OpportunityID from Lead
        resultsTable = sfAPI.execSOQLQuery('OpportunityRef', caseObj.sfLeadID)
        if resultsTable['status']=="Ok":
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


# //CLASS BASED VIEWS

# Case List View
class CaseListView(LoginRequiredMixin, ListView):
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
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(caseNotes__icontains=search) |
                Q(street__icontains=search) |
                Q(surname_1__icontains=search)
            )

        # ...and for open or closed cases
        if self.request.GET.get('showClosed') == "True":
            queryset = queryset.filter(
                Q(caseType=caseTypesEnum.CLOSED.value) | Q(caseType=caseTypesEnum.APPROVED.value))

        elif self.request.GET.get('showSF') == "True":
            queryset = queryset.filter(
                Q(caseType=caseTypesEnum.APPLICATION.value) | Q(caseType=caseTypesEnum.PRE_APPROVAL.value))

        else:
            queryset = queryset.exclude(caseType=caseTypesEnum.CLOSED.value).exclude(
                caseType=caseTypesEnum.APPROVED.value).exclude(caseType=caseTypesEnum.APPLICATION.value).\
                exclude(caseType=caseTypesEnum.PRE_APPROVAL.value)

        # ...and for open my cases
        if self.request.GET.get('myCases') == "True":
            queryset = queryset.filter(user=self.request.user)

        # ...and orderby.....
        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            orderBy = ['-updated']
        else:
            orderBy = [self.request.GET.get('order'), '-updated']

        queryset = queryset.order_by(*orderBy)


        return queryset

    def get_context_data(self, **kwargs):
        context = super(CaseListView, self).get_context_data(**kwargs)
        context['title'] = 'Cases'

        boolean_list=['showClosed','showSF','myCases']

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        for arg in boolean_list:
            if self.request.GET.get(arg) == "True":
                context[arg] = "True"
            else:
                context[arg] = "False"

        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            context['order'] = '-updated'
        else:
            context['order'] = self.request.GET.get('order')

        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context


# Case Detail View (UpdateView)
class CaseDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'case/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm
    context_object_name = 'obj'

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Case Detail'
        context['isUpdate'] = True
        context['caseTypesEnum'] = caseTypesEnum

        clientDict = {}
        clientDict = self.get_queryset().filter(caseID=self.object.caseID).values()[0]

        loanObj = LoanValidator(clientDict)
        context['status'] = loanObj.validateLoan()

        return context

    def form_valid(self, form):

        # Get pre-save object and check whether we can change
        pre_obj = Case.objects.filter(pk=self.kwargs.get('pk')).get()
        initialCaseType = pre_obj.caseType

        # Don't allow to manually change to Application
        if form.cleaned_data['caseType'] == caseTypesEnum.APPLICATION.value and initialCaseType == caseTypesEnum.DISCOVERY.value:
            messages.error(self.request, "Please update to Meeting Held first")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': self.kwargs.get('pk')}))

        obj = form.save(commit=False)

        #Prior Nullable field
        if not obj.pensionAmount:
            obj.pensionAmount=0

        # Update age if birthdate present and user
        if obj.birthdate_1 != None:
            obj.age_1 = int((datetime.date.today() - obj.birthdate_1).days / 365.25)
        if obj.birthdate_2 != None:
            obj.age_2 = int((datetime.date.today() - obj.birthdate_2).days / 365.25)
        obj.save()

        # Renames and moves the image file if present
        if obj.propertyImage:
            path, filename = obj.propertyImage.name.split("/")
            ext = pathlib.Path(obj.propertyImage.name).suffix

            newFilename = settings.MEDIA_ROOT + "/" + path + "/" + str(obj.caseUID) + "." + ext
            os.rename(settings.MEDIA_ROOT + "/" + obj.propertyImage.name,
                      newFilename)
            obj.propertyImage = path + "/" + str(obj.caseUID) + "." + ext
            obj.save(update_fields=['propertyImage'])

        # Checks for a closed case and redirects to Case Close View
        if obj.caseType == caseTypesEnum.CLOSED.value:
            return HttpResponseRedirect(reverse_lazy('case:caseClose', kwargs={'uid': str(obj.caseUID)}))

        # Generates documents when "Meeting Held" set or updated (move to another trigger?)
        if obj.caseType == caseTypesEnum.MEETING_HELD.value and initialCaseType == caseTypesEnum.DISCOVERY.value:
            if obj.meetingDate:
                if not obj.summaryDocument:
                    messages.warning(self.request, "Warning - there is no Loan Summary document")

                docList = (('pdfPrivacy/', "Privacy-"),
                           ('pdfElectronic/', "Electronic-"),
                           ('pdfRespLending/', "Responsible-"),
                           ('pdfClientData/', "ClientData-"))

                sourcePath = 'https://householdcapital.app/client2/'
                targetPath = settings.MEDIA_ROOT + "/customerReports/"
                clientUID = obj.caseUID

                for doc in docList:
                    pdf = pdfGenerator(str(clientUID))
                    pdf.createPdfFromUrl(sourcePath + doc[0] + str(clientUID), "",
                                         targetPath + doc[1] + str(clientUID)[-12:] + ".pdf")

                obj.privacyDocument = targetPath + docList[0][1] + str(clientUID)[-12:] + ".pdf"
                obj.electronicDocument = targetPath + docList[1][1] + str(clientUID)[-12:] + ".pdf"
                obj.responsibleDocument = targetPath + docList[2][1] + str(clientUID)[-12:] + ".pdf"
                obj.dataDocument = targetPath + docList[3][1] + str(clientUID)[-12:] + ".pdf"

                obj.save(update_fields=['privacyDocument', 'electronicDocument', 'responsibleDocument', 'dataDocument'])
                messages.success(self.request, "Additional meeting documents generated")
            else:
                messages.error(self.request, "Not updated - no meeting has been recorded")
                obj.caseType = pre_obj.caseType
                obj.save(update_fields=['caseType'])
        else:
            messages.success(self.request, "Case has been updated")

        # Convert to Opportunity if Meeting Held
        if form.cleaned_data['caseType'] == caseTypesEnum.MEETING_HELD.value and obj.sfOpportunityID is None:
            # Background task to update SF
            print("convert")
            app.send_task('SF_Lead_Convert', kwargs={'caseUID': str(obj.caseUID)})

        elif not obj.sfOpportunityID:
            #Update Lead
            app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(obj.caseUID)})

        # If status updated to Application - synch with Salesforce
        if form.cleaned_data['caseType'] == caseTypesEnum.APPLICATION.value and initialCaseType == caseTypesEnum.MEETING_HELD.value:
            if obj.sfOpportunityID:
                app.send_task('SF_Opp_Synch', kwargs={'caseUID': str(obj.caseUID)})

        return super(CaseDetailView, self).form_valid(form)


# Case Create View (Create View)
class CaseCreateView(LoginRequiredMixin, CreateView):
    template_name = 'case/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm

    def get_context_data(self, **kwargs):
        context = super(CaseCreateView, self).get_context_data(**kwargs)
        context['title'] = 'New Case'

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

        # Set fields manually
        obj.caseType = caseTypesEnum.DISCOVERY.value
        obj.user = self.request.user

        obj.save()
        messages.success(self.request, "Lead Created")

        #Background task to update SF
        app.send_task('Create_SF_Case_Lead', kwargs={'caseUID':str(obj.caseUID)})

        return super(CaseCreateView, self).form_valid(form)


# Case Delete View (Delete View)
class CaseDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            Case.objects.filter(caseUID=kwargs['uid']).delete()
            messages.success(self.request, "Case deleted")

        return HttpResponseRedirect(reverse_lazy('case:caseList'))


# Case Close View (Update View)
class CaseCloseView(LoginRequiredMixin, UpdateView):
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
        context['title'] = 'Close Case'
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        if form.cleaned_data['closeReason']:
            obj.closeDate=timezone.now()

        messages.success(self.request, "Case closed or marked as followed-up")

        # Background task to update SF
        app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(obj.case.caseUID)})
        return super(CaseCloseView, self).form_valid(form)


# Case Summary View (List View) - work in progress
class CaseSummaryView(LoginRequiredMixin, ListView):
    template_name = 'case/caseSummary.html'
    context_object_name = 'object_list'
    model = Case

    def get_queryset(self, **kwargs):
        queryset = Case.objects.all().select_related('loan', 'lossdata').order_by('-timestamp')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(CaseSummaryView, self).get_context_data(**kwargs)
        context['title'] = 'Case Summary'
        return context


class CaseAnalysisView(LoginRequiredMixin, TemplateView):
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'case/caseAnalysis.html'

    def get_context_data(self, **kwargs):
        context = super(CaseAnalysisView, self).get_context_data(**kwargs)
        context['title'] = 'Loan Analysis'
        return context



# Loan Summary Email
class CaseEmailLoanSummary(LoginRequiredMixin, TemplateView):
    template_name = 'case/loanSummary/email.html'
    model = Case

    def get(self, request, *args, **kwargs):
        email_context = {}
        caseUID = str(kwargs['uid'])

        caseObj = Case.objects.queryset_byUID(caseUID).get()

        email_context['obj'] = caseObj
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

        attachFilename = "HouseholdLoanSummary.pdf"
        bcc = caseObj.user.email

        subject, from_email, to = "Household Loan Summary Report", caseObj.user.email, caseObj.email
        text_content = "Text Message"

        localfile = open(caseObj.summaryDocument.name, 'rb')
        pdfContents = localfile.read()

        try:
            html = get_template(self.template_name)
            html_content = html.render(email_context)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to], [bcc])
            msg.attach_alternative(html_content, "text/html")
            msg.attach(attachFilename, pdfContents, 'application/pdf')
            msg.send()
            messages.success(self.request, "Loan Summary emailed to client")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

        except:
            write_applog("ERROR", 'CaseEmailLoanSummary', 'get',
                         "Failed to email Loan Summary Report:" + caseUID)
            messages.error(self.request, "Loan Summary could not be emailed")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))



class CaseOwnView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        caseUID = str(kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if self.request.user.profile.isCreditRep == True:
            caseObj.user = self.request.user
            caseObj.save(update_fields=['user'])
            messages.success(self.request, "Ownership Changed")

        else:
            messages.error(self.request, "You must be a Credit Representative to take ownership")

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))


class CaseSolicitorView(LoginRequiredMixin, SFHelper, UpdateView):
    # template_name = 'case/loanSummary/email.html'
    model = Case
    template_name = 'case/caseSolicitor.html'

    form_class = SolicitorForm

    def get(self, request, *args, **kwargs):
        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if not caseObj.valuationDocument:
            messages.error(self.request, "Please add AVM to app (if available) before instructing Solicitors")

        if not caseObj.sfLeadID:
            messages.error(self.request, "No Salesforce lead associated with this case")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
        else:
            return super(CaseSolicitorView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CaseSolicitorView, self).get_context_data(**kwargs)
        context['title'] = "Create Solicitor Instruction"

        return context

    def get_object(self, **kwargs):
        obj = Case.objects.filter(caseUID=self.kwargs['uid']).get()
        return obj

    def form_valid(self, form):

        caseObj = form.save(commit=False)
        caseObj.specialConditions = form.cleaned_data['specialConditions']
        caseObj.save()

        sfAPI = apiSalesforce()
        openResult = sfAPI.openAPI(True)

        if openResult['status']=="Ok":

            result, message = self.getSFids(sfAPI, caseObj)

            if result == False and message == "Opportunity":
                messages.error(self.request, "Instruction not created: Could not find Opportunity in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            if result == False and message == "Loan":
                messages.error(self.request, "Instruction not created: Could not find Loan in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            # generate pdf
            docList = (('pdfInstruction/', "Instruction-"),
                       )
            sourcePath = 'https://householdcapital.app/client2/'
            targetPath = settings.MEDIA_ROOT + "/customerReports/"
            clientUID = caseObj.caseUID

            for doc in docList:
                pdf = pdfGenerator(str(clientUID))
                pdf.createPdfFromUrl(sourcePath + doc[0] + str(clientUID), "",
                                     targetPath + doc[1] + str(clientUID)[-12:] + ".pdf")

            if caseObj.solicitorInstruction:
                subject_title = "Solicitors Instructions (Amendment) - "
            else:
                subject_title = "Solicitors Instructions - "

            caseObj.solicitorInstruction = targetPath + docList[0][1] + str(clientUID)[-12:] + ".pdf"

            caseObj.save(update_fields=['solicitorInstruction'])

            email_template = 'case/caseSolicitorEmail.html'
            email_context = {}
            email_context['first_name'] = caseObj.user.first_name
            html = get_template(email_template)
            html_content = html.render(email_context)

            subject, from_email, to, bcc = subject_title + str(caseObj.sfLoanID), caseObj.user.email, \
                                           [caseObj.user.email, 'lendingservices@householdcapital.com',
                                            'RL-HHC-Instructions@dentons.com',
                                            'Kelly.Ford@dentons.com'], None

            msg = EmailMultiAlternatives(subject, "Solicitors Instructions", from_email, to, bcc)

            msg.attach_alternative(html_content, "text/html")

            # Instruction Attachment
            msg.attach("Instruction-" + str(caseObj.sfLoanID) + ".pdf", pdf.getContent(), 'application/pdf')

            # RP Data Attachment
            if caseObj.valuationDocument:
                attachFilename = "Valuation-" + str(caseObj.sfLoanID) + ".pdf"
                localfile = open(caseObj.valuationDocument.path, 'rb')
                pdfContents = localfile.read()
                msg.attach(attachFilename, pdfContents, 'application/pdf')

            msg.send()

            messages.success(self.request, "Instruction sent to Dentons")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

        else:
            messages.error(self.request, "Instruction not created: Could not log-in to Salesforce API")
            return HttpResponseRedirect(reverse_lazy('case:caseSolicitor', kwargs={'uid': str(caseObj.caseUID)}))


class CaseValuerView(LoginRequiredMixin, SFHelper, UpdateView):
    # template_name = 'case/loanSummary/email.html'
    model = Case
    template_name = 'case/caseValuer.html'

    form_class = ValuerForm

    def get(self, request, *args, **kwargs):
        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        #Original process was to seek title from Dentons
        #if not caseObj.titleDocument:
        #    messages.error(self.request,
        #                   "Important! Please add title (from Dentons email) to app before instructing Valuer")

        if not caseObj.sfLeadID:
            messages.error(self.request, "No Salesforce lead associated with this case")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
        else:
            return super(CaseValuerView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CaseValuerView, self).get_context_data(**kwargs)
        context['title'] = "Create Valuer Instruction"

        return context

    def get_object(self, **kwargs):
        obj = Case.objects.filter(caseUID=self.kwargs['uid']).get()
        return obj

    def form_valid(self, form):

        caseObj = form.save(commit=False)
        caseObj.valuerFirm = form.cleaned_data['valuerFirm']
        caseObj.valuerEmail = form.cleaned_data['valuerEmail']
        caseObj.valuerContact = form.cleaned_data['valuerContact']

        caseObj.save()

        sfAPI = apiSalesforce()
        statusResult = sfAPI.openAPI(True)

        if statusResult['status']=="Ok":

            result, message = self.getSFids(sfAPI, caseObj)

            if result == False and message == "Opportunity":
                messages.error(self.request, "Instruction not created: Could not find Opportunity in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            if result == False and message == "Loan":
                messages.error(self.request, "Instruction not created: Could not find Loan in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            # generate pdf
            docList = (('pdfValInstruction/', "ValInstruction-"),
                       )
            sourcePath = 'https://householdcapital.app/client2/'
            targetPath = settings.MEDIA_ROOT + "/customerReports/"
            clientUID = caseObj.caseUID

            for doc in docList:
                pdf = pdfGenerator(str(clientUID))
                pdf.createPdfFromUrl(sourcePath + doc[0] + str(clientUID), "",
                                     targetPath + doc[1] + str(clientUID)[-12:] + ".pdf")

            caseObj.valuerInstruction = targetPath + docList[0][1] + str(clientUID)[-12:] + ".pdf"

            caseObj.save(update_fields=['valuerInstruction'])

            #Override valuer email
            temporary_email='credit@householdcapital.com'

            email_template = 'case/caseValuerEmail.html'
            email_context = {}
            email_context['first_name'] = caseObj.user.first_name
            html = get_template(email_template)
            html_content = html.render(email_context)
            subject, from_email, to, bcc = "Household Capital: Valuation Instruction - " + str(
                caseObj.sfLoanID), caseObj.user.email, \
                                           [temporary_email, 'lendingservices@householdcapital.com',
                                            caseObj.user.email
                                            ], None

            msg = EmailMultiAlternatives(subject, "Valuers Instructions", from_email, to, bcc)
            msg.attach_alternative(html_content, "text/html")

            # Instruction Attachment
            msg.attach("ValInstruction-" + str(caseObj.sfLoanID) + ".pdf", pdf.getContent(), 'application/pdf')

            # Title Attachment
            if caseObj.titleDocument:
                attachFilename = "Title-" + str(caseObj.sfLoanID) + ".pdf"
                localfile = open(caseObj.titleDocument.path, 'rb')
                pdfContents = localfile.read()
                msg.attach(attachFilename, pdfContents, 'application/pdf')

            msg.send()

            messages.success(self.request, "Instruction sent to Valuer")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

        else:
            messages.error(self.request, "Instruction not created: Could not log-in to Salesforce API")
            return HttpResponseRedirect(reverse_lazy('case:caseValuer', kwargs={'uid': str(caseObj.caseUID)}))


class CaseDataExtract(LoginRequiredMixin, SFHelper, FormView):
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
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
        else:
            return super(CaseDataExtract, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CaseDataExtract, self).get_context_data(**kwargs)
        context['title'] = "Create Application Data File"
        return context

    def form_valid(self, form):
        caseObj = Case.objects.filter(caseUID=self.kwargs['uid']).get()
        sfAPI = apiSalesforce()
        statusResult = sfAPI.openAPI(True)

        if statusResult['status'] == "Ok":

            result, message = self.getSFids(sfAPI, caseObj)

            if result == False and message == "Opportunity":
                messages.error(self.request, "Could not find Opportunity in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            if result == False and message == "Loan":
                messages.error(self.request, "Could not find Loan in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            # generate dictionary from Salesforce
            loanDict = sfAPI.getLoanExtract(caseObj.sfOpportunityID)['data']

            # enrich SOQL based dictionary
            # parse purposes from SF and enrich SOQL dictionary

            appLoanList = ['totalLoanAmount', 'topUpAmount', 'refinanceAmount', 'giveAmount', 'renovateAmount',
                           'travelAmount', 'careAmount', 'giveDescription', 'renovateDescription', 'travelDescription',
                           'careDescription', 'annualPensionIncome', 'topUpIncomeAmount', 'topUpFrequency', 'topUpPeriod',
                           'topUpBuffer','careRegularAmount','careFrequency','carePeriod','topUpContingencyAmount',
                           'topUpContingencyDescription','topUpDrawdownAmount','careDrawdownAmount','careDrawdownDescription',
                           'futureEquityAmount','topUpPlanAmount','carePlanAmount','totalPlanAmount','planEstablishmentFee',
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
                                'Prop.Home_Value_AVM__c', 'Loan.Application_Amount__c', 'Loan.Establishment_Fee__c',
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
            appLoanobj=Loan.objects.queryset_byUID(str(self.kwargs['uid'])).get()
            appCaseObj = Case.objects.queryset_byUID(str(self.kwargs['uid'])).get()

            # Data Enrichment / Purposes - Change Purposes back

            #loanDict['app_totalLoanAmount'] = int(loanDict['Loan.Application_Amount__c'])
            #if abs(int(loanDict['app_totalLoanAmount'])-appLoanDict['totalLoanAmount'])> 1:
            #    messages.error(self.request, "Salesforce and App loan amounts are different")
                #return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            purposeMap=['topUpAmount','refinanceAmount','giveAmount','renovateAmount','travelAmount','careAmount','giveDescription',
                        'renovateDescription','travelDescription','careDescription','topUpDescription','topUpIncomeAmount',
                        'topUpPeriod','topUpBuffer','careRegularAmount',
                        'carePeriod','topUpContingencyAmount','topUpContingencyDescription','topUpDrawdownAmount',
                        'careDrawdownAmount','careDrawdownDescription',
                        'topUpPlanAmount','carePlanAmount','totalPlanAmount','planEstablishmentFee','totalLoanAmount', 'establishmentFee']

            for purpose in purposeMap:
                loanDict['app_'+purpose]=appLoanDict[purpose]

            loanDict['app_topUpFrequency']=appLoanobj.enumDrawdownFrequency()
            loanDict['app_careFrequency'] = appLoanobj.enumCareFrequency()

            if appCaseObj.superFund:
                loanDict['app_SuperFund'] = appCaseObj.superFund.fundName
            else:
                loanDict['app_SuperFund'] = "Super Fund"

            loanDict['app_SuperAmount'] = appCaseObj.superAmount
            loanDict['app_MaxLoanAmount'] = round(appLoanDict['maxLVR'] * appCaseObj.valuation / 100, 0)

            loanDict['app_annualPensionIncome'] = int(appCaseObj.pensionAmount) * 26

            loanDict['app_futureEquityAmount']=max(int(loanDict['app_MaxLoanAmount'])-int(loanDict['app_totalPlanAmount']),0)

            loanDict['Loan.Default_Rate__c']=loanDict['Loan.Interest_Rate__c']+2

            # write to csv file and save
            targetFile = settings.MEDIA_ROOT + "/customerReports/data-" + str(caseObj.caseUID)[-12:] + ".csv"

            with open(targetFile, 'w') as f:
                for key in loanDict.keys():
                    f.write("%s," % key)
                f.write("EOL\n")

                for key in loanDict.keys():
                    f.write("%s," % str(loanDict[key]).replace(",", "").replace("None", ""))
                f.write("EOL\n")
                f.close()

            caseObj.dataCSV = targetFile
            caseObj.save(update_fields=['dataCSV'])

            messages.success(self.request, "Application Data File Created")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

        else:
            messages.error(self.request, "Could not log-in to Salesforce API")
            return HttpResponseRedirect(reverse_lazy('case:caseData', kwargs={'uid': str(caseObj.caseUID)}))


class CloudbridgeView(LoginRequiredMixin, TemplateView):
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

        logStr=""
        if self.request.GET.get('action') == 'generate':

            #Generate and Save File Only
            CB = CloudBridge(caseObj.sfOpportunityID, False, True, False)
            result = CB.openAPIs()

            logStr = result['responseText']
            if result['status'] == "Error":
                messages.error(self.request, logStr)
                return context

            result = CB.createLixi()
            if result['status'] != "Ok":
                messages.error(self.request, 'Creation Error')
                context['log'] = result['log']
                return context

            caseObj.lixiFile=result['data']['filename']
            caseObj.save(update_fields=["lixiFile"])

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
            print(result)

            if result['warningLog']:
                messages.warning(self.request, "Post submission errors - " + result['warningLog'])


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

            #Save AMAL submission data
            caseObj.amalIdentifier=result['data']['identifier']
            caseObj.amalLoanID = result['data']['AMAL_LoanId']

            context['log'] = result['log']
            messages.success(self.request, "Successfully sent to AMAL Production")

            if result['warningLog']:
                messages.warning(self.request, "Post submission errors - " + result['warningLog'])

        return context


# Not used - refactor
class CaseSalesforce(LoginRequiredMixin, FormView):
    # template_name = 'case/loanSummary/email.html'
    model = Case
    template_name = 'case/caseSend.html'
    form_class = SFPasswordForm

    def get(self, request, *args, **kwargs):

        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        mappify = apiMappify()
        result = mappify.setAddress({"streetAddress": caseObj.street, "suburb": caseObj.suburb,
                                     "postcode": caseObj.postcode, "state": caseObj.enumStateType()})

        if result['status'] != 'Ok':
            messages.error(self.request, 'Missing address fields - please add before sending to Salesforce')
        else:
            result = mappify.checkPostalAddress()

            if result['status'] == 'Error':
                messages.error(self.request, "No Address Match - please check before sending to Salesforce")

            if "Low Confidence" in result['responseText']:
                messages.error(self.request,
                               "Address Match - Low Confidence - please check before sending to Salesforce")
                messages.error(self.request, "Closest Match - " + result['result']['streetAddress'])

        return super(CaseSalesforce, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CaseSalesforce, self).get_context_data(**kwargs)
        context['title'] = "Salesforce Lead"
        return context

    def form_valid(self, form):

        caseUID = str(self.kwargs['uid'])
        caseDict = Case.objects.dictionary_byUID(caseUID)
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        sfAPI = apiSalesforce()
        result = sfAPI.openAPI(True)

        if result["status"]=="Ok":

            salesforceMap = {'LastName': 'surname_1', 'FirstName': 'firstname_1', 'Street': 'street',
                             'Postalcode': 'postcode', 'City': 'suburb',
                             'Phone': 'phoneNumber', 'Email': 'email', 'Home_Value_AVM__c': 'valuation',
                             'Super_value__c': 'superAmount',
                             'Pension_Value_Fortnightly__c': 'pensionAmount'
                             }

            salesforceState = {'NSW': 'New South Wales', 'ACT': 'Australian Capital Territory', 'VIC': 'Victoria',
                               'NT': 'Northern Territory', 'WA': 'Western Australia',
                               'QLD': 'Queensland', 'SA': 'South Australia', "TAS": "Tasmania"}
            leadDict = {}

            for sfKey, localKey in salesforceMap.items():
                leadDict[sfKey] = caseDict[localKey]

            try:
                leadDict['Birthdate__c'] = caseObj.birthdate_1.strftime("%Y-%m-%d")
                leadDict['Gender__c'] = caseObj.enumSex()[0]
            except:
                pass

            if caseObj.enumStateType():
                leadDict['State'] = salesforceState[caseObj.enumStateType()]

            leadDict['Country'] = 'Australia'
            leadDict['OwnerID'] = caseObj.user.profile.salesforceID

            result = sfAPI.createLead(leadDict)

            if result['status']=='Ok':
                caseObj.sfLeadID = result['data']['id']
                caseObj.save(update_fields=['sfLeadID'])

                messages.success(self.request, "Salesforce Lead Created!")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
            else:
                messages.error(self.request, "Lead not created: " + result['responseText'])
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

        else:
            messages.error(self.request, "Lead not created: Could not log-in to Salesforce API")
            return HttpResponseRedirect(reverse_lazy('case:caseSalesforce', kwargs={'uid': caseObj.caseUID}))

