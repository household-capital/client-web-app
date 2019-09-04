import datetime
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.functions import TruncDate, TruncDay, TruncMonth, Cast
from django.db.models.fields import DateField
from django.db.models import Sum, F, Func
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.timezone import get_current_timezone

from django.views.generic import TemplateView

from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case, FundedData

from apps.enquiry.models import Enquiry
from apps.lib.site_Enums import caseTypesEnum, directTypesEnum, channelTypesEnum


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
            context['caseColor'] = "#5184a1"
        else:
            context['caseColor'] = "#fdb600"

        context['enquiryHealth'] = enquiryHealth
        if enquiryHealth[0] > .74:
            context['enquiryColor'] = "#5184a1"
        else:
            context['enquiryColor'] = "#fdb600"

        # Enquiry
        context['openEnquiries'] = Enquiry.objects.openEnquiries().count()

        # Open Case
        qsOpenCases = Case.objects.openCases()
        context['openCases'] = qsOpenCases.count()
        context['openDiscovery'] = qsOpenCases.filter(caseType=caseTypesEnum.DISCOVERY.value).count()
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

        # Funded Data
        qsFunded = FundedData.objects.all()
        if qsFunded:
            context['portfolioBalance'] = int(qsFunded.aggregate(Sum('principal'))['principal__sum'])
            context['portfolioFunded'] = int(qsFunded.aggregate(Sum('advanced'))['advanced__sum'])
        else:
            context['portfolioBalance']=0
            context['portfolioFunded']=0

        if context['portfolioBalance'] > 0:
            hashSum = \
            qsFunded.annotate(lvr=Sum(F('principal') / F('totalValuation') * F('principal'))).aggregate(Sum('lvr'))[
                'lvr__sum']
            context['portfolioLvr'] = int(hashSum / context['portfolioBalance'] * 100)

        context['portfolioLoans'] = qsFunded.filter(principal__gt=0).count()

        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        # Lead Generation
        qsEnqs = Enquiry.objects.all()
        tz = get_current_timezone()

        # - get enquiry data and build table
        dataQs = qsEnqs.exclude(referrer=directTypesEnum.REFERRAL.value) \
            .annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(leads=Count('enqUID')) \
            .values('referrer', 'date', 'leads').order_by('date')

        tableData = {}
        for item in dataQs:
            if item['date'].strftime('%b-%y') not in tableData:
                tableData[item['date'].strftime('%b-%y')] = {item['referrer']: item['leads']}
            else:
                tableData[item['date'].strftime('%b-%y')][item['referrer']] = item['leads']

        context['directData'] = tableData
        context['directTypesEnum'] = directTypesEnum

        #- get monthly date range
        dateQs = qsEnqs.annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(leads=Count('enqUID')) \
            .values('date').order_by('date')

        dateRange = [item['date'].strftime('%b-%y') for item in dateQs]

        # - get case data and build table
        qsCases = Case.objects.all()
        dataQs = qsCases.exclude(salesChannel=channelTypesEnum.DIRECT_ACQUISITION.value) \
            .annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(cases=Count('caseUID')) \
            .values('salesChannel', 'date', 'cases').order_by('date')

        tableData = {}
        for item in dataQs:
            if item['date'].strftime('%b-%y') not in tableData:
                tableData[item['date'].strftime('%b-%y')] = {item['salesChannel']: item['cases']}
            else:
                tableData[item['date'].strftime('%b-%y')][item['salesChannel']] = item['cases']

        context['dateRange'] = dateRange
        context['referralData'] = tableData
        context['channelTypesEnum'] = channelTypesEnum

        tableData = {}
        for column in dateRange:
            total = 0
            if column in context['directData']:
                enq = context['directData'][column]
                for item, value in enq.items():
                    total += value
            if column in context['referralData']:
                case = context['referralData'][column]
                for item, value in case.items():
                    total += value
            tableData[column] = total

        context['totalData'] = tableData

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

        context['dataNSW'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90, 2)),
                                        default=self.dateParse)
        context['dataVic'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90, 3)),
                                        default=self.dateParse)
        context['dataQld'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90, 4)),
                                        default=self.dateParse)
        context['dataSA'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90, 5)),
                                       default=self.dateParse)
        context['dataWA'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90, 6)),
                                       default=self.dateParse)
        context['dataTas'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsByState', 90, 7)),
                                        default=self.dateParse)

        context['dataSEO'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsBySource', 90, True)),
                                        default=self.dateParse)
        context['dataSEM'] = json.dumps(list(WebCalculator.objects.timeSeries('InteractionsBySource', 90, False)),
                                        default=self.dateParse)

        context['dataEmailSEO'] = json.dumps(list(WebCalculator.objects.timeSeries('EmailBySource', 90, True)),
                                             default=self.dateParse)
        context['dataEmailSEM'] = json.dumps(list(WebCalculator.objects.timeSeries('EmailBySource', 90, False)),
                                             default=self.dateParse)

        # Calculator Summary Data
        qs = WebCalculator.objects.all()

        context['interactions'] = self.__deDupe(qs.filter())
        context['valid_cases'] = self.__deDupe(qs.filter(status=True))
        context['provided_email'] = qs.filter(email__isnull=False).count()

        context['invalid_cases'] = self.__deDupe(qs.filter(status=False))
        context['postcode'] = self.__deDupe(qs.filter(errorText__icontains='Postcode'))
        context['youngest_borrower'] = self.__deDupe(qs.filter(errorText__icontains='must be 60'))
        context['youngest_joint'] = self.__deDupe(qs.filter(errorText__icontains='must be 65'))
        context['minimum_loan'] = self.__deDupe(qs.filter(errorText__icontains='size'))

        context['website'] = self.__deDupe(qs.filter(referrer__icontains='calculator'))
        context['superannuation'] = self.__deDupe(qs.filter(referrer__icontains='superannuation'))
        context['reverse_mortgage'] = self.__deDupe(qs.filter(referrer__icontains='reverse'))
        context['equity_release'] = self.__deDupe(qs.filter(referrer__icontains='equity'))
        context['retirement_planning'] = self.__deDupe(qs.filter(referrer__icontains='planning'))
        context['centrelink'] = self.__deDupe(qs.filter(referrer__icontains='centrelink'))
        context['refinance'] = self.__deDupe(qs.filter(referrer__icontains='refinance'))

        context['topUp'] = self.__deDupe(qs.filter(isTopUp=True))
        context['refi'] = self.__deDupe(qs.filter(isRefi=True))
        context['live'] = self.__deDupe(qs.filter(isLive=True))
        context['give'] = self.__deDupe(qs.filter(isGive=True))
        context['care'] = self.__deDupe(qs.filter(isCare=True))

        context['NSW'] = self.__deDupe(qs.filter(postcode__startswith='2'))
        context['VIC'] = self.__deDupe(qs.filter(postcode__startswith='3'))
        context['QLD'] = self.__deDupe(qs.filter(postcode__startswith='4'))
        context['SA'] = self.__deDupe(qs.filter(postcode__startswith='5'))
        context['WA'] = self.__deDupe(qs.filter(postcode__startswith='6'))
        context['TAS'] = self.__deDupe(qs.filter(postcode__startswith='7'))

        context['website_email'] = self.__deDupe(qs.filter(referrer__icontains='calculator', email__isnull=False))
        context['superannuation_email'] = self.__deDupe(
            qs.filter(referrer__icontains='superannuation', email__isnull=False))
        context['reverse_mortgage_email'] = self.__deDupe(qs.filter(referrer__icontains='reverse', email__isnull=False))
        context['equity_release_email'] = self.__deDupe(qs.filter(referrer__icontains='equity', email__isnull=False))
        context['retirement_planning_email'] = self.__deDupe(
            qs.filter(referrer__icontains='planning', email__isnull=False))
        context['centrelink_email'] = self.__deDupe(qs.filter(referrer__icontains='centrelink', email__isnull=False))
        context['refinance_email'] = self.__deDupe(qs.filter(referrer__icontains='refinance', email__isnull=False))

        context['NSW_email'] = self.__deDupe(qs.filter(postcode__startswith='2', email__isnull=False))
        context['VIC_email'] = self.__deDupe(qs.filter(postcode__startswith='3', email__isnull=False))
        context['QLD_email'] = self.__deDupe(qs.filter(postcode__startswith='4', email__isnull=False))
        context['SA_email'] = self.__deDupe(qs.filter(postcode__startswith='5', email__isnull=False))
        context['WA_email'] = self.__deDupe(qs.filter(postcode__startswith='6', email__isnull=False))
        context['TAS_email'] = self.__deDupe(qs.filter(postcode__startswith='7', email__isnull=False))

        return context

    def __deDupe(self, qs):
        tz = get_current_timezone()
        result=qs.annotate(date=Cast(TruncDay('timestamp', tzinfo=tz), DateField())).values_list('date') \
            .annotate(interactions=Count('postcode', distinct=True)) \
            .values_list('date', 'interactions').aggregate(Sum('interactions'))['interactions__sum']
        if result:
            return result
        else:
            return 0
