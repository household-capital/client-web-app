#Python Imports
import os
import datetime

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.core.files import File
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import UpdateView, ListView, TemplateView, View

# Local Application Imports
from apps.calculator.models import WebCalculator
from apps.case.models import Case
from apps.lib.loanValidator import LoanValidator
from apps.lib.enums import caseTypesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum
from apps.lib.utilities import pdfGenerator
from apps.logging import write_applog
from .forms import EnquiryForm, ReferrerForm
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

        queryset=queryset.filter(actioned=0)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phoneNumber__icontains=search) |
                Q(postcode__icontains=search)

            )

        # ...and for open my items
        if self.request.GET.get('myEnquiries') == "True":
            queryset = queryset.filter(user=self.request.user)

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

        self.request.session['webQueue']=WebCalculator.objects.queueCount()
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
            loanObj = LoanValidator({}, clientDict)
            chkOpp = loanObj.chkClientDetails()
            context['status'] = chkOpp
            queryset = Enquiry.objects.queryset_byUID(str(self.kwargs['uid']))
            obj = queryset.get()
            context['obj'] = obj
            context['isUpdate']=True
        return context

    def form_valid(self, form):

        clientDict = form.cleaned_data
        obj = form.save(commit=False)

        loanObj = LoanValidator({}, clientDict)
        chkOpp = loanObj.chkClientDetails()

        if obj.user==None and self.request.user.profile.isCreditRep == True:
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


# Case Email
class EnquiryEmailEligibility(LoginRequiredMixin, TemplateView):
    template_name = 'enquiry/email/email_eligibility_summary.html'
    model = Enquiry

    def get(self, request, *args, **kwargs):
        email_context = {}
        enqUID = str(kwargs['uid'])

        queryset = Enquiry.objects.queryset_byUID(enqUID)
        obj = queryset.get()

        clientDict = queryset.values()[0]
        loanObj = LoanValidator([], clientDict)
        email_context['eligibility'] = loanObj.chkClientDetails()
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


class EnquiryConvert(LoginRequiredMixin, View):
    # This view does not render it creates a case from an enquiry and marks it actioned
    context_object_name = 'object_list'
    model = WebCalculator

    def get(self, request, *args, **kwargs):

        enqUID = str(kwargs['uid'])

        #get Enquiry object and dictionary
        queryset = Enquiry.objects.queryset_byUID(enqUID)
        enq_obj = queryset.get()
        enqDict = Enquiry.objects.dictionary_byUID(enqUID)

        if enqDict['name'] == None:
            enqDict['name']="Unknown"

        #Create dictionary of Case fields from Enquiry fields
        if ' ' in enqDict['name']:
            firstname, surname = enqDict['name'].split(' ',1)
        else:
            firstname=""
            surname=enqDict['name']

        caseDict={}
        caseDict['caseType']=caseTypesEnum.LEAD.value
        caseDict['caseDescription']=surname +" - "+ str(enqDict['postcode'])
        caseDict['enquiryDocument']=enqDict['summaryDocument']
        caseDict['caseNotes']=enqDict['enquiryNotes']
        caseDict['firstname_1']=firstname
        caseDict['surname_1']=surname
        caseDict['adviser']=enq_obj.enumReferrerType()
        user=self.request.user

        copyFields=['loanType','age_1','age_2', 'dwellingType', 'valuation', 'postcode', 'email', 'phoneNumber']
        for field in copyFields:
            caseDict[field]=enqDict[field]

        #Create and save new Case
        case_obj = Case.objects.create(user=user, **caseDict)
        case_obj.save()

        #Set enquiry to actioned
        enq_obj.actioned=1
        enq_obj.save()

        #Copy enquiryReport across to customerReport and add to the database
        try:
            if caseDict['enquiryDocument'] != None:

                old_file=enqDict["summaryDocument"]
                new_file=enqDict["summaryDocument"].replace('enquiryReports', 'customerReports')

                os.rename(old_file,new_file)
                print(new_file)
                case_obj.enquiryDocument.name = new_file
                case_obj.save()
        except:
            pass

        messages.success(self.request, "Enquiry converted to a new Case")

        return HttpResponseRedirect(reverse_lazy("case:caseList"))

# CALCULATOR

# Calculator Queue
class CalcListView(LoginRequiredMixin, ListView):
    paginate_by = 6
    template_name = 'enquiry/calculator/calcList.html'
    context_object_name = 'object_list'
    model = WebCalculator

    def get_queryset(self, **kwargs):
        queryset = super(CalcListView, self).get_queryset()

        queryset = queryset.filter(email__isnull=False, actioned=0).order_by('-timestamp')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(CalcListView, self).get_context_data(**kwargs)
        context['title'] = 'Web Queue'

        self.request.session['webQueue'] = WebCalculator.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context


class CalcMarkSpam(LoginRequiredMixin, UpdateView):
    # This view does not render it updates the calculator and redirects to the ListView
    context_object_name = 'object_list'
    model = WebCalculator

    def get(self, request, *args, **kwargs):
        calcUID = str(kwargs['uid'])
        queryset = WebCalculator.objects.queryset_byUID(str(calcUID))
        obj = queryset.get()
        obj.actioned = -1
        obj.save(update_fields=['actioned'])
        return HttpResponseRedirect(reverse_lazy("enquiry:calcList"))


class CalcSendDetails(LoginRequiredMixin, UpdateView):
    # This view does not render it creates and enquiry, sends an email, updates the calculator
    # and redirects to the Enquiry ListView
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'enquiry/email/email_cover_calculator.html'

    def get(self, request, *args, **kwargs):
        calcUID = str(kwargs['uid'])
        queryset = WebCalculator.objects.queryset_byUID(str(calcUID))
        obj = queryset.get()

        calcDict = WebCalculator.objects.dictionary_byUID(str(calcUID))

        # Create enquiry using WebCalculator Data
        # Remove certain items from the dictionary
        referrer = calcDict['referrer']
        calcDict.pop('calcUID')
        calcDict.pop('actionedBy')
        calcDict.pop('id')
        calcDict.pop('referrer')
        calcDict.pop('updated')
        calcDict.pop('timestamp')
        calcDict.pop('actioned')
        user = self.request.user

        enq_obj = Enquiry.objects.create(user=user,referrer=directTypesEnum.WEB_CALCULATOR.value, referrerID=referrer,
                                         **calcDict)
        enq_obj.save()

        # PRODUCE PDF REPORT
        sourceUrl = 'https://householdcapital.app/enquiry/calcSummaryPdf/' + str(enq_obj.enqUID)
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
            write_applog("ERROR", 'CalcSendDetails', 'get',
                         "Failed to save Calc Summary in Database: " + str(enq_obj.enqUID))

        email_context = {}
        email_context['user'] = request.user
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

        subject, from_email, to, bcc = "Household Loan Enquiry", \
                                       self.request.user.email, \
                                       obj.email, \
                                       self.request.user.email
        text_content = "Text Message"
        attachFilename = 'HHC-CalculatorSummary'

        sent = pdf.emailPdf(self.template_name, email_context, subject, from_email, to, bcc, text_content,
                            attachFilename)

        if sent:
            messages.success(self.request, "Client has been emailed and enquiry created")
        else:
            messages.error(self.request, "Enquiry created - but email not sent")

        obj.actioned = 1  # Actioned=1, Spam=-1
        obj.save(update_fields=['actioned'])

        return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))


# Report - Summary analytics using filters - could move to model
class CalcSummaryReportView(LoginRequiredMixin, ListView):
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'enquiry/calculator/calcSummary.html'

    def get_context_data(self, **kwargs):
        context = super(CalcSummaryReportView, self).get_context_data(**kwargs)

        context['title'] = 'Calculator Interaction Summary'
        qs = self.get_queryset()

        context['interactions'] = qs.filter().count()
        context['valid_cases'] = qs.filter(status=True).count()
        context['provided_email'] = qs.filter(email__isnull=False).count()

        context['invalid_cases'] = qs.filter(status=False).count()
        context['postcode'] = qs.filter(errorText__icontains='Postcode').count()
        context['youngest_borrower'] = qs.filter(errorText__icontains='must be 60').count()
        context['youngest_joint'] = qs.filter(errorText__icontains='must be 65').count()
        context['minimum_loan'] = qs.filter(errorText__icontains='size').count()

        context['website'] = qs.filter(referrer__icontains='calculator').count()
        context['superannuation'] = qs.filter(referrer__icontains='superannuation').count()
        context['reverse_mortgage'] = qs.filter(referrer__icontains='reverse').count()
        context['equity_release'] = qs.filter(referrer__icontains='equity').count()
        context['retirement_planning'] = qs.filter(referrer__icontains='planning').count()
        context['centrelink'] = qs.filter(referrer__icontains='centrelink').count()
        context['referrers'] = context['website'] + context['superannuation'] + context['reverse_mortgage'] + context[
            'equity_release'] + context['retirement_planning'] + context['centrelink']

        context['topUp'] = qs.filter(isTopUp=True).count()
        context['refi'] = qs.filter(isRefi=True).count()
        context['live'] = qs.filter(isLive=True).count()
        context['give'] = qs.filter(isGive=True).count()
        context['care'] = qs.filter(isCare=True).count()
        context['purposes'] = context['topUp'] + context['refi'] + context['live'] + context['give'] + context['care']

        context['NSW'] = qs.filter(postcode__startswith='2').count()
        context['VIC'] = qs.filter(postcode__startswith='3').count()
        context['QLD'] = qs.filter(postcode__startswith='4').count()
        context['SA'] = qs.filter(postcode__startswith='5').count()
        context['WA'] = qs.filter(postcode__startswith='6').count()
        context['TAS'] = qs.filter(postcode__startswith='7').count()

        today = datetime.date.today()

        for days in range(0,7):
            context['NumT'+str(days)]=qs.filter(timestamp__contains=today-datetime.timedelta(days=days)).count()
            context['DayT' + str(days)] =today- datetime.timedelta(days=days)

        return context


class CalcSummaryPdfView(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name = 'enquiry/document/calculator_summary.html'

    def get_context_data(self, **kwargs):
        context = super(CalcSummaryPdfView, self).get_context_data(**kwargs)

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
            loanObj = LoanValidator({}, clientDict)
            chkOpp = loanObj.chkClientDetails()
            context['status'] = chkOpp
            queryset = Enquiry.objects.queryset_byUID(str(self.kwargs['uid']))
            obj = queryset.get()
            context['obj'] = obj
        return context

    def form_valid(self, form):

        clientDict = form.cleaned_data
        obj = form.save(commit=False)

        loanObj = LoanValidator({}, clientDict)
        chkOpp = loanObj.chkClientDetails()

        obj.user = None
        obj.referrer=directTypesEnum.REFERRAL.value
        obj.referrerID=self.request.user.profile.referrer.companyName

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

        return HttpResponseRedirect(reverse_lazy('enquiry:enqReferrerUpdate', kwargs={'uid': str(obj.enqUID)}))


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

        bcc=enqObj.user.email
        subject, from_email, to = "Household Capital: Follow-up", enqObj.user.email, enqObj.email
        text_content = "Text Message"

        enqObj.followUp = datetime.datetime.now()
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

