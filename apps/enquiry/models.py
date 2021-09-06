#Python Imports
import uuid, os, reversion
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db import models
from django.db.models.functions import TruncDate, TruncDay, Cast
from django.db.models import Count
from django.db.models.fields import DateField
from django.utils.timezone import get_current_timezone
from django.utils.encoding import smart_text
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.postgres.fields import JSONField

from apps.helpers.model_utils import ReversionModel
from apps.lib.site_Utilities import join_name, validate_loan
from apps.lib.hhc_LoanValidator import LoanValidator


from urllib.parse import urljoin
#Local Imports
from apps.lib.site_Enums import *
from apps.case.model_utils import get_existing_case, create_case_from_enquiry, update_case_from_enquiry
from config.celery import app
from apps.base.model_utils import AbstractAddressModel
from apps.enquiry.note_utils import add_enquiry_note
from django_comments.models import Comment


class EnquiryManager(models.Manager):

    #Custom model manager to return related queryset and dictionary (using UID)
    def queryset_byUID(self,uidString):
        searchWeb = Enquiry.objects.get(enqUID=uuid.UUID(uidString)).pk
        return super(EnquiryManager, self).filter(pk=searchWeb)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

    # Custom data queries
    def queueCount(self):
        return Enquiry.objects.filter(deleted_on__isnull=True, user__isnull=True,actioned=0).count()

    def openEnquiries(self):
        return Enquiry.objects.filter(deleted_on__isnull=True, actioned=0, followUp__isnull=True).exclude(status=False,user__isnull=False)

    def __timeSeriesQry(self, qs, length):
        #utility function appended to base time series query
        tz = get_current_timezone()
        qryDate=datetime.now(tz)-timedelta(days=length)

        return qs.filter(timestamp__gte=qryDate).annotate(date=Cast(TruncDay('timestamp', tzinfo=tz), DateField())) \
                   .values_list('date') \
                   .annotate(interactions=Count('enqUID',distinct=True)) \
                   .values_list('date', 'interactions').order_by('-date')

    def timeSeries(self, seriesType, length, search=None):

        result = self.__timeSeriesQry(Enquiry.objects.filter(referrer=seriesType, deleted_on__isnull=True), length)

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
        query = Q(deleted_on__isnull=True) & query
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
        (directTypesEnum.WEB_PREQUAL.value, 'Pre Qualification'),
        (directTypesEnum.SEARCH.value, 'Search'),
        (directTypesEnum.WEB_VISA.value, 'VISA Enquiry'),
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
        (directTypesEnum.WEB_PREQUAL.value, '<i class="fas fa-user-check"></i> Pre Qualification'),
        (directTypesEnum.SEARCH.value, '<i class="fas fa-search"></i> Search'),
        (directTypesEnum.WEB_VISA.value, '<i class="fab fa-cc-visa"></i> VISA Enquiry'),
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
        (marketingTypesEnum.FACEBOOK_INTERACTIVE.value, "Facebook Interactive"),
        (marketingTypesEnum.FACEBOOK_CALCULATOR.value, "Facebook Calculator"),
        (marketingTypesEnum.LINKEDIN.value, "LinkedIn"),
        (marketingTypesEnum.GOOGLE_MOBILE.value, "Google Ads Mobile"),
        (marketingTypesEnum.YOUR_LIFE_CHOICES.value, "Your Life Choices"),
        (marketingTypesEnum.NATIONAL_SENIORS.value, "National Seniors"),
        (marketingTypesEnum.STARTS_AT_60.value, "Starts at 60"),
        (marketingTypesEnum.CARE_ABOUT.value, "Care About"),
        (marketingTypesEnum.BROKER_REFERRAL.value, "Broker Referral"),
        (marketingTypesEnum.BROKER_SPECIALIST.value, "Broker Specialist"),
        (marketingTypesEnum.FINANCIAL_ADVISER.value, "Financial Adviser"),
        (marketingTypesEnum.AGED_CARE_ADVISER.value, "Age Care Adviser"),

        (marketingTypesEnum.CARE_ABOUT_CALC_LP.value, "Care About - Calculator LP"),
        (marketingTypesEnum.STARTS_AT_60_CALC_LP.value, "Starts at 60 - Calculator LP"),
        (marketingTypesEnum.YOUR_LIFE_CHOICES_CALC_LP.value, "Your Life Choices - Calculator LP"),

        (marketingTypesEnum.FACEBOOK_VISA.value, "Facebook Visa"),

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
        (enquiryStagesEnum.WAIT_LIST.value, "Wait List"),

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

    FeeProductTypes = (
        ("HHC.RM.2018", "HHC.RM.2018"),
        ("HHC.RM.2021", "HHC.RM.2021")
    )


    # Identifiers
    enqUID = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    sfEnqID = models.CharField(max_length=20, null=True, blank=True)


    product_type = models.CharField(null=True, blank=True, max_length=11, choices=FeeProductTypes)
    
    # Origin
    # Person:
    referrerID = models.CharField(max_length=200,blank= True,null=True)
    referralUser = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='referralUser', null=True, blank=True, on_delete=models.SET_NULL)
    # Not a person:
    referrer = models.IntegerField(blank=False,null=False,choices=referrerTypes)  # "Lead Source" - not a person!
    marketingSource = models.IntegerField(blank=True, null=True, choices=marketingTypes)
    submissionOrigin = models.CharField(max_length=800, blank=True, null=True)
    origin_timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=False, auto_now=False)
    origin_id = models.CharField(max_length=36, null=True, blank=True)

    # Client Data
    email=models.EmailField(blank=True, null=True)
    phoneNumber = models.CharField(max_length=15, blank=True, null=True)
    # Deprecated field - just used for form collection now (phone enquiry) before being passed on to the real notes system
    enquiryNotes = models.TextField(null=True, blank=True) # deprecated

    # Enquiry Inputs
    productType = models.IntegerField(choices=productTypes, null=True, blank=True, default=0)
    loanType = models.IntegerField(choices=loanTypes, null=True, blank=True)
    DEPRECATED_name = models.CharField(max_length=121, blank=True, null=True) # 40 chars firstname, 80 chars surname plus ' '
    firstname = models.CharField(max_length=40, blank=True, null=True)
    lastname = models.CharField(max_length=80, blank=True, null=True)

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
    errorText = models.CharField(max_length=200, blank=True, null=True)
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
    # THIS IS ACTUALLY A LEAD LEVEL FIELD, WE HAVE THIS HERE PURELY TO HELP CAPTURE IT FROM THE
    # PHONE ENQUIRY FORM AND PASS THROUGH TO THE LEAD IN OUR SAVE BELOW.
    propensityCategory = models.IntegerField(choices=propensityChoices, blank=True, null=True)
    
    marketing_campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.SET_NULL)
    
    head_doc = JSONField(default=dict)

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

    def has_duplicate(self):
        if self.email and (Enquiry.objects.filter(email=self.email, deleted_on__isnull=True).count() > 1):
            return True
        if self.phoneNumber and (Enquiry.objects.filter(phoneNumber=self.phoneNumber, deleted_on__isnull=True).count() > 1):
            return True

        return False

    @property
    def has_notes(self):
        return Comment.objects.for_model(self).exists()

    @property
    def name(self):
        return join_name(self.firstname, None, self.lastname)

    def __str__(self):
        return smart_text(self.email)
    
    def save(self, should_sync=False, ignore_case_creation=False, *args, **kwargs):

        is_create = self.pk is None
        lead_obj_created = False
        if is_create:
            # attempt sync on create
            should_sync = bool(
                (self.email or self.phoneNumber)  and  
                self.user and 
                self.postcode
            )

        if is_create and self.propensityCategory is None:
            if self.referrer == directTypesEnum.PHONE.value:
                self.propensityCategory = propensityCategoriesEnum.D.value

            elif self.referrer == directTypesEnum.WEB_ENQUIRY.value:
                self.propensityCategory = propensityCategoriesEnum.D.value

            elif self.referrer == directTypesEnum.WEB_CALCULATOR.value:
                self.propensityCategory = propensityCategoriesEnum.D.value

        my_dict = self.__dict__

        if not self.product_type:
            self.product_type = "HHC.RM.2021"
        
        validation_result = validate_loan(my_dict, self.product_type)

        if validation_result['status'] == "Error":
            self.status = 0
            self.errorText = validation_result['responseText']
            self.maxLoanAmount = None
            self.maxLVR = None
            self.maxDrawdownAmount = None
            self.maxDrawdownMonthly = None
        else:
            self.status = 1
            self.errorText = None
            self.maxLoanAmount = validation_result['data']['maxLoan']
            self.maxLVR = validation_result['data']['maxLVR']
            self.maxDrawdownAmount = validation_result['data']['maxDrawdown']
            self.maxDrawdownMonthly = validation_result['data']['maxDrawdownMonthly']
        
        super(Enquiry, self).save(*args, **kwargs)
        self.refresh_from_db()

        if is_create and self.enquiryNotes:
            note_user = self.user if (self.referrer == directTypesEnum.PHONE.value) else None
            add_enquiry_note(self, self.enquiryNotes, user=note_user)

        # Case Wasnt passed in save kwarg / Or doesnt exist
        if not self.case_id: 
            existing_case = get_existing_case(self.phoneNumber, self.email)
            if existing_case is not None: 
                existing_case.enquiries.add(self)
                if is_create and self.referrer in RESET_DO_NOT_MARKET:
                    existing_case.doNotMarket = False
                    existing_case.save(should_sync=True)
                if existing_case.caseStage == caseStagesEnum.CLOSED.value: 
                    existing_case.caseStage = caseStagesEnum.UNQUALIFIED_CREATED.value
                    existing_case.save()#should_sync=True)
            else:
                if not ignore_case_creation: # Special kwarg to prevent case creation [During Migration]
                    create_case_from_enquiry(self)
                    should_sync = False 
                    lead_obj_created = True
                # no need to re-trigger sync as current job already takes care of it.

        if not lead_obj_created and is_create:
            # only update if this a new enquiry being attached.
            update_case_from_enquiry(self, self.case)

        if should_sync:
            # if this is a should_sync which comes from user assignment
            if not self.case.sfLeadID: 
                # if user didnt exist then sync never passed 
                app.send_task('sfEnquiryLeadSync', kwargs={'enqUID': str(self.enqUID)})
            else:
                app.send_task('Update_SF_Enquiry', kwargs={'enqUID': str(self.enqUID)})

    
    class Meta:
        ordering = ('-updated',)
