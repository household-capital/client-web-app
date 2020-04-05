import json
import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.functions import TruncDate, TruncDay, TruncMonth, Cast, ExtractDay
from django.db.models.fields import DateField
from django.db.models import Sum, F, Func,  Avg, Min, Max, Value, CharField
from django.db.models import Count, When, Case as dbCase
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.timezone import get_current_timezone

from django.views.generic import TemplateView, View

from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case
from apps.servicing.models import Facility, FacilityEnquiry

from apps.enquiry.models import Enquiry
from apps.lib.site_Enums import caseStagesEnum, directTypesEnum, channelTypesEnum, appTypesEnum

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


class LandingView(LoginOnlyRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return HttpResponseRedirect(reverse_lazy("landing:dashboard"))
        else:
            return HttpResponseRedirect(reverse_lazy("referrer:main"))



class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "landing/dashboard.html"

    def dateParse(self, arg):
        if isinstance(arg, datetime.date):
            return str(arg)
        if isinstance(arg,datetime.timedelta):
            return str(arg.days)

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context['title'] = 'Dashboard'

        # Time Series Data
        tsData = json.dumps(list(WebCalculator.objects.timeSeries('Interactions', 90)), default=self.dateParse)
        context['chartInteractionData'] = tsData

        tsData = json.dumps(list(WebCalculator.objects.timeSeries('Email', 90)), default=self.dateParse)
        context['chartEmailData'] = tsData

        tsData = json.dumps(list(Enquiry.objects.timeSeries('Phone', 90)), default=self.dateParse)
        context['chartPhoneData'] = tsData

        # Enquiry
        context['openEnquiries'] = Enquiry.objects.openEnquiries().count()

        # Open Case
        qsOpenCases = Case.objects.openCases()
        context['openCases'] = qsOpenCases.count()
        context['openDiscovery'] = qsOpenCases.filter(caseStage=caseStagesEnum.DISCOVERY.value).count()
        context['openMeetingHeld'] = qsOpenCases.filter(caseStage=caseStagesEnum.MEETING_HELD.value).count()
        context['openApplication'] = qsOpenCases.filter(caseStage=caseStagesEnum.APPLICATION.value).count()
        context['openDocumentation'] = qsOpenCases.filter(caseStage=caseStagesEnum.DOCUMENTATION.value).count()


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
        context['applications'] = qsCases.filter(titleDocument__isnull=False).exclude(titleDocument="").count()

        # Funded Data
        qsFunded = Facility.objects.filter(currentBalance__gt=0, dischargeDate__isnull=True)
        if qsFunded:
            context['portfolioLimit'] = int(qsFunded.aggregate(Sum('approvedAmount'))['approvedAmount__sum'])
            context['portfolioBalance'] = int(qsFunded.aggregate(Sum('currentBalance'))['currentBalance__sum'])
            context['portfolioFunded'] = int(qsFunded.aggregate(Sum('advancedAmount'))['advancedAmount__sum'])
        else:
            context['portfolioLimit'] = 0
            context['portfolioBalance']=0
            context['portfolioFunded']=0

        if context['portfolioBalance'] > 0:
            hashSum = \
            qsFunded.annotate(lvr=Sum(F('currentBalance') / F('totalValuation') * F('currentBalance'))).aggregate(Sum('lvr'))['lvr__sum']
            context['portfolioLvr'] = int(hashSum / context['portfolioBalance'] * 100)

        context['portfolioLoans'] = Facility.objects.filter(currentBalance__gt=0, dischargeDate__isnull=True).count()
        context['facilityLoans'] = Facility.objects.exclude(status=0).count()
        context['caseLoans'] = qsCases.filter(caseStage=caseStagesEnum.FUNDED.value).exclude(appType=appTypesEnum.VARIATION.value).count()
        if context['facilityLoans'] == context['caseLoans']:
            context['clientSFRec'] = True
        else:
            context['clientSFRec'] = False


        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()
        self.request.session['loanEnquiryQueue'] =  FacilityEnquiry.objects.queueCount()

        # LEAD GENERATION TABLE

        qsEnqs = Enquiry.objects.all()
        tz = get_current_timezone()

        #- get monthly date range
        dateQs = qsEnqs.annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(leads=Count('enqUID')) \
            .values('date').order_by('date')

        dateRange = [item['date'].strftime('%b-%y') for item in dateQs][-12:]
        context['dateRange'] = dateRange


        # - get enquiry data and build table
        dataQs = qsEnqs.exclude(referrer=directTypesEnum.REFERRAL.value) \
            .annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(leads=Count('enqUID')) \
            .values('referrer', 'date', 'leads').order_by('date')

        context['directData'] = self.__createTableData(dataQs, 'referrer', 'leads')
        context['directTypesEnum'] = directTypesEnum


        # - get case data and build table
        qsCases = Case.objects.all()
        dataQs = qsCases.exclude(salesChannel=channelTypesEnum.DIRECT_ACQUISITION.value) \
            .annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(cases=Count('caseUID')) \
            .values('salesChannel', 'date', 'cases').order_by('date')

        context['referralData'] = self.__createTableData(dataQs, 'salesChannel', 'cases')
        context['channelTypesEnum'] = channelTypesEnum

        # - get interaction data and build table
        qsInteractions = WebCalculator.objects.all()
        dataQs = qsInteractions \
            .annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(interactions=Count('calcUID')) \
            .annotate(type=Value('interactions', output_field=CharField())) \
            .values('type','date', 'interactions').order_by('date')

        context['interactionData'] = self.__createTableData(dataQs, 'type', 'interactions')

        #tableTsData = []
        #for key, item in context['interactionData'].items():
        #    tableTsData.append([datetime.datetime.strptime(key, "%b-%y").strftime('%Y-%m-%d'), item['interactions']])

        #context['chartInteraction'] = tableTsData[-12:]

        tableTsPhoneData = []
        tableTsCalcData = []
        for key, item in context['directData'].items():
            tableTsPhoneData.append([datetime.datetime.strptime(key, "%b-%y").strftime('%Y-%m-%d'), self.__getItem(item,directTypesEnum.PHONE.value, 0)])
            tableTsCalcData.append([datetime.datetime.strptime(key, "%b-%y").strftime('%Y-%m-%d'), self.__getItem(item,directTypesEnum.WEB_CALCULATOR.value, 0)])

        context['chartCalcMthData'] = tableTsCalcData[-12:]
        context['chartPhoneMthData'] = tableTsPhoneData[-12:]

        # - generate totals
        tableData = {}
        tableTsData=[]
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
            tableTsData.append([datetime.datetime.strptime(column, "%b-%y").strftime('%Y-%m-%d'), total])

        context['totalData'] = tableData
        context['chartEnquiry'] = tableTsData

        # MEETING AND SETTLEMENT GRAPH DATA

        # - get meeting data
        qsMeetings = Case.objects.filter(meetingDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('meetingDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(meetings=Count('caseUID')) \
            .values('date', 'meetings').order_by('date')

        context['chartMeetingData']=json.dumps(self.__createTimeSeries(dataQs, 'meetings'),default=self.dateParse)

        # - get zoom meeting data
        qsMeetings = Case.objects.filter(meetingDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('meetingDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(zoomMeetings=Count(dbCase(When(isZoomMeeting=True, then=1)))) \
            .values('date', 'zoomMeetings').order_by('date')

        context['chartZoomMeetingData']=json.dumps(self.__createTimeSeries(dataQs, 'zoomMeetings'),default=self.dateParse)

        # - get settlement data
        qsMeetings = Facility.objects.filter(settlementDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('settlementDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(settlements=Count('settlementDate')) \
            .values('date', 'settlements').order_by('date')

        context['chartSettlementData']=json.dumps(self.__createTimeSeries(dataQs, 'settlements'),default=self.dateParse)


        # NEW LOANS / PORTFOLIO DATA

        qsNewLoans = Facility.objects.filter(settlementDate__isnull=False).order_by("settlementDate")
        dataQs = qsNewLoans \
            .annotate(date=Cast(TruncMonth('settlementDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(newLoans=Sum('approvedAmount')) \
            .values('date', 'newLoans').order_by('date')

        context['chartNewLoansData'] = json.dumps(self.__createTimeSeries(dataQs, 'newLoans'),
                                                    default=self.dateParse)

        context['chartPortfolioData'] = json.dumps(self.__createCumulativeTimeSeries(dataQs, 'newLoans'),
                                                  default=self.dateParse)

        # AVERAGE DAYS
        qsMeetings = Facility.objects.filter(settlementDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('settlementDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(ave_days=Avg((F('settlementDate')-F('meetingDate')))) \
            .annotate(min_days=Min((F('settlementDate') - F('meetingDate')))) \
            .values('date', 'ave_days', 'min_days').order_by('date')

        context['chartAverageDays'] = json.dumps(self.__createTimeSeries(dataQs, 'ave_days'),
                                                  default=self.dateParse)
        context['chartMinDays'] = json.dumps(self.__createTimeSeries(dataQs, 'min_days'),
                                                  default=self.dateParse)
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

    def __createTableData(self, dataQs, labelName, itemName):
        tableData = {}
        for item in dataQs:
            if item['date'].strftime('%b-%y') not in tableData:
                tableData[item['date'].strftime('%b-%y')] = {item[labelName]: item[itemName]}
            else:
                tableData[item['date'].strftime('%b-%y')][item[labelName]] = item[itemName]
        return tableData

    def __createTimeSeries(self, dataQs, itemName):
        timeSeriesData = []
        for item in dataQs:
            timeSeriesData.append([item['date'],item[itemName]])
        return timeSeriesData

    def __createCumulativeTimeSeries(self, dataQs, itemName):
        timeSeriesData = []
        total = 0
        for item in dataQs:
            total += item[itemName]
            timeSeriesData.append([item['date'],total])
        return timeSeriesData

    def __getItem(self,dict,key, default=None):
        if key in dict:
            return dict[key]
        else:
            return default

