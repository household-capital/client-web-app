import csv
import json
import datetime
import pytz
from django.utils import timezone


from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.functions import TruncDate, TruncDay, TruncMonth, Cast, ExtractDay, ExtractWeek, ExtractYear, \
    Concat
from django.db.models.fields import DateField
from django.db.models import Sum, F, Func, Avg, Min, Max, Value, CharField, FloatField, BooleanField, ExpressionWrapper
from django.db.models import Count, When, Case as dbCase
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.utils.timezone import get_current_timezone

from django.views.generic import TemplateView, View

from apps.calculator.models import WebCalculator
from apps.case.models import Case, Loan
from apps.servicing.models import Facility

from apps.enquiry.models import Enquiry
from apps.lib.site_Enums import caseStagesEnum, directTypesEnum, channelTypesEnum, appTypesEnum, closeReasonEnum
from apps.lib.site_ViewUtils import updateNavQueue
from apps.lib.mixins import HouseholdLoginRequiredMixin, LoginOnlyRequiredMixin

class LandingView(LoginOnlyRequiredMixin, View):
    # Main entry point view - switch between Household Views and Referrer Views

    def get(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return HttpResponseRedirect(reverse_lazy("landing:dashboard"))
        else:
            return HttpResponseRedirect(reverse_lazy("referrer:main"))


class DashboardView(HouseholdLoginRequiredMixin, TemplateView):
    template_name = "landing/dashboard.html"

    def dateParse(self, arg):
        if isinstance(arg, datetime.date):
            return str(arg)
        if isinstance(arg, datetime.timedelta):
            return str(arg.days)

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context['title'] = 'Dashboard'

        # Time Series Data

        tsData = json.dumps(list(Enquiry.objects.timeSeries(directTypesEnum.WEB_CALCULATOR.value, 90)), default=self.dateParse)
        context['chartEmailData'] = tsData

        tsData = json.dumps(list(Enquiry.objects.timeSeries(directTypesEnum.PHONE.value, 90)), default=self.dateParse)
        context['chartPhoneData'] = tsData

        tsData = json.dumps(list(Enquiry.objects.timeSeries(directTypesEnum.WEB_ENQUIRY.value, 90)), default=self.dateParse)
        context['chartWebData'] = tsData

        # Totals
        qsEnqs = Enquiry.objects.all().exclude(closeReason=closeReasonEnum.CALL_ONLY.value)
        context['totalEnquiries'] = qsEnqs.count()
        context['webEnquiries'] = qsEnqs.filter(referrer=directTypesEnum.WEB_CALCULATOR.value).count()
        context['emailEnquiries'] = qsEnqs.filter(referrer=directTypesEnum.EMAIL.value).count() + \
                                    qsEnqs.filter(referrer=directTypesEnum.WEB_ENQUIRY.value).count()
        context['phoneEnquiries'] = qsEnqs.filter(referrer=directTypesEnum.PHONE.value).count()

        qsCases = Case.objects.all()
        context['totalCases'] = qsCases.count()
        context['meetings'] = qsCases.filter(meetingDate__isnull=False).count()

        # Funded Data
        qsFunded = Facility.objects.filter(currentBalance__gt=0, dischargeDate__isnull=True)
        if qsFunded:
            context['portfolioPlan'] = int(qsFunded.aggregate(Sum('totalPlanAmount'))['totalPlanAmount__sum'])
            context['portfolioLimit'] = int(qsFunded.aggregate(Sum('approvedAmount'))['approvedAmount__sum'])
            context['portfolioBalance'] = int(qsFunded.aggregate(Sum('currentBalance'))['currentBalance__sum'])
            context['portfolioFunded'] = int(qsFunded.aggregate(Sum('advancedAmount'))['advancedAmount__sum'])
        else:
            context['portfolioPlan'] = 0
            context['portfolioLimit'] = 0
            context['portfolioBalance'] = 0
            context['portfolioFunded'] = 0

        if context['portfolioBalance'] > 0:
            hashSum = \
                qsFunded.annotate(lvr=Sum(F('currentBalance') / F('totalValuation') * F('currentBalance'))).aggregate(
                    Sum('lvr'))['lvr__sum']
            context['portfolioLvr'] = int(hashSum / context['portfolioBalance'] * 100)

        context['portfolioLoans'] = Facility.objects.filter(currentBalance__gt=0, dischargeDate__isnull=True).count()
        context['facilityLoans'] = Facility.objects.exclude(status=0).count()
        context['caseLoans'] = qsCases.filter(caseStage=caseStagesEnum.FUNDED.value).exclude(
            appType=appTypesEnum.VARIATION.value).count()
        if context['facilityLoans'] == context['caseLoans']:
            context['clientSFRec'] = True
        else:
            context['clientSFRec'] = False

        # Update Nav Queues
        updateNavQueue(self.request)

        # LEAD GENERATION TABLE

        qsEnqs = Enquiry.objects.all().exclude(closeReason=closeReasonEnum.CALL_ONLY.value)
        tz = get_current_timezone()

        # - get monthly date range
        dateQs = qsEnqs.annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(leads=Count('enqUID')) \
            .values('date').order_by('date')

        dateRange = [item['date'].strftime('%b-%y') for item in dateQs][-12:]
        context['dateRange'] = dateRange

        # - get enquiry data and build table
        dataQs = qsEnqs \
            .annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(leads=Count('enqUID')) \
            .values('referrer', 'date', 'leads').order_by('date')

        context['directData'] = self.__createTableData(dataQs, 'referrer', 'leads')
        context['directTypesEnum'] = directTypesEnum

        tableTsPhoneData = []
        tableTsCalcData = []
        tableTsPartnerData =[]
        for key, item in context['directData'].items():
            tableTsPhoneData.append([datetime.datetime.strptime(key, "%b-%y").strftime('%Y-%m-%d'),
                                     self.__getItem(item, directTypesEnum.PHONE.value, 0)])
            tableTsCalcData.append([datetime.datetime.strptime(key, "%b-%y").strftime('%Y-%m-%d'),
                                    self.__getItem(item, directTypesEnum.WEB_CALCULATOR.value, 0)])
            tableTsPartnerData.append([datetime.datetime.strptime(key, "%b-%y").strftime('%Y-%m-%d'),
                                    self.__getItem(item, directTypesEnum.PARTNER.value, 0)])

        context['chartCalcMthData'] = tableTsCalcData[-12:]
        context['chartPhoneMthData'] = tableTsPhoneData[-12:]
        context['chartPartnerData'] = tableTsPartnerData[-12:]

        # - generate totals
        tableData = {}
        tableTsData = []
        for column in dateRange:
            total = 0
            if column in context['directData']:
                enq = context['directData'][column]
                for item, value in enq.items():
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

        context['chartMeetingData'] = json.dumps(self.__createTimeSeries(dataQs, 'meetings')[-12:],
                                                 default=self.dateParse)

        # - get zoom meeting data
        qsMeetings = Case.objects.filter(meetingDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('meetingDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(zoomMeetings=Count(dbCase(When(isZoomMeeting=True, then=1)))) \
            .values('date', 'zoomMeetings').order_by('date')

        context['chartZoomMeetingData'] = json.dumps(self.__createTimeSeries(dataQs, 'zoomMeetings')[-12:],
                                                     default=self.dateParse)

        # - get settlement data
        qsMeetings = Facility.objects.filter(settlementDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('settlementDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(settlements=Count('settlementDate')) \
            .values('date', 'settlements').order_by('date')

        context['chartSettlementData'] = json.dumps(self.__createTimeSeries(dataQs, 'settlements')[-12:],
                                                    default=self.dateParse)

        # NEW LOANS / PORTFOLIO DATA

        qsNewLoans = Facility.objects.filter(settlementDate__isnull=False).order_by("settlementDate")
        dataQs = qsNewLoans \
            .annotate(date=Cast(TruncMonth('settlementDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(newLoans=Sum('approvedAmount')) \
            .values('date', 'newLoans').order_by('date')

        context['chartNewLoansData'] = json.dumps(self.__createTimeSeries(dataQs, 'newLoans')[-12:],
                                                  default=self.dateParse)

        context['chartPortfolioData'] = json.dumps(self.__createCumulativeTimeSeries(dataQs, 'newLoans')[-12:],
                                                   default=self.dateParse)

        # AVERAGE DAYS
        qsMeetings = Facility.objects.filter(settlementDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('settlementDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(ave_days=Avg((F('settlementDate') - F('meetingDate')))) \
            .annotate(min_days=Min((F('settlementDate') - F('meetingDate')))) \
            .values('date', 'ave_days', 'min_days').order_by('date')

        context['chartAverageDays'] = json.dumps(self.__createTimeSeries(dataQs, 'ave_days')[-12:],
                                                 default=self.dateParse)
        context['chartMinDays'] = json.dumps(self.__createTimeSeries(dataQs, 'min_days')[-12:],
                                             default=self.dateParse)

        # CONVERSION  DATA
        # - get meeting conversion
        qsMeetings = Case.objects.filter(meetingDate__isnull=False)
        dataQs = qsMeetings \
            .annotate(date=Cast(TruncMonth('meetingDate', tzinfo=tz), DateField())) \
            .values_list('date') \
            .annotate(proportion=ExpressionWrapper(Value(100.0) * Count('amalLoanID') / Count('meetingDate'),
                                                   output_field=FloatField())) \
            .values('date', 'proportion').order_by('date')

        context['chartMeetingConversion'] = json.dumps(self.__createTimeSeries(dataQs, 'proportion')[-12:-3],
                                                       default=self.dateParse)

        # - get enquiry conversion
        qsEnqs = Enquiry.objects.all()
        dataQs = qsEnqs \
            .annotate(date=Cast(TruncMonth('timestamp', tzinfo=tz), DateField())) \
            .annotate(converted=dbCase(When(actioned=-1, then=True),
                                       output_field=BooleanField()
                                       )) \
            .values_list('date') \
            .annotate(proportion=ExpressionWrapper(Value(100.0) * Count('converted') / Count('enqUID'),
                                                   output_field=FloatField())) \
            .values('date', 'proportion').order_by('date')

        context['chartEnquiryConversion'] = json.dumps(self.__createTimeSeries(dataQs, 'proportion')[-12:],
                                                       default=self.dateParse)

        return context

    def __deDupe(self, qs):
        tz = get_current_timezone()
        result = qs.annotate(date=Cast(TruncDay('timestamp', tzinfo=tz), DateField())).values_list('date') \
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
            timeSeriesData.append([item['date'], item[itemName]])
        return timeSeriesData

    def __createCumulativeTimeSeries(self, dataQs, itemName):
        timeSeriesData = []
        total = 0
        for item in dataQs:
            total += item[itemName]
            timeSeriesData.append([item['date'], total])
        return timeSeriesData

    def __getItem(self, dict, key, default=None):
        if key in dict:
            return dict[key]
        else:
            return default


class Weekly(HouseholdLoginRequiredMixin, TemplateView):
    template_name = "landing/dashboard_weekly.html"

    def get_context_data(self, **kwargs):
        context = super(Weekly, self).get_context_data(**kwargs)
        context['title'] = 'Dashboard'
        tz = get_current_timezone()

        # - get ordered list
        qsDates = Case.objects.filter(meetingDate__isnull=False) \
            .annotate(
            date=Concat(ExtractYear('meetingDate'), Value('-W'), ExtractWeek('meetingDate'), output_field=CharField())) \
            .values('date') \
            .annotate(newDate=Max('meetingDate')) \
            .order_by('-newDate')

        # - get cases data
        qsCases = Case.objects.all() \
            .annotate(
            date=Concat(ExtractYear('timestamp'), Value('-W'), ExtractWeek('timestamp'), output_field=CharField())) \
            .values('date') \
            .annotate(cases=Count('caseUID')) \
            .order_by()

        # - get enquiry data
        qsEnqs = Enquiry.objects.all() \
            .annotate(
            date=Concat(ExtractYear('timestamp'), Value('-W'), ExtractWeek('timestamp'), output_field=CharField())) \
            .values('date') \
            .annotate(enquiries=Count('enqUID')) \
            .order_by()

        # - get meeting data
        qsMeetings = Case.objects.filter(meetingDate__isnull=False)
        dataMeetings = qsMeetings \
            .annotate(
            date=Concat(ExtractYear('meetingDate'), Value('-W'), ExtractWeek('meetingDate'), output_field=CharField())) \
            .values('date') \
            .annotate(meetings=Count('caseUID')) \
            .order_by()

        # - get zoom meeting data
        qsZoom = Case.objects.filter(meetingDate__isnull=False)
        dataZoom = qsZoom \
            .annotate(
            date=Concat(ExtractYear('meetingDate'), Value('-W'), ExtractWeek('meetingDate'), output_field=CharField())) \
            .values('date') \
            .annotate(zoomMeetings=Count(dbCase(When(isZoomMeeting=True, then=1)))) \
            .order_by()

        # - get settlement data
        qsSettle = Facility.objects.filter(settlementDate__isnull=False)
        dataSettle = qsSettle \
            .annotate(date=Concat(ExtractYear('settlementDate'), Value('-W'), ExtractWeek('settlementDate'),
                                  output_field=CharField())) \
            .values('date') \
            .annotate(settlements=Count('settlementDate')) \
            .order_by()

        output = []
        for item in qsDates:
            meetings = self.get_data_item('meetings', item['date'], dataMeetings)
            zoomMeetings = self.get_data_item('zoomMeetings', item['date'], dataZoom)
            settlements = self.get_data_item('settlements', item['date'], dataSettle)
            cases = self.get_data_item('cases', item['date'], qsCases)
            enquiries = self.get_data_item('enquiries', item['date'], qsEnqs)

            output.append({'date': item['date'],
                           'meetings': meetings,
                           'zoomMeetings': zoomMeetings,
                           'settlements': settlements,
                           'enquiries': enquiries,
                           'cases': cases,
                           })

        context['object_list'] = output
        context['dataMeetings'] = dataMeetings.__dict__

        return context

    def get_data_item(self, itemName, date, qs):
        try:
            value = qs.filter(date=date).get()[itemName]
        except:
            value = 0
        return value


class CalculatorExtract(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Calculator.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['CalcUID', 'LoanType', 'Age1', 'Age2', 'DwellingType', 'Valuation', 'MaxLoanAmount',
             'maxLVR', 'Postcode','Status','TimeStamp', 'Referrer'])

        qs = WebCalculator.objects.all()

        for interaction in qs:

            row = []
            row.append(interaction.calcUID)
            row.append(interaction.enumLoanType())
            row.append(interaction.age_1 if interaction.age_1 else 'null')
            row.append(interaction.age_2 if interaction.age_2 else 'null')
            row.append(interaction.enumDwellingType())
            row.append(interaction.valuation if interaction.valuation else 'null')
            row.append(interaction.maxLoanAmount if interaction.maxLoanAmount else 'null')
            row.append(interaction.maxLVR if interaction.maxLVR else 'null')
            row.append(interaction.postcode if interaction.postcode else 'null')
            row.append(interaction.status)
            row.append(timezone.localtime(interaction.timestamp))
            row.append(interaction.referrer)
            writer.writerow(row)
        return response


class EnquiryExtract(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Enquiry.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['EnqUID', 'Phone Number','LoanType', 'Age1', 'Age2', 'DwellingType', 'Valuation', 'MaxLoanAmount',
             'maxLVR', 'Postcode','Status','TimeStamp', 'Referrer', 'ReferrerID','marketingSource'])

        qs = Enquiry.objects.all()

        for interaction in qs:

            row = []
            row.append(interaction.enqUID)
            row.append(interaction.phoneNumber if interaction.phoneNumber else 'null')
            row.append(interaction.enumLoanType())
            row.append(interaction.age_1 if interaction.age_1 else 'null')
            row.append(interaction.age_2 if interaction.age_2 else 'null')
            row.append(interaction.enumDwellingType())
            row.append(interaction.valuation if interaction.valuation else 'null')
            row.append(interaction.maxLoanAmount if interaction.maxLoanAmount else 'null')
            row.append(interaction.maxLVR if interaction.maxLVR else 'null')
            row.append(interaction.postcode if interaction.postcode else 'null')
            row.append(interaction.status)
            row.append(timezone.localtime(interaction.timestamp))
            row.append(interaction.enumReferrerType())
            row.append(interaction.referrerID)
            row.append(interaction.enumMarketingSource())

            writer.writerow(row)
        return response