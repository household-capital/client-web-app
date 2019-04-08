# Python Imports
import datetime
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
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View, FormView


# Third-party Imports

# Local Application Imports
from apps.calculator.models import WebCalculator
from apps.lib.loanValidator import LoanValidator
from apps.lib.enums import caseTypesEnum
from apps.lib.utilities import pdfGenerator
from apps.lib.salesforceAPI import apiSalesforce
from apps.logging import write_applog
from .forms import CaseDetailsForm, LossDetailsForm, SFPasswordForm, SolicitorForm, ValuerForm
from .models import Case, LossData
from apps.enquiry.models import Enquiry


# // UTILITIES

class SFHelper():

    def getSFids(self, sfAPI, caseObj):
        #Get SF information from generated leads
        
        # get related OpportunityID from Lead
        resultsTable = sfAPI.execSOQLQuery('OpportunityRef', caseObj.sfLeadID)
        oppID = resultsTable.iloc[0]["ConvertedOpportunityId"]
        if oppID == None:
            return (False, "Opportunity")
    
        # get related LoanID from Opportunity
        resultsTable = sfAPI.execSOQLQuery('LoanRef', oppID)
        loanID = resultsTable.iloc[0]["Name"]
        if oppID == None:
            return (False, "Loan")
    
        # save OpportunityID and LoanID
        caseObj.sfOpportunityID = oppID
        caseObj.sfLoanID = loanID
        caseObj.save(update_fields=['sfOpportunityID', 'sfLoanID'])
    
        return (True, "Success")


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
            queryset = queryset.filter(Q(caseType=caseTypesEnum.CLOSED.value) |Q(caseType=caseTypesEnum.APPROVED.value))
        else:
            queryset = queryset.exclude(caseType=caseTypesEnum.CLOSED.value).exclude(caseType=caseTypesEnum.APPROVED.value)

        # ...and for open my cases
        if self.request.GET.get('myCases') == "True":
            queryset = queryset.filter(user=self.request.user)

        # ...and orderby.....
        if self.request.GET.get('order') == None or self.request.GET.get('order')=="":
            orderBy='-updated'
        else:
            orderBy=self.request.GET.get('order')

        queryset=queryset.order_by(orderBy)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(CaseListView, self).get_context_data(**kwargs)
        context['title'] = 'Cases'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        if self.request.GET.get('showClosed') == "True":
            context['showClosed'] = "True"
        else:
            context['showClosed'] = "False"

        if self.request.GET.get('myCases') == "True":
            context['myCases'] = "True"
        else:
            context['myCases'] = "False"


        if self.request.GET.get('order') == None or self.request.GET.get('order') == "":
            context['order']= '-updated'
        else:
            context['order']=self.request.GET.get('order')

        self.request.session['webQueue'] = WebCalculator.objects.queueCount()
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

        loanObj = LoanValidator([], clientDict)
        context['status'] = loanObj.chkClientDetails()

        return context

    def form_valid(self, form):

        #Get pre-save object and check whether we can change
        pre_obj=Case.objects.filter(pk=self.kwargs.get('pk')).get()
        if pre_obj.sfLeadID:
            messages.info(self.request, "Note: your changes won't be updated in Salesforce")

        # Don't allow to manually change to Application
        if form.cleaned_data['caseType']==caseTypesEnum.APPLICATION.value and pre_obj.caseType!=caseTypesEnum.MEETING_HELD.value:
            messages.error(self.request,"Please update to Meeting Held first"  )
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': self.kwargs.get('pk')}))

        obj = form.save(commit=False)

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
        if obj.caseType == caseTypesEnum.MEETING_HELD.value and pre_obj.caseType!= caseTypesEnum.MEETING_HELD.value:
            if obj.meetingDate:
                if not obj.summaryDocument:
                    messages.warning(self.request, "Warning - there is no Loan Summary document")

                docList = (('pdfPrivacy/', "Privacy-"),
                           ('pdfElectronic/', "Electronic-"),
                           ('pdfRespLending/', "Responsible-"),
                           ('pdfClientData/', "ClientData-"))

                sourcePath = 'https://householdcapital.app/client/'
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
                messages.success(self.request,"Additional meeting documents generated")
            else:
                messages.error(self.request, "Not updated - no meeting has been recorded")
                obj.caseType=pre_obj.caseType
                obj.save(update_fields=['caseType'])

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

        # Update age if birthdate present
        if obj.birthdate_1 != None:
            obj.age_1 = datetime.date.today().year - obj.birthdate_1.year

        if obj.birthdate_2 != None:
            obj.age_2 = datetime.date.today().year - obj.birthdate_2.year

        # Set fields manually
        obj.caseType = caseTypesEnum.LEAD.value
        obj.user = self.request.user

        obj.save()
        messages.success(self.request, "Lead Created")
        return super(CaseCreateView, self).form_valid(form)


# Case Delete View (Delete View)
class CaseDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            Case.objects.filter(caseUID=kwargs['uid']).delete()
            messages.success(self.request, "Lead deleted")

        return HttpResponseRedirect(reverse_lazy('case:caseList'))


# Case Close View (Update View)
class CaseCloseView(LoginRequiredMixin, UpdateView):
    model = LossData
    template_name = 'case/caseLoss.html'
    form_class = LossDetailsForm
    context_object_name = 'obj'
    success_url = reverse_lazy('case:caseList')

    def get_object(self, queryset=None):
        queryset = LossData.objects.queryset_byUID(str(self.kwargs.get('uid')))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CaseCloseView, self).get_context_data(**kwargs)
        context['title'] = 'Close Case'
        return context

    def get_initial(self):
        initial = super(CaseCloseView, self).get_initial()
        initial['lossDate'] = datetime.datetime.today().strftime("%d/%m/%Y")
        return initial


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


# Case Email
class CaseEmailEligibility(LoginRequiredMixin, TemplateView):
    template_name = 'case/caseEmail.html'
    model = Case

    def get(self, request, *args, **kwargs):
        email_context={}
        caseUID = str(kwargs['uid'])

        queryset = Case.objects.queryset_byUID(str(caseUID))
        obj = queryset.get()

        clientDict = queryset.values()[0]
        loanObj = LoanValidator([], clientDict)
        email_context['enquiry'] = loanObj.chkClientDetails()
        email_context['obj']=obj

        subject, from_email, to = "Eligibility Summary", settings.DEFAULT_FROM_EMAIL, self.request.user.email
        text_content = "Text Message"

        html = get_template(self.template_name)
        html_content = html.render(email_context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        messages.success(self.request, "A draft email has been sent to you")
        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk':obj.pk}))

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

        attachFilename="HouseholdLoanSummary.pdf"
        bcc=caseObj.user.email

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



class CaseSalesforce(LoginRequiredMixin, FormView):
    #template_name = 'case/loanSummary/email.html'
    model = Case
    template_name = 'case/caseSend.html'
    form_class = SFPasswordForm

    def get_context_data(self, **kwargs):
        context=super(CaseSalesforce,self).get_context_data(**kwargs)
        context['title']="Salesforce Lead"
        return context

    def form_valid(self, form):

        caseUID = str(self.kwargs['uid'])
        caseDict = Case.objects.dictionary_byUID(caseUID)
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        password=form.cleaned_data['password']
        sfAPI = apiSalesforce()
        status=sfAPI.openAPI(password)

        if status:


            salesforceMap={'LastName':'surname_1','FirstName':'firstname_1','Street':'street','Postalcode':'postcode', 'City':'suburb',
                           'Phone':'phoneNumber','Email':'email','Home_Value_AVM__c':'valuation','Super_value__c':'superAmount',
                           'Pension_Value_Fortnightly__c':'pensionAmount'
                           }

            salesforceState={'NSW':'New South Wales','ACT':'Australian Capital Territory', 'VIC':'Victoria', 'NT':'Northern Territory',
                             'QLD':'Queensland', 'SA':'South Australia', "TAS":"Tasmania"}
            leadDict = {}

            for sfKey,localKey in salesforceMap.items():
                    leadDict[sfKey]=caseDict[localKey]

            try:
                leadDict['Birthdate__c']=caseObj.birthdate_1.strftime("%Y-%m-%d")
                leadDict['Gender__c']=caseObj.enumSex()[0]
            except:
                pass

            if caseObj.enumStateType():
                leadDict['State']=salesforceState[caseObj.enumStateType()]


            leadDict['Country'] = 'Australia'
            if caseObj.superFund != None:
                leadDict['Super_Fund__c']=caseObj.superFund.fundName
            leadDict['Interested__c']='Yes'
            leadDict['Type__c']='Borrower'
            result=sfAPI.createLead(leadDict)


            if result['success']:
                caseObj.sfLeadID=result['id']
                caseObj.save(update_fields=['sfLeadID'])

                messages.success(self.request, "Salesforce Lead Created!")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
            else:
                messages.error(self.request,"Lead not created: "+result['message'])
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

        else:
            messages.error(self.request, "Lead not created: Could not log-in to Salesforce API")
            return HttpResponseRedirect(reverse_lazy('case:caseSalesforce', kwargs={'uid': caseObj.caseUID}))


class CaseOwnView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        caseUID = str(kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if self.request.user.profile.isCreditRep==True:
            caseObj.user=self.request.user
            caseObj.save(update_fields=['user'])
            messages.success(self.request,"Ownership Changed")

        else:
            messages.error(self.request, "You must be a Credit Representative to take ownership")

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))


class CaseSolicitorView(LoginRequiredMixin, SFHelper, UpdateView):
    #template_name = 'case/loanSummary/email.html'
    model = Case
    template_name = 'case/caseSolicitor.html'

    form_class = SolicitorForm

    def get(self, request, *args, **kwargs):
        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if not caseObj.sfLeadID:
            messages.error(self.request, "No Salesforce lead associated with this case")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
        else:
            return super(CaseSolicitorView,self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(CaseSolicitorView, self).get_context_data(**kwargs)
        context['title'] = "Create Solicitor Instruction"

        return context

    def get_object(self, **kwargs):
        obj = Case.objects.filter(caseUID=self.kwargs['uid']).get()
        return obj

    def form_valid(self, form):

        caseObj = form.save(commit=False)
        caseObj.specialConditions=form.cleaned_data['specialConditions']
        caseObj.save()

        password = form.cleaned_data['password']
        sfAPI = apiSalesforce()
        status = sfAPI.openAPI(password)

        if status:

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
            sourcePath = 'https://householdcapital.app/client/'
            targetPath = settings.MEDIA_ROOT + "/customerReports/"
            clientUID = caseObj.caseUID

            for doc in docList:
                pdf = pdfGenerator(str(clientUID))
                pdf.createPdfFromUrl(sourcePath + doc[0] + str(clientUID), "",
                                     targetPath + doc[1] + str(clientUID)[-12:] + ".pdf")

            caseObj.solicitorInstruction = targetPath + docList[0][1] + str(clientUID)[-12:] + ".pdf"

            caseObj.save(update_fields=['solicitorInstruction'])

            email_template = 'case/caseSolicitorEmail.html'
            email_context = {}
            email_context['first_name'] = caseObj.user.first_name
            html = get_template(email_template)
            html_content = html.render(email_context)
            subject, from_email, to, bcc = "Solicitors Instructions - " + str(caseObj.sfLoanID), caseObj.user.email, \
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
    #template_name = 'case/loanSummary/email.html'
    model = Case
    template_name = 'case/caseValuer.html'

    form_class = ValuerForm

    def get(self, request, *args, **kwargs):
        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if not caseObj.sfLeadID:
            messages.error(self.request, "No Salesforce lead associated with this case")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
        else:
            return super(CaseValuerView,self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(CaseValuerView, self).get_context_data(**kwargs)
        context['title'] = "Create Valuer Instruction"

        return context

    def get_object(self, **kwargs):
        obj = Case.objects.filter(caseUID=self.kwargs['uid']).get()
        return obj

    def form_valid(self, form):

        caseObj = form.save(commit=False)
        caseObj.valuerFirm=form.cleaned_data['valuerFirm']
        caseObj.valuerEmail = form.cleaned_data['valuerEmail']
        caseObj.valuerContact = form.cleaned_data['valuerContact']

        caseObj.save()

        password = form.cleaned_data['password']
        sfAPI = apiSalesforce()
        status = sfAPI.openAPI(password)

        if status:

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
            sourcePath = 'https://householdcapital.app/client/'
            targetPath = settings.MEDIA_ROOT + "/customerReports/"
            clientUID = caseObj.caseUID

            for doc in docList:
                pdf = pdfGenerator(str(clientUID))
                pdf.createPdfFromUrl(sourcePath + doc[0] + str(clientUID), "",
                                     targetPath + doc[1] + str(clientUID)[-12:] + ".pdf")

            caseObj.valuerInstruction = targetPath + docList[0][1] + str(clientUID)[-12:] + ".pdf"

            caseObj.save(update_fields=['valuerInstruction'])

            email_template = 'case/caseValuerEmail.html'
            email_context = {}
            email_context['first_name'] = caseObj.user.first_name
            html = get_template(email_template)
            html_content = html.render(email_context)
            subject, from_email, to, bcc = "Household Capital: Valuation Instruction - " + str(caseObj.sfLoanID), caseObj.user.email, \
                                           [caseObj.valuerEmail, 'lendingservices@householdcapital.com',caseObj.user.email
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
    template_name = 'case/caseData.html'

    form_class = SFPasswordForm

    def get(self, request, *args, **kwargs):
        caseUID = str(self.kwargs['uid'])
        caseObj = Case.objects.queryset_byUID(caseUID).get()

        if not caseObj.sfLeadID:
            messages.error(self.request, "No Salesforce lead associated with this case")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
        else:
            return super(CaseDataExtract,self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(CaseDataExtract, self).get_context_data(**kwargs)
        context['title'] = "Create Application Data File"

        return context


    def form_valid(self, form):

        caseObj = Case.objects.filter(caseUID=self.kwargs['uid']).get()
        password = form.cleaned_data['password']
        sfAPI = apiSalesforce()
        status = sfAPI.openAPI(password)

        if status:

            result, message = self.getSFids(sfAPI, caseObj)

            if result == False and message == "Opportunity":
                messages.error(self.request, "Could not find Opportunity in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            if result == False and message == "Loan":
                messages.error(self.request, "Could not find Loan in Salesforce")
                return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))

            # generate dictionary
            loanDict = sfAPI.getLoanExtract(caseObj.sfOpportunityID)


            loanDict.update(Case.objects.dictionary_byUID(str(self.kwargs['uid'])))


            targetFile= settings.MEDIA_ROOT + "/customerReports/data-"+str(caseObj.caseUID)[-12:] + ".csv"

            with open(targetFile, 'w') as f:
                for key in loanDict.keys():
                    f.write("%s," % key)
                f.write("EOL\n")

                for key in loanDict.keys():
                    f.write("%s," % str(loanDict[key]).replace(",",""))
                f.write("EOL\n")
                f.close()

            caseObj.dataCSV=targetFile
            caseObj.save(update_fields=['dataCSV'])

            messages.success(self.request, "Application Data File Created")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk': caseObj.pk}))
        else:
            messages.error(self.request, "Could not log-in to Salesforce API")
            return HttpResponseRedirect(reverse_lazy('case:caseData', kwargs={'uid': str(caseObj.caseUID)}))




