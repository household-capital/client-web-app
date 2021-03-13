#Python Imports
import uuid, os, reversion
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db import models
from django.db.models.functions import TruncDate,TruncDay, Cast
from django.db.models import Count
from django.db.models.fields import DateField
from django.utils.timezone import get_current_timezone
from django.utils.encoding import smart_text
from django.urls import reverse_lazy
from django.db.models import Q

from apps.helpers.model_utils import ReversionModel

from urllib.parse import urljoin
#Local Imports
from apps.lib.site_Enums import *
from apps.case.model_utils import get_existing_case, create_case_from_enquiry
from config.celery import app
from apps.base.model_utils import AbstractAddressModel

class EnquiryManager(models.Manager):

    #Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self,uidString):
        searchWeb = Enquiry.objects.get(enqUID=uuid.UUID(uidString)).pk
        return super(EnquiryManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

    # Custom data queries
    def queueCount(self):
        return Enquiry.objects.filter(user__isnull=True,actioned=0).count()

    def openEnquiries(self):
        return Enquiry.objects.filter(actioned=0, followUp__isnull=True).exclude(status=False,user__isnull=False)

    def __timeSeriesQry(self, qs, length):
        #utility function appended to base time series query
        tz = get_current_timezone()
        qryDate=datetime.now(tz)-timedelta(days=length)

        return qs.filter(timestamp__gte=qryDate).annotate(date=Cast(TruncDay('timestamp', tzinfo=tz), DateField())) \
                   .values_list('date') \
                   .annotate(interactions=Count('enqUID',distinct=True)) \
                   .values_list('date', 'interactions').order_by('-date')

    def timeSeries(self, seriesType, length, search=None):

        result = self.__timeSeriesQry(Enquiry.objects.filter(referrer=seriesType), length)

        return result if result else {}

    def find_duplicates_QS(self, email, phoneNumber):
        if email and phoneNumber:
            query = (Q(email__iexact=email) | Q(phoneNumber=phoneNumber))
        elif email:
            query = Q(email__iexact=email)
        elif phoneNumber:
            query = Q(phoneNumber=phoneNumber)
        else:
            raise Exception('email or phone must be present')

        return Enquiry.objects.filter(query)

    def find_duplicates(self, email, phoneNumber, order_by="-updated"):
        return self.find_duplicates_QS(email, phoneNumber).order_by(order_by)


class MarketingCampaign(models.Model):

    campaign_name = models.CharField(max_length=200, unique=True)
    
    def __str__(self):
        return smart_text(self.campaign_name)

@reversion.register()
class Enquiry(AbstractAddressModel, ReversionModel, models.Model):

    productTypes = (
        (productTypesEnum.LUMP_SUM.value, "Lump Sum"),
        (productTypesEnum.INCOME.value, "Income"),
        (productTypesEnum.COMBINATION.value, "Combination"),
        (productTypesEnum.CONTINGENCY_20K.value, "Contingency 20K"),
        (productTypesEnum.REFINANCE.value, "Refinance"),

    )

    loanTypes = (
        (loanTypesEnum.SINGLE_BORROWER.value, 'Single'),
        (loanTypesEnum.JOINT_BORROWER.value, 'Joint')
    )

    dwellingTypes = (
        (dwellingTypesEnum.HOUSE.value, 'House'),
        (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    referrerTypes=(
        (directTypesEnum.PHONE.value,'Phone'),
        (directTypesEnum.EMAIL.value, 'Email'),
        (directTypesEnum.WEB_ENQUIRY.value,'Web'),
        (directTypesEnum.SOCIAL.value, 'Social'),
        (directTypesEnum.WEB_CALCULATOR.value, 'Calculator'),
        (directTypesEnum.PARTNER.value, 'Partner'),
        (directTypesEnum.BROKER.value, 'Broker'),
        (directTypesEnum.ADVISER.value, 'Adviser'),
        (directTypesEnum.OTHER.value,'Other'),
    )

    refferTypesHTML = (
        (directTypesEnum.PHONE.value, '<i class="fas fa-mobile"></i> Phone'),
        (directTypesEnum.EMAIL.value, '<i class="fas fa-envelope"></i> Email'),
        (directTypesEnum.WEB_ENQUIRY.value,'<i class="fas fa-mouse-pointer"></i> Web'),
        (directTypesEnum.SOCIAL.value, '<i class="fas fa-thumbs-up"></i> Social'),
        (directTypesEnum.WEB_CALCULATOR.value, '<i class="fas fa-calculator"></i> Calculator'),
        (directTypesEnum.PARTNER.value, '<i class="fas fa-handshake"></i> Partner'),
        (directTypesEnum.BROKER.value, '<i class="fas fa-user-tie"></i> Broker'),
        (directTypesEnum.ADVISER.value, '<i class="fas fa-comments"></i> Adviser'),
        (directTypesEnum.OTHER.value,'<i class="fas fa-question"></i> Other'),
    )


    closeReasons=(
        (closeReasonEnum.DUPLICATE.value, 'Duplicate'),
        (closeReasonEnum.AGE_RESTRICTION.value, 'Age Restriction'),
        (closeReasonEnum.POSTCODE_RESTRICTION.value, 'Postcode Restriction'),
        (closeReasonEnum.MINIMUM_LOAN_AMOUNT.value, 'Below minimum loan amount'),
        (closeReasonEnum.MORTGAGE.value, 'Refinance too Large'),
        (closeReasonEnum.SHORT_TERM.value, 'Short-term / Bridging Requirement'),
        (closeReasonEnum.TENANTS.value, 'Tenants in common'),
        (closeReasonEnum.UNSUITABLE_PROPERTY.value, 'Unsuitable Property'),
        (closeReasonEnum.UNSUITABLE_PURPOSE.value, 'Unsuitable Purpose'),
        (closeReasonEnum.ALTERNATIVE_SOLUTION.value, 'Client Pursuing Alternative'),
        (closeReasonEnum.COMPETITOR.value, 'Client went to Competitor'),
        (closeReasonEnum.CALL_ONLY.value, 'Call only'),
        (closeReasonEnum.NO_CLIENT_ACTION.value, 'No further action by client'),
        (closeReasonEnum.ANTI_REVERSE_MORTGAGE.value, "Does not like Reverse Mortgages"),
        (closeReasonEnum.CALL_ONLY.value, 'Fees too high'),
        (closeReasonEnum.OTHER.value , 'Other')
    )

    marketingTypes = (
        (marketingTypesEnum.WEB_SEARCH.value, "Web search"),
        (marketingTypesEnum.TV_ADVERT.value, "TV Advert"),
        (marketingTypesEnum.TV_ADVERTORIAL.value, "TV Advertorial"),
        (marketingTypesEnum.RADIO.value, "Radio"),
        (marketingTypesEnum.WORD_OF_MOUTH.value, "Word of mouth"),
        (marketingTypesEnum.COMPETITOR.value, "Competitor"),
        (marketingTypesEnum.DIRECT_MAIL.value, "Direct mail"),
        (marketingTypesEnum.DIRECT_EMAIL.value, "Direct Email"),
        (marketingTypesEnum.FACEBOOK.value, "Facebook"),
        (marketingTypesEnum.LINKEDIN.value, "LinkedIn"),
        (marketingTypesEnum.YOUR_LIFE_CHOICES.value, "Your Life Choices"),
        (marketingTypesEnum.NATIONAL_SENIORS.value, "National Seniors"),
        (marketingTypesEnum.STARTS_AT_60.value, "Starts at 60"),
        (marketingTypesEnum.CARE_ABOUT.value, "Care About"),
        (marketingTypesEnum.BROKER_REFERRAL.value, "Broker Referral"),
        (marketingTypesEnum.BROKER_SPECIALIST.value, "Broker Specialist"),
        (marketingTypesEnum.FINANCIAL_ADVISER.value, "Financial Adviser"),
        (marketingTypesEnum.AGED_CARE_ADVISER.value, "Age Care Adviser"),
        (marketingTypesEnum.OTHER.value, "Other"),
    )


    enquiryStageTypes = (
        (enquiryStagesEnum.GENERAL_INFORMATION.value, "General Information"),
        (enquiryStagesEnum.BROCHURE_SENT.value, "Brochure Sent"),
        (enquiryStagesEnum.SUMMARY_SENT.value, "Customer Summary Sent"),
        (enquiryStagesEnum.DISCOVERY_MEETING.value, "Discovery Meeting"),
        (enquiryStagesEnum.LOAN_INTERVIEW.value, "Loan Interview"),
        (enquiryStagesEnum.LIVE_TRANSFER.value, "Live Transfer"),
        (enquiryStagesEnum.DUPLICATE.value, "Duplicate"),
        (enquiryStagesEnum.FUTURE_CALL.value, "Future Call"),
        (enquiryStagesEnum.MORE_TIME_TO_THINK.value, "More time to think"),
        (enquiryStagesEnum.DID_NOT_QUALIFY.value, "Did not Qualify"),
        (enquiryStagesEnum.NOT_PROCEEDING.value, "Not Proceeding"),
        (enquiryStagesEnum.FOLLOW_UP_NO_ANSWER.value, "Follow-up: No Answer"),
        (enquiryStagesEnum.FOLLOW_UP_VOICEMAIL.value,"Follow-up: Voicemail"),
        (enquiryStagesEnum.INITIAL_NO_ANSWER.value, "Initial: No Answer"),
        (enquiryStagesEnum.NVN_EMAIL_SENT.value, "NVN: Email Sent"),

    )

    stateTypes=(
        (stateTypesEnum.NSW.value, "NSW"),
        (stateTypesEnum.VIC.value, "VIC"),
        (stateTypesEnum.ACT.value, "ACT"),
        (stateTypesEnum.QLD.value, "QLD"),
        (stateTypesEnum.SA.value, "SA"),
        (stateTypesEnum.WA.value, "WA"),
        (stateTypesEnum.TAS.value, "TAS"),
        (stateTypesEnum.NT.value, "NT"),
    )


    # Identifiers
    enqUID = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    referrer=models.IntegerField(blank=False,null=False,choices=referrerTypes)
    referrerID=models.CharField(max_length=200,blank= True,null=True)
    referralUser=models.ForeignKey(settings.AUTH_USER_MODEL, related_name='referralUser', null=True, blank=True, on_delete=models.SET_NULL)
    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    sfEnqID = models.CharField(max_length=20, null=True, blank=True)
    marketingSource = models.IntegerField(blank=True, null=True, choices=marketingTypes )
    submissionOrigin = models.CharField(max_length=200, blank=True, null=True)

    # Client Data
    email=models.EmailField(blank=True, null=True)
    phoneNumber = models.CharField(max_length=15, blank=True, null=True)
    enquiryNotes = models.TextField(null=True, blank=True)

    # Enquiry Inputs
    productType = models.IntegerField(choices=productTypes, null=True, blank=True, default=0)
    loanType = models.IntegerField(choices=loanTypes, null=True, blank=True)
    name = models.CharField(max_length=121, blank=True, null=True) # 40 chars firstname, 80 chars surname plus ' '
    age_1=models.IntegerField(blank=True, null=True)
    age_2 = models.IntegerField(blank=True, null=True)
    dwellingType=models.IntegerField(blank=True, null=True, choices=dwellingTypes)

    # ~ Property Data
    streetAddress = models.CharField(max_length=80, blank=True, null=True)
    suburb = models.CharField(max_length=40, blank=True, null=True)
    state = models.IntegerField(choices=stateTypes, null=True, blank=True)
    postcode=models.IntegerField(blank=True, null=True)
    valuation=models.IntegerField(blank=True, null=True)
    isReferPostcode = models.BooleanField(blank=True, null=True)
    referPostcodeStatus = models.BooleanField(blank=True, null=True)
    mortgageDebt = models.IntegerField(null=True, blank=True)
    mortgageRepayment = models.IntegerField(blank=True, null=True)
    valuationDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='enquiryReports')

    # ~ Purpose Data
    isRefi=models.BooleanField(default=False, blank=True, null=True)
    isTopUp=models.BooleanField(default=False, blank=True, null=True)
    isLive=models.BooleanField(default=False, blank=True, null=True)
    isGive=models.BooleanField(default=False, blank=True, null=True)
    isCare = models.BooleanField(default=False, blank=True, null=True)
    calcLumpSum = models.IntegerField(blank=True, null=True)
    calcIncome = models.IntegerField(blank=True, null=True)

    #Calculated Data
    status = models.BooleanField(default=True, blank=False, null=False)
    maxLoanAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownMonthly = models.IntegerField(blank=True, null=True)
    maxLVR = models.FloatField(blank=True, null=True)
    errorText = models.CharField(max_length=40, blank=True, null=True)
    summaryDocument = models.FileField(null=True, blank=True, upload_to='enquiryReports')

    #Workflow
    actioned=models.IntegerField(default=0,blank=True, null=True)
    isCalendly=models.BooleanField(default=False, blank=True, null=True)
    followUp = models.DateTimeField(null=True, blank=True, auto_now_add=False, auto_now=False)
    secondfollowUp = models.DateTimeField(null=True, blank=True, auto_now_add=False, auto_now=False)
    closeDate = models.DateField(blank=True, null=True)
    closeReason=models.IntegerField(blank=True, null=True, choices=closeReasons)
    followUpDate=models.DateField(blank=True, null=True)
    followUpNotes = models.TextField(blank=True, null=True)
    doNotMarket = models.BooleanField(default=False) # TODO: REMOVE THIS FIELD AFTER this value has been propagated to CASE after new data models are taken into effect
    enquiryStage = models.IntegerField(blank=True, null=True, choices=enquiryStageTypes)
    requestedCallback = models.BooleanField(default=False, blank=False, null=False)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    calcTotal=models.IntegerField(blank=True, null=True) # deprecated
    calcTopUp=models.IntegerField( blank=True, null=True) # deprecated
    calcRefi=models.IntegerField(blank=True, null=True)  # deprecated
    calcLive=models.IntegerField( blank=True, null=True)  # deprecated
    calcGive=models.IntegerField(blank=True, null=True)  # deprecated
    calcCare = models.IntegerField( blank=True, null=True)  # deprecated
    calcDrawdown = models.IntegerField(blank=True, null=True)  # deprecated
    payIntAmount=models.IntegerField(blank=True, null=True)  # deprecated
    payIntPeriod = models.IntegerField(blank=True, null=True)  # deprecated
    lossNotes=models.TextField(blank=True, null=True)  # deprecated

    # Scoring
    propensityCategory = models.IntegerField(choices=propensityChoices, blank=True, null=True)
    
    marketing_campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.SET_NULL)
    
    objects = EnquiryManager()


    case = models.ForeignKey(
        'case.Case',
        related_name='enquiries',
        blank=True, 
        null=True,  # Forward migration to fix some of these: Loosely constraining this to allow selective migration 
        on_delete=models.CASCADE 
    )

    @property
    def get_absolute_url(self):
        return reverse_lazy("enquiry:enquiryDetail", kwargs={"uid":self.enqUID})

    def get_SF_url(self):
        if self.sfEnqID: 
            return urljoin(
                os.getenv('SALESFORCE_BASE_URL'),
                "lightning/r/Enquiry__c/{0}/view".format(self.sfEnqID)
            )
        if self.sfLeadID:
            return urljoin(
                os.getenv('SALESFORCE_BASE_URL'),
                "lightning/r/Lead/{0}/view".format(self.sfLeadID)
            )


    def enumReferrerType(self):
        if self.referrer is not None:
            return dict(self.referrerTypes)[self.referrer]

    def enumReferrerTypeHTML(self): 
        if self.referrer is not None: 
            return dict(self.refferTypesHTML)[self.referrer]
        return 'N/A'

    def enumLoanType(self):
        if self.loanType is not None:
            return dict(self.loanTypes)[self.loanType]

    def referralCompany(self):
        if self.referralUser is not None:
            return self.referralUser.profile.referrer

    def enumDwellingType(self):
        if self.dwellingType is not None:
            return dict(self.dwellingTypes)[self.dwellingType]

    def enumCloseReason(self):
        if self.closeReason is not None:
            return dict(self.closeReasons)[self.closeReason]

    def enumMarketingSource(self):
        if self.marketingSource is not None:
            return dict(self.marketingTypes)[self.marketingSource]

    def enumEnquiryStage(self):
        if self.enquiryStage is not None:
            return dict(self.enquiryStageTypes)[self.enquiryStage]

    def enumPropensityCategory(self):
        if self.propensityCategory is not None:
            return dict(propensityChoices)[self.propensityCategory]

    def has_duplicate(self):
        if self.email and (Enquiry.objects.filter(email=self.email).count() > 1):
            return True
        if self.phoneNumber and (Enquiry.objects.filter(phoneNumber=self.phoneNumber).count() > 1):
            return True

        return False

    def __str__(self):
        return smart_text(self.email)
    
    def save(self, should_sync=False, *args, **kwargs):

        is_create = self.pk is None
         
        if is_create: 
            # attempt sync on create
            should_sync = bool(
                (self.email or self.phoneNumber)  and  
                self.user and 
                self.postcode
            )
        
        super(Enquiry, self).save(*args, **kwargs)
        self.refresh_from_db()
        # Case Wasnt passed in save kwarg / Or doesnt exist
        if not self.case_id: 
            existing_case = get_existing_case(self.phoneNumber, self.email)
            if existing_case is not None: 
                existing_case.enquiries.add(self)
            else: 
                create_case_from_enquiry(self)
                should_sync = False 
                # no need to re-trigger sync as current job already takes care of it.

        if should_sync:
            # if this is a should_sync which comes from user assignment
            if self.user and self.case.owner is None: 
                case = self.case 
                case.owner = self.user 
                case.save()
                # if user didnt exist then sync never passed 
                app.send_task('sfEnquiryLeadSync', kwargs={'enqUID': str(self.enqUID)})
            else:
                app.send_task('Update_SF_Enquiry', kwargs={'enqUID': str(self.enqUID)})
    class Meta:
        ordering = ('-updated',)
