import datetime
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from django.views.generic import TemplateView

from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case
from apps.enquiry.models import Enquiry
from apps.lib.enums import caseTypesEnum, directTypesEnum


# Create your views here.

class LoginOnlyRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginOnlyRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)


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


class LandingView(LoginOnlyRequiredMixin, TemplateView):
    template_name = "landing/main_landing.html"

    def get(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return HttpResponseRedirect(reverse_lazy("landing:dashboard"))
        else:
            return HttpResponseRedirect(reverse_lazy("enquiry:enqReferrerCreate"))

    def get_context_data(self, **kwargs):
        context = super(LandingView, self).get_context_data(**kwargs)
        context['page_description'] = 'Please choose an application'
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "landing/dashboard.html"

    def dateParse(self, arg):
        if isinstance(arg, datetime.date):
            return str(arg)

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context['title'] = 'Dashboard'

        # Time Series Data
        tsData = json.dumps(list(WebCalculator.objects.timeSeries('Interactions', 90)), default=self.dateParse)
        context['chartInteractionData'] = tsData

        tsData = json.dumps(list(WebCalculator.objects.timeSeries('Email', 90)), default=self.dateParse)
        context['chartEmailData'] = tsData

        # Pipeline Health
        caseHealth = Case.objects.pipelineHealth()
        enquiryHealth = Enquiry.objects.pipelineHealth()

        context['caseHealth'] = caseHealth
        if caseHealth[0] > .74:
            context['caseColor'] = "#28a745"
        else:
            context['caseColor'] = "#fdb600"

        context['enquiryHealth'] = enquiryHealth
        if enquiryHealth[0] > .74:
            context['enquiryColor'] = "#28a745"
        else:
            context['enquiryColor'] = "#fdb600"

        # Enquiry
        context['openEnquiries'] = Enquiry.objects.openEnquiries().count()

        # Open Case
        qsOpenCases = Case.objects.openCases()
        context['openCases'] = qsOpenCases.count()
        context['openLead'] = qsOpenCases.filter(caseType=caseTypesEnum.LEAD.value).count()
        context['openOpportunity'] = qsOpenCases.filter(caseType=caseTypesEnum.OPPORTUNITY.value).count()
        context['openMeetingHeld'] = qsOpenCases.filter(caseType=caseTypesEnum.MEETING_HELD.value).count()
        context['openApplication'] = qsOpenCases.filter(caseType=caseTypesEnum.APPLICATION.value).count()
        context['openPreApproval'] = qsOpenCases.filter(caseType=caseTypesEnum.PRE_APPROVAL.value).count()

        # Totals
        qsEnqs = Enquiry.objects.all()
        context['totalEnquiries'] = qsEnqs.count()
        context['webEnquiries'] = qsEnqs.filter(referrer=directTypesEnum.WEB_CALCULATOR.value).count()
        context['emailEnquiries'] = qsEnqs.filter(referrer=directTypesEnum.EMAIL.value).count() + \
                                    qsEnqs.filter(referrer=directTypesEnum.WEB_ENQUIRY.value).count()
        context['phoneEnquiries'] = qsEnqs.filter(referrer=directTypesEnum.PHONE.value).count()
        context['referralEnquiries'] = qsEnqs.filter(referrer=directTypesEnum.REFERRAL.value).count()

        qsCases = Case.objects.all()
        context['totalCases'] = qsCases.count()
        context['meetings'] = qsCases.filter(meetingDate__isnull=False).count()
        context['applications'] = qsCases.filter(solicitorInstruction__isnull=False).exclude(
            solicitorInstruction__exact="").count()
        context['approvals'] = qsCases.filter(caseType=caseTypesEnum.APPROVED.value).count()

        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context


class DashboardCalcView(LoginRequiredMixin, TemplateView):
    template_name = "landing/dashboard_calc.html"

    def dateParse(self, arg):
        if isinstance(arg, datetime.date):
            return str(arg)

    def get_context_data(self, **kwargs):
        context = super(DashboardCalcView, self).get_context_data(**kwargs)
        context['title'] = 'Dashboard'

        # Time Series Data

        context['dataNSW']= json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90,2)), default=self.dateParse)
        context['dataVic'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90, 3)),default=self.dateParse)
        context['dataQld']= json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90,4)), default=self.dateParse)
        context['dataSA']= json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90,5)), default=self.dateParse)
        context['dataWA']= json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90,6)), default=self.dateParse)
        context['dataTas']= json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90,7)), default=self.dateParse)

        context['dataSEO']= json.dumps(list(WebCalculator.objects.timeSeries('InteractionsBySource', 90,True)), default=self.dateParse)
        context['dataSEM']= json.dumps(list(WebCalculator.objects.timeSeries('InteractionsBySource', 90,False)), default=self.dateParse)

        context['dataEmailSEO']= json.dumps(list(WebCalculator.objects.timeSeries('EmailBySource', 90,True)), default=self.dateParse)
        context['dataEmailSEM']= json.dumps(list(WebCalculator.objects.timeSeries('EmailBySource', 90, False)), default=self.dateParse)

        # Calculator Summary Data
        qs = WebCalculator.objects.all()
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

        context['topUp'] = qs.filter(isTopUp=True).count()
        context['refi'] = qs.filter(isRefi=True).count()
        context['live'] = qs.filter(isLive=True).count()
        context['give'] = qs.filter(isGive=True).count()
        context['care'] = qs.filter(isCare=True).count()

        context['NSW'] = qs.filter(postcode__startswith='2').count()
        context['VIC'] = qs.filter(postcode__startswith='3').count()
        context['QLD'] = qs.filter(postcode__startswith='4').count()
        context['SA'] = qs.filter(postcode__startswith='5').count()
        context['WA'] = qs.filter(postcode__startswith='6').count()
        context['TAS'] = qs.filter(postcode__startswith='7').count()

        context['website_email'] = qs.filter(referrer__icontains='calculator', email__isnull=False).count()
        context['superannuation_email'] = qs.filter(referrer__icontains='superannuation',email__isnull=False).count()
        context['reverse_mortgage_email'] = qs.filter(referrer__icontains='reverse',email__isnull=False).count()
        context['equity_release_email'] = qs.filter(referrer__icontains='equity',email__isnull=False).count()
        context['retirement_planning_email'] = qs.filter(referrer__icontains='planning',email__isnull=False).count()
        context['centrelink_email'] = qs.filter(referrer__icontains='centrelink',email__isnull=False).count()

        context['NSW_email'] = qs.filter(postcode__startswith='2',email__isnull=False).count()
        context['VIC_email'] = qs.filter(postcode__startswith='3',email__isnull=False).count()
        context['QLD_email'] = qs.filter(postcode__startswith='4',email__isnull=False).count()
        context['SA_email'] = qs.filter(postcode__startswith='5',email__isnull=False).count()
        context['WA_email'] = qs.filter(postcode__startswith='6',email__isnull=False).count()
        context['TAS_email'] = qs.filter(postcode__startswith='7',email__isnull=False).count()


        return context
