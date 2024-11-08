#Python imports
import uuid, os, reversion, pytz
from datetime import datetime, timedelta

#Django Imports
from django.conf import settings
from django.db.models.signals import post_save
from django.db import models
from django.db.models import Q
from django.utils.encoding import smart_text
from django.utils import timezone
from django.urls import reverse_lazy
from django_comments.models import Comment
from django.contrib.postgres.fields import JSONField

#Local Application Imports
from apps.lib.site_Enums import *
from apps.lib.site_Utilities import calc_age, get_default_product_now, validate_loan

from apps.accounts.models import Referer
from urllib.parse import urljoin

from apps.base.model_utils import AbstractAddressModel
from apps.helpers.model_utils import ReversionModel

from config.celery import app
from apps.case.note_utils import add_case_note


class FundDetail(models.Model):
    #Model for Fund Names/Images
    fundID=models.AutoField(primary_key=True)
    fundName=models.CharField(max_length=30,blank=False, null=False)
    fundImage = models.ImageField(null=False, blank=False, upload_to='fundImages')

    def __str__(self):
        return smart_text(self.fundName)

    def __unicode__(self):
        return smart_text(self.fundName)

    class Meta:
        ordering = ('fundName',)
        verbose_name_plural = "Superfund Definitions"


class CaseManager(models.Manager):

    #Custom model manager to return related querysets (using UID)
    def queryset_byUID(self,uidString):
       if self.model.__name__=='Case':
            searchCase=Case.objects.get(caseUID=uuid.UUID(uidString)).caseID
            return super(CaseManager,self).filter(caseID=searchCase)
       else:
           searchCase = Case.objects.get(caseUID=uuid.UUID(uidString))
           return super(CaseManager, self).filter(case=searchCase)

    def dictionary_byUID(self,uidString):
        return self.queryset_byUID(uidString).values()[0]

    # Custom data queries
    def openCases(self):
        closedTypes = [caseStagesEnum.CLOSED.value, caseStagesEnum.FUNDED.value]
        return Case.objects.exclude(caseStage__in=closedTypes)

    def queueCount(self):
        return Case.objects.filter(owner__isnull=True, deleted_on__isnull=True).count()


    def find_duplicates_QS(self, email, phoneNumber):
        if email and phoneNumber:
            query = (Q(email_1__iexact=email) | Q(phoneNumber_1=phoneNumber))
        elif email:
            query = Q(email_1__iexact=email)
        elif phoneNumber:
            query = Q(phoneNumber_1=phoneNumber)
        else:
            raise Exception('email or phone must be present')
        query = Q(deleted_on__isnull=True) & (query)
        return Case.objects.filter(query)

    def find_duplicates(self, email, phoneNumber, order_by="-updated"):
        return self.find_duplicates_QS(email, phoneNumber).order_by(order_by)

@reversion.register()
class Case(AbstractAddressModel, ReversionModel, models.Model):
    # Main model - extended by Loan, ModelSettings and LossData

    class Meta:
        ordering = ('-updated',)
        verbose_name_plural = "Case"
        # TODO RE-ADd this to make it work with multiple properties (N cases for 1 customer)
        # constraints = [
        #     # Ensures constraint on DB level, raises IntegrityError (500 on debug=False)
        #     models.UniqueConstraint(
        #         fields=[
        #             'phoneNumber_1', 
        #             'email_1'
        #         ], 
        #         condition=Q(
        #             Q(appType=appTypesEnum.NEW_APPLICATION.value) &
        #             Q(deleted_on__isnull=True)
        #         ),
        #         name='email_phone_lead_definition_uniqueness'
        #     ),
        # ]
    

    appTypes = (
        (appTypesEnum.NEW_APPLICATION.value, "Application"),
        (appTypesEnum.VARIATION.value, "Variation"),
    )

    referrerTypes = (
        (-1, 'Unassigned'),
        (directTypesEnum.PHONE.value,'Phone'),
        (directTypesEnum.EMAIL.value, 'Email'),
        (directTypesEnum.WEB_ENQUIRY.value,'Web'),
        (directTypesEnum.SOCIAL.value, 'Social'),
        (directTypesEnum.WEB_CALCULATOR.value, 'Calculator'),
        (directTypesEnum.PARTNER.value, 'Partner'),
        (directTypesEnum.BROKER.value, 'Broker'),
        (directTypesEnum.ADVISER.value, 'Adviser'),
        (directTypesEnum.WEB_PREQUAL.value, 'Pre Qualification'),
        (directTypesEnum.WEB_VISA.value, 'Visa Enquiry'),
        (directTypesEnum.SEARCH.value, 'Search'),
        (directTypesEnum.OTHER.value,'Other'),
    )

    caseStages=(
                  (caseStagesEnum.UNQUALIFIED_CREATED.value,"Unqualified / Lead created"),
                  (caseStagesEnum.MARKETING_QUALIFIED.value,"Marketing Qualified"),
                  (caseStagesEnum.SQ_GENERAL_INFO.value,"SQ - General Info"),
                  (caseStagesEnum.SQ_BROCHURE_SENT.value,"SQ - Brochure sent"),
                  (caseStagesEnum.SQ_CUSTOMER_SUMMARY_SENT.value,"SQ - Customer summary sent"),
                  (caseStagesEnum.SQ_FUTURE_CALL.value,"SQ - Future call"),

                  (caseStagesEnum.SQ_NO_ANSWER.value, "SQ - No Answer"),
                  (caseStagesEnum.SQ_VOICEMAIL.value, "SQ - Voicemail"),
                  (caseStagesEnum.SQ_EMAIL_SENT.value, "SQ - Email Sent"),
                  (caseStagesEnum.SQ_PRE_QUAL.value, "SQ - Pre Qual"),
                  (caseStagesEnum.MEETING_BOOKED.value, "Meeting Booked"),

                  (caseStagesEnum.DISCOVERY.value,"Discovery"),
                  (caseStagesEnum.WAIT_LIST.value, "Wait List"),
                  (caseStagesEnum.MEETING_HELD.value, "Meeting Held"),
                  (caseStagesEnum.APPLICATION.value, "Application"),
                  (caseStagesEnum.DOCUMENTATION.value, "Documentation"),
                  (caseStagesEnum.FUNDED.value, "Funded"),
                  (caseStagesEnum.CLOSED.value, "Closed"),    
        )

    clientTypes=(
        (clientTypesEnum.BORROWER.value, 'Borrower'),
        (clientTypesEnum.NOMINATED_OCCUPANT.value, 'Nominated Occupant'),
        (clientTypesEnum.PERMITTED_COHABITANT.value, 'Permitted Cohabitant'),
        (clientTypesEnum.POWER_OF_ATTORNEY.value, 'Power of Attorney'),
    )

    clientSex=(
        (clientSexEnum.FEMALE.value, 'Female'),
        (clientSexEnum.MALE.value, 'Male'))

    dwellingTypes=(
        (dwellingTypesEnum.HOUSE.value, 'House'),
        (dwellingTypesEnum.APARTMENT.value, 'Apartment'))

    pensionTypes=(
        (pensionTypesEnum.FULL_PENSION.value, 'Full'),
        (pensionTypesEnum.PARTIAL_PENSION.value, 'Partial'),
        (pensionTypesEnum.NO_PENSION.value, 'None')
    )

    investmentTypes = (
        (investmentTypesEnum.SUPER.value, 'Superannuation'),
        (investmentTypesEnum.SHARES.value, 'Shares / Managed Funds'),
        (investmentTypesEnum.PROPERTY.value, 'Investment Property'),
        (investmentTypesEnum.COMBINED.value, 'Combined Investments'),
    )


    loanTypes=(
        (loanTypesEnum.SINGLE_BORROWER.value,'Single'),
        (loanTypesEnum.JOINT_BORROWER.value,'Joint')
    )

    channelTypes=(
        (channelTypesEnum.DIRECT_ACQUISITION.value, "Direct Acquisition"),
        (channelTypesEnum.PARTNER.value, "Partner"),
        (channelTypesEnum.BROKER.value, "Broker"),
        (channelTypesEnum.ADVISER.value, "Adviser")
    )

    channelDetailTypes=(
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
        (marketingTypesEnum.VISA.value, "VISA"),

        (marketingTypesEnum.MENTOR1_CALC_LP.value, "Mentor1 - Calculator LP"),
        (marketingTypesEnum.MONEYGPS_CALC_LP.value, "MoneyGPS - Calculator LP"),
        
        (marketingTypesEnum.OTHER.value, "Other"),
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

    salutationTypes=(
        (salutationEnum.MR.value,"Mr."),
        (salutationEnum.MS.value, "Ms."),
        (salutationEnum.MRS.value, "Mrs."),
        (salutationEnum.DR.value, "Dr."),
        (salutationEnum.PROF.value, "Prof."),
    )

    maritalTypes=(
        (maritalEnum.SINGLE.value, "Single"),
        (maritalEnum.MARRIED.value, "Married"),
        (maritalEnum.DIVORCED.value, "Divorced"),
        (maritalEnum.WIDOWED.value, "Widowed"),
        (maritalEnum.DEFACTO.value, "De Facto"),
        (maritalEnum.SEPARATED.value, "Separated"),
    )

    productTypes = (
        (productTypesEnum.LUMP_SUM.value, "Lump Sum"),
        (productTypesEnum.INCOME.value, "Income"),
        (productTypesEnum.COMBINATION.value, "Combination"),
        (productTypesEnum.CONTINGENCY_20K.value, "Contingency 20K"),
        (productTypesEnum.REFINANCE.value, "Refinance"),
    )

    loanRating = (
        (loanRatingEnum.SIMPLE.value, 'Simple'),
        (loanRatingEnum.MODERATE.value, 'Moderate'),
        (loanRatingEnum.COMPLEX.value, 'Complex'),
    ) 

    # ClientApp Identifiers
    caseID = models.AutoField(primary_key=True)
    caseUID = models.UUIDField(default=uuid.uuid4, editable=False)
    # - Variation References
    refCaseUID = models.UUIDField(null=True, blank=True)
    refFacilityUID  = models.UUIDField(null=True, blank=True)
    # - Application References
    appUID = models.UUIDField(null=True, blank=True)

    # Case Summary Data
    caseStage = models.IntegerField(choices=caseStages)
    appType = models.IntegerField(default = 0, choices = appTypes)
    productType = models.IntegerField(choices=productTypes, null=True, blank=True, default=0)
    caseDescription = models.CharField(max_length=90, null=False, blank=False) # Surname + postcode
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    # Customer Data
    caseNotes = models.TextField(blank=True, null=True) # Deprecated
    loanType = models.IntegerField(choices=loanTypes,null=True, blank=True)

    #- Borrower 1
    clientType1 = models.IntegerField(choices=clientTypes,null=True, blank=True)
    salutation_1 = models.IntegerField(choices=salutationTypes,null=True, blank=True)
    middlename_1 = models.CharField(max_length=40, null=True, blank=True)
    maritalStatus_1 = models.IntegerField(choices=maritalTypes,null=True, blank=True)
    surname_1 = models.CharField(max_length=80, null=True, blank=True)
    firstname_1 = models.CharField(max_length=40, null=True, blank=True)
    preferredName_1 = models.CharField(max_length=40, null=True, blank=True)
    birthdate_1 = models.DateField(null=True, blank=True)
    age_1 = models.IntegerField(null=True, blank=True)
    sex_1 = models.IntegerField(choices=clientSex,null=True, blank=True)
    phoneNumber_1 = models.CharField(max_length=20, null=True, blank=True)
    email_1 = models.EmailField(null=True, blank=True)

    distribution_contact_email = models.EmailField(null=True, blank=True)

    #- Borrower 2
    clientType2 = models.IntegerField(choices=clientTypes, null=True, blank=True)
    salutation_2 = models.IntegerField(choices=salutationTypes,null=True, blank=True)
    middlename_2 = models.CharField(max_length=40, null=True, blank=True)
    maritalStatus_2 = models.IntegerField(choices=maritalTypes,null=True, blank=True)
    surname_2 = models.CharField(max_length=80, null=True, blank=True)
    firstname_2 = models.CharField(max_length=40, null=True, blank=True)
    preferredName_2 = models.CharField(max_length=40, null=True, blank=True)
    birthdate_2 = models.DateField(null=True, blank=True)
    age_2 = models.IntegerField(null=True, blank=True)
    sex_2 = models.IntegerField(choices=clientSex,null=True, blank=True)

    #- Additional Data
    superFund = models.ForeignKey(FundDetail,null=True, blank=True, on_delete=models.SET_NULL)
    superAmount = models.IntegerField(null=True, blank=True)
    investmentLabel = models.IntegerField(choices=investmentTypes,default=0)
    pensionType = models.IntegerField(choices=pensionTypes,default=2) # deprecated
    pensionAmount = models.IntegerField(default=0)
    mortgageDebt = models.IntegerField(null=True, blank=True)

    # Property Data
    street = models.CharField(max_length=80, null=True, blank=True)
    suburb = models.CharField(max_length=30, null=True, blank=True)
    postcode = models.IntegerField(null=True, blank=True)
    state = models.IntegerField(choices=stateTypes, null=True, blank=True)
    valuation = models.IntegerField(null=True, blank=True)
    dwellingType = models.IntegerField(choices=dwellingTypes, null=True, blank=True)
    propertyImage = models.ImageField(null=True, blank=True, upload_to='customerImages')
    isReferPostcode = models.BooleanField(blank=True, null=True)
    referPostcodeStatus = models.BooleanField(blank=True, null=True)

    # Customer Document Data
    meetingDate = models.DateTimeField(blank=True, null=True)
    isZoomMeeting = models.BooleanField(default=False, null=True, blank=True)
    summaryDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerReports')
    summarySentDate = models.DateTimeField(blank=True, null=True)
    summarySentRef = models.CharField(max_length=30, null=True, blank=True)
    responsibleDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerReports')
    enquiryDocument = models.FileField(max_length=150,null=True, blank=True) # deprecated
    valuationDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments')
    titleDocument = models.FileField(max_length=150,null=True, blank=True, upload_to='customerDocuments') # deprecated
    titleRequest = models.BooleanField(null=True, blank=True)
    lixiFile= models.FileField(max_length=150, null=True, blank=True)
    applicationDocument = models.FileField(max_length=150, null=True, blank=True, upload_to='customerReports')
    preQualDocument = models.FileField(max_length=150,null=True, blank=True)
    # Referral / Channel Data
    salesChannel = models.IntegerField(choices=channelTypes,null=True, blank=True)
    channelDetail = models.IntegerField(choices=channelDetailTypes, null=True, blank=True)
    marketing_campaign = models.ForeignKey('enquiry.MarketingCampaign', null=True, blank=True, on_delete=models.SET_NULL)
    adviser = models.CharField(max_length=60, null=True, blank=True)
    referralCompany = models.ForeignKey(Referer ,null=True, blank=True, on_delete=models.SET_NULL)
    referralRepNo = models.CharField(max_length=60, null=True, blank=True)

    #Third Party Identifiers / Workflow
    sfLeadID = models.CharField(max_length=20, null=True, blank=True)
    sfOpportunityID = models.CharField(max_length=20, null=True, blank=True)
    sfLoanID = models.CharField(max_length=20, null=True, blank=True)
    amalIdentifier = models.CharField(max_length=40, null=True, blank=True)
    amalLoanID = models.CharField(max_length=40, null=True, blank=True)

    enquiryCreateDate = models.DateTimeField(null=True, blank=True)
    enqUID = models.UUIDField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    # Scoring
    propensityCategory = models.IntegerField(choices=propensityChoices, blank=True, null=True)

    
    doNotMarket = models.BooleanField(default=False)

    # eligibility
    is_eligible = models.BooleanField(default=True, blank=False, null=False)
    ineligible_reason = models.CharField(max_length=200, blank=True, null=True)
    maxLoanAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownAmount = models.IntegerField(blank=True, null=True)
    maxDrawdownMonthly = models.IntegerField(blank=True, null=True)
    maxLVR = models.FloatField(blank=True, null=True)


    # new fields to move from lead
    referrer = models.IntegerField(blank=False, null=False, choices=referrerTypes, default=-1)
    # default to unassigned to allow migration and not break the null/blank = False
    followUp = models.DateTimeField(auto_now_add=False, auto_now=False, blank=True, null=True)
    
    touched_in_sf_sync = models.BooleanField(default=False, blank=True, null=True)

    # for generating enquriies 
    calcLumpSum = models.IntegerField(blank=True, null=True)
    calcIncome = models.IntegerField(blank=True, null=True)

    lead_needs_action = models.BooleanField(default=False, blank=True, null=True)
    # True if Action btn shows
    loan_rating = models.IntegerField(blank=True, null=True, choices=loanRating)
    
    head_doc = JSONField(default=dict)

    objects=CaseManager()

    def __str__(self):
        return smart_text(self.caseDescription)

    def __unicode__(self):
        return smart_text(self.caseDescription)

    def enumReferrerType(self):
        if self.referrer is not None:
            return dict(self.referrerTypes)[self.referrer]

    def enumCaseStage(self):
        return dict(self.caseStages).get(self.caseStage)

    def enumLoanType(self):
        if self.loanType is not None:
            return dict(self.loanTypes).get(self.loanType)
    
    def enumLoanRating(self):
        return dict(self.loanRating).get(self.loan_rating)

    def enumStateType(self):
        if self.state is not None:
            return dict(self.stateTypes).get(self.state)

    def enumDwellingType(self):
        return dict(self.dwellingTypes).get(self.dwellingType)

    def enumProductType(self):
        return dict(self.productTypes).get(self.productType)

    def enumSex(self):
        if self.clientType2 == None:
            return [dict(self.clientSex)[self.sex_1],None]
        else:
            return [dict(self.clientSex)[self.sex_1],dict(self.clientSex)[self.sex_2]]

    def enumClientType(self):
        if self.clientType2 == None:
            return [dict(self.clientTypes).get(self.clientType1),None]
        else:
            return [dict(self.clientTypes).get(self.clientType1),dict(self.clientTypes).get(self.clientType2)]

    def enumChannelType(self):
        if self.salesChannel is not None:
            return dict(self.channelTypes)[self.salesChannel]

    def enumChannelDetailType(self):
        if self.channelDetail is not None:
            return dict(self.channelDetailTypes)[self.channelDetail]

    def enumPensionType(self):
        if self.pensionType is not None:
            return dict(self.pensionTypes)[self.pensionType]

    def enumInvestmentLabel(self):
            return dict(self.investmentTypes)[self.investmentLabel]

    def enumMaritalStatus(self):
        if self.clientType2 == None:
            return [dict(self.maritalTypes)[self.maritalStatus_1],None]
        else:
            return [dict(self.maritalTypes)[self.maritalStatus_1],dict(self.maritalTypes)[self.maritalStatus_2]]

    def enumSalutation(self):
        if self.clientType2 == None:
            return [dict(self.salutationTypes).get(self.salutation_1),None]
        else:
            return [dict(self.salutationTypes).get(self.salutation_1),dict(self.salutationTypes).get(self.salutation_2)]

    def enumReferPostcodeStatus(self):
        if self.referPostcodeStatus != None:
            if self.referPostcodeStatus:
                return 'Approved'
            else:
                return 'Rejected'

    def enumPropensityCategory(self):
        if self.propensityCategory is not None:
            return dict(propensityChoices)[self.propensityCategory]

    def get_absolute_url(self):
        return reverse_lazy("case:caseDetail", kwargs={"uid": self.caseUID})

    def get_referrer_url(self):
        return reverse_lazy("referrer:caseDetail", kwargs={"uid": self.caseUID})

    def get_SF_url(self):
        if self.sfOpportunityID:
            return urljoin(
                os.getenv('SALESFORCE_BASE_URL'),
                "lightning/r/Opportunity/{0}/view".format(self.sfOpportunityID)
            )
        if self.sfLeadID:
            return urljoin(
                os.getenv('SALESFORCE_BASE_URL'),
                "lightning/r/Lead/{0}/view".format(self.sfLeadID)
            )

    @property
    def notes_summary(self):
        summary = ''
        for comment in Comment.objects.for_model(self):
            summary += '\r\n' + comment.comment
        return summary

    @property
    def email(self):
        return self.email_1

    @property
    def phoneNumber(self):
        return self.phoneNumber_1
    
    def save(self, should_sync=False, *args, **kwargs):
        is_create = self.pk is None
        if is_create: 
            product_type = "HHC.RM.2021"
        else: 
            product_type = self.loan.product_type
        my_dict = self.__dict__
        validation_result = validate_loan(my_dict, product_type)

        if validation_result['status'] == "Error":
            self.is_eligible = 0
            self.ineligible_reason = validation_result['responseText']
            self.maxLoanAmount = None
            self.maxLVR = None
            self.maxDrawdownAmount = None
            self.maxDrawdownMonthly = None
        else:
            self.is_eligible = 1
            self.ineligible_reason = None
            self.maxLoanAmount = validation_result['data']['maxLoan']
            self.maxLVR = validation_result['data']['maxLVR']
            self.maxDrawdownAmount = validation_result['data']['maxDrawdown']
            self.maxDrawdownMonthly = validation_result['data']['maxDrawdownMonthly']

        # Prior Nullable field
        if not self.pensionAmount:
            self.pensionAmount = 0

        # Update age if birthdate present
        # FIX ME - age is a silly field, it will keep needing to be updated!
        if self.birthdate_1 is not None:
            self.age_1 = calc_age(self.birthdate_1)
        if self.birthdate_2 is not None:
            self.age_2 = calc_age(self.birthdate_2)


        super(Case, self).save(*args, **kwargs)
        self.refresh_from_db()

        if is_create and self.caseNotes:
            add_case_note(self, self.caseNotes, user=None)
        

        if should_sync or is_create: 
            if self.sfOpportunityID:
                app.send_task('SF_Opp_Synch', kwargs={'caseUID': str(self.caseUID)})
                app.send_task('SF_Doc_Synch', kwargs={'caseUID': str(self.caseUID)})
            else:
                app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(self.caseUID)})



# Pre-save function to extend Case
def create_case_extensions(sender, instance, created, **kwargs):
    if created:
       loan, created = Loan.objects.get_or_create(case=instance)
       modelSettings, created = ModelSetting.objects.get_or_create(case=instance)
       lossData, created = LossData.objects.get_or_create(case=instance)
       factFind, created = FactFind.objects.get_or_create(case=instance)

post_save.connect(create_case_extensions, sender=Case)


class Loan(models.Model):

    protectedChoices = (
        (0, "0%"),
        (5, "5%"),
        (10, "10%"),
        (15, "15%"),
        (20, "20%"))

    drawdownFrequency=(
        (incomeFrequencyEnum.FORTNIGHTLY.value, 'Fortnightly'),
        (incomeFrequencyEnum.MONTHLY.value, 'Monthly'))
    productTypes = (
        ("HHC.RM.2018", "HHC.RM.2018"),
        ("HHC.RM.2021", "HHC.RM.2021")
    )

    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    product_type = models.CharField(null=True, blank=True, max_length=11, choices=productTypes)
    localLoanID = models.AutoField(primary_key=True)
    maxLVR = models.FloatField(null=False, blank=False,default=0)
    actualLVR = models.FloatField(null=True, blank=True, default=0)
    protectedEquity = models.IntegerField(default=0, choices=protectedChoices)
    detailedTitle = models.BooleanField(default=False)
    isLowLVR = models.BooleanField(default=False)

    # Contract Amounts
    purposeAmount = models.IntegerField(default=0)
    establishmentFee = models.IntegerField(default=0)
    totalLoanAmount = models.IntegerField(default=0)

    # Plan Amounts
    planPurposeAmount = models.IntegerField(default=0)
    planEstablishmentFee = models.IntegerField(default=0)
    totalPlanAmount = models.IntegerField(default=0)

    interestPayAmount = models.IntegerField(default=0)
    interestPayPeriod = models.IntegerField(default=0)
    annualPensionIncome = models.IntegerField(default=0)

    # Customer Selections
    choiceRetireAtHome = models.BooleanField(default=False)
    choiceAvoidDownsizing = models.BooleanField(default=False)
    choiceAccessFunds = models.BooleanField(default=False)
    choiceTopUp = models.BooleanField(default=False)
    choiceRefinance = models.BooleanField(default=False)
    choiceGive = models.BooleanField(default=False)
    choiceReserve = models.BooleanField(default=False)
    choiceLive = models.BooleanField(default=False)
    choiceCare = models.BooleanField(default=False)
    choiceFuture = models.BooleanField(default=False)
    choiceCenterlink= models.BooleanField(default=False)
    choiceVariable = models.BooleanField(default=False)
    consentPrivacy= models.BooleanField(default=False)
    consentElectronic = models.BooleanField(default=False)

    #Variations
    accruedInterest = models.IntegerField(null=True, blank=True)
    orgTotalLoanAmount = models.IntegerField(default=0)
    orgPurposeAmount = models.IntegerField(default=0)
    orgEstablishmentFee = models.IntegerField(default=0)
    variationTotalAmount = models.IntegerField(default=0)
    variationPurposeAmount = models.IntegerField(default=0)
    variationFeeAmount = models.IntegerField(default=0)


    objects=CaseManager()

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    class Meta:
        verbose_name_plural = "Case Loan Details"

    def get_purposes(self):
        dict={}
        qs = LoanPurposes.objects.filter(loan = self)
        for purpose in qs:
            if purpose.enumCategory in dict:
                dict[purpose.enumCategory][purpose.enumIntention] = purpose
            else:
                dict[purpose.enumCategory]={purpose.enumIntention:purpose}
        return dict

    def purpose(self, category, intention):
        qs = LoanPurposes.objects.filter(loan=self)
        for purpose in qs:
            if purpose.enumCategory == category and purpose.enumIntention == intention:
                return purpose

    def save(self, *args, **kwargs):
        is_create = self.pk is None 
        if is_create:
            # default new.
            self.product_type = get_default_product_now()
        
        super(Loan, self).save(*args, **kwargs)
class LoanPurposes(models.Model):

    drawdownFrequencyTypes=(
        (incomeFrequencyEnum.FORTNIGHTLY.value, 'Fortnightly'),
        (incomeFrequencyEnum.MONTHLY.value, 'Monthly'))

    categoryTypes = (
        (purposeCategoryEnum.TOP_UP.value, "TOP_UP"),
        (purposeCategoryEnum.REFINANCE.value, "REFINANCE"),
        (purposeCategoryEnum.LIVE.value, "LIVE"),
        (purposeCategoryEnum.GIVE.value, "GIVE"),
        (purposeCategoryEnum.CARE.value, "CARE")
    )

    intentionTypes = (
        (purposeIntentionEnum.INVESTMENT.value, "INVESTMENT"),
        (purposeIntentionEnum.CONTINGENCY.value, "CONTINGENCY"),
        (purposeIntentionEnum.REGULAR_DRAWDOWN.value, "REGULAR_DRAWDOWN"),
        (purposeIntentionEnum.GIVE_TO_FAMILY.value, "GIVE_TO_FAMILY"),
        (purposeIntentionEnum.RENOVATIONS.value, "RENOVATIONS"),
        (purposeIntentionEnum.TRANSPORT_AND_TRAVEL.value, "TRANSPORT_AND_TRAVEL"),
        (purposeIntentionEnum.LUMP_SUM.value, "LUMP_SUM"),
        (purposeIntentionEnum.MORTGAGE.value, "MORTGAGE"),
        (purposeIntentionEnum.REGULAR_DRAWDOWN_FUNDED.value, "REGULAR_DRAWDOWN_FUNDED")
    )

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    purposeID = models.AutoField(primary_key=True)
    purposeUID = models.UUIDField(default=uuid.uuid4, editable=False)
    active = models.BooleanField(default=True)
    category = models.IntegerField(choices=categoryTypes)
    intention = models.IntegerField(choices=intentionTypes)
    amount = models.IntegerField(default=0,blank=True, null=True)
    originalAmount = models.IntegerField(default=0,blank=True, null=True)
    drawdownAmount = models.IntegerField(default=0,blank=True, null=True)
    drawdownFrequency = models.IntegerField(choices=drawdownFrequencyTypes, blank=True, null=True)
    drawdownStartDate = models.DateTimeField(blank=True, null=True)
    drawdownEndDate = models.DateTimeField(blank=True, null=True)

    contractDrawdowns = models.IntegerField(default = 0, blank=True, null=True)
    planDrawdowns = models.IntegerField(default = 0, blank=True, null=True)
    planAmount = models.IntegerField(default=0,blank=True, null=True)

    planPeriod = models.IntegerField(default=0, blank=True, null=True)  # used for simple input

    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    topUpBuffer = models.BooleanField(default = False) #deprecated


    class Meta:
        verbose_name_plural = "Case Loan Purposes"

    @property
    def variationAmount(self):
        return self.amount - self.originalAmount

    @property
    def enumCategory(self):
        return dict(self.categoryTypes)[self.category]

    @property
    def enumIntention(self):
        return dict(self.intentionTypes)[self.intention]

    @property
    def enumDrawdownFrequency(self):
        if self.drawdownFrequency:
            return dict(self.drawdownFrequencyTypes)[self.drawdownFrequency]

    @property
    def enumDrawdownFreqVal(self):
        if self.drawdownFrequency:
            return 12 if self.drawdownFrequency == incomeFrequencyEnum.MONTHLY.value else 26

    def get_absolute_url(self):
        if self.intention in [
            purposeIntentionEnum.REGULAR_DRAWDOWN.value,
            purposeIntentionEnum.REGULAR_DRAWDOWN_FUNDED.value
        ]:
            return reverse_lazy("case:caseVariationDrawdown", kwargs={"purposeUID": self.purposeUID})
        else:
            return reverse_lazy("case:caseVariationLumpSum", kwargs={"purposeUID": self.purposeUID})

    @property
    def enumCategoryPretty(self):
        return dict(self.categoryTypes)[self.category].replace("_"," ").lower().title()

    @property
    def enumIntentionPretty(self):
        return dict(self.intentionTypes)[self.intention].replace("_"," ").lower().title().replace(" To ", " to ").replace(" And ", " and ")


class LoanApplication(models.Model):
    expenseFrequencyTypes = (
        (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
        (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        (incomeFrequencyEnum.QUARTERLY.value, "Quarterly"),
        (incomeFrequencyEnum.ANNUALLY.value, "Annually")
    )

    incomeFrequencyTypes = (
        (incomeFrequencyEnum.WEEKLY.value, "Weekly"),
        (incomeFrequencyEnum.FORTNIGHTLY.value, "Fortnightly"),
        (incomeFrequencyEnum.MONTHLY.value, "Monthly"),
        (incomeFrequencyEnum.ANNUALLY.value, "Annually")
    )

    loan = models.OneToOneField(Loan, on_delete=models.CASCADE)
    localAppID = models.AutoField(primary_key=True)
    # reference field (to Applications Model)
    appUID = models.UUIDField(null=True, blank=True)

    #Application Financial Fields
    assetSaving = models.IntegerField(default=0)
    assetVehicles = models.IntegerField(default=0)
    assetOther = models.IntegerField(default=0)
    liabLoans = models.IntegerField(default=0)
    liabCards = models.IntegerField(default=0)
    liabOther = models.IntegerField(default=0)
    limitCards = models.IntegerField(default=0)
    totalAnnualIncome = models.IntegerField(default=0)
    incomePension = models.IntegerField(default=0)
    incomePensionFreq = models.IntegerField(choices=incomeFrequencyTypes, default=incomeFrequencyEnum.FORTNIGHTLY.value)
    incomeSavings = models.IntegerField(default=0)
    incomeSavingsFreq = models.IntegerField(choices=incomeFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    incomeOther = models.IntegerField(default=0)
    incomeOtherFreq = models.IntegerField(choices=incomeFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    totalAnnualExpenses = models.IntegerField(default=0)
    expenseHomeIns = models.IntegerField(default=0)
    expenseHomeInsFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseRates = models.IntegerField(default=0)
    expenseRatesFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.QUARTERLY.value)
    expenseGroceries = models.IntegerField(default=0)
    expenseGroceriesFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.WEEKLY.value)
    expenseUtilities = models.IntegerField(default=0)
    expenseUtilitiesFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.QUARTERLY.value)
    expenseMedical = models.IntegerField(default=0)
    expenseMedicalFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseTransport = models.IntegerField(default=0)
    expenseTransportFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseRepay = models.IntegerField(default=0)
    expenseRepayFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)
    expenseOther = models.IntegerField(default=0)
    expenseOtherFreq = models.IntegerField(choices=expenseFrequencyTypes, default=incomeFrequencyEnum.MONTHLY.value)

    #Income Fields
    choiceProduct = models.BooleanField(default=True)
    choiceOtherNeeds = models.BooleanField(blank=True, null=True)
    choiceMortgage = models.BooleanField(blank=True, null=True)
    choiceOwnership = models.BooleanField(blank=True, null=True)
    choiceOccupants = models.BooleanField(blank=True, null=True)

    #Bank Details
    bankBsbNumber = models.CharField(max_length=7, null=True, blank=True)
    bankAccountName = models.CharField(max_length=20, null=True, blank=True)
    bankAccountNumber = models.CharField(max_length=12, null=True, blank=True)

    #Workflow
    signingName_1 = models.CharField(max_length=50, null=True, blank=True)
    signingName_2 = models.CharField(max_length=50, null=True, blank=True)
    signingDate = models.DateTimeField(blank=True, null=True)
    ip_address =  models.CharField(max_length=60, null=True, blank=True)
    user_agent = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Case Loan Application"

    def __str__(self):
        return smart_text(self.loan.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.loan.case.caseDescription)


class ModelSetting(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    inflationRate=models.FloatField(null=True, blank=True)
    housePriceInflation=models.FloatField(null=True, blank=True)
    interestRate=models.FloatField(null=True, blank=True)
    lendingMargin=models.FloatField(null=True, blank=True)
    comparisonRateIncrement=models.FloatField(null=True, blank=True)
    establishmentFeeRate=models.FloatField(null=True, blank=True)

    objects=CaseManager()

    class Meta:
        verbose_name_plural = "Case Settings"

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)


class LossData(models.Model):
    closeReasonTypes=(
        (closeReasonEnumUpdated.BELOW_MIN_AGE.value, 'Below minimum age'),
        (closeReasonEnumUpdated.INVALID_REFER_POSTCODE.value, 'Invalid or rejected refer postcode'),
        (closeReasonEnumUpdated.BELOW_MIN_LOAN_AMOUNT.value, 'Below minimum loan amount'),
        (closeReasonEnumUpdated.ABOVE_MAX_LOAN_AMOUNT.value, 'Above maximum loan amount'),
        (closeReasonEnumUpdated.REFI_TOO_LARGE.value, 'Refinance too large'),
        (closeReasonEnumUpdated.UNSUITABLE_PURPOSE.value, 'Unsuitable purpose'),
        (closeReasonEnumUpdated.UNSUITABLE_PROPERTY.value, 'Unsuitable property'),
        (closeReasonEnumUpdated.UNSUITABLE_TITLE_OWNERSHIP.value, 'Unsuitable title ownership'),
        (closeReasonEnumUpdated.DECEASED_BORROWER.value, 'Deceased borrower'),
        (closeReasonEnumUpdated.NOT_PROCEEDING.value, 'Not proceeding'),
        (closeReasonEnumUpdated.DOESNT_LIKE_REV_MORTGAGES.value, 'Doesn’t like Reverse Mortgages'),
        (closeReasonEnumUpdated.FEE_INTEREST_TOO_HIGH.value, 'Fees or interest rate too high'),
        (closeReasonEnumUpdated.OTHER.value, 'Other'),


        # OLD VALUES -> Remove after migration
        (closeReasonEnumUpdated.AGE_RESTRICTION.value, 'Age Restriction'),
        (closeReasonEnumUpdated.POSTCODE_RESTRICTION.value, 'Postcode Restriction'),
        (closeReasonEnumUpdated.MINIMUM_LOAN_AMOUNT.value, 'Below minimum loan amount'),
        (closeReasonEnumUpdated.CREDIT.value, 'Credit History'),
        (closeReasonEnumUpdated.MORTGAGE.value, 'Mortgage too Large'),
        (closeReasonEnumUpdated.SHORT_TERM.value, 'Short-term / Bridging Requirement'),
        (closeReasonEnumUpdated.TENANTS.value, 'Tenants in common'),
        (closeReasonEnumUpdated.ALTERNATIVE_SOLUTION.value, 'Client Pursuing Alternative'),
        (closeReasonEnumUpdated.COMPETITOR.value, 'Client went to Competitor'),
        (closeReasonEnumUpdated.NO_CLIENT_ACTION.value, 'No further action by client'),
    )

    case = models.OneToOneField(Case, on_delete=models.CASCADE)

    lossNotes=models.TextField(blank=True, null=True) # remove this

    closeDate = models.DateField(blank=True, null=True)
    closeReason = models.IntegerField(blank=True, null=True, choices=closeReasonTypes)

    followUpDate=models.DateField(blank=True, null=True)
    followUpNotes = models.TextField(blank=True, null=True)
    doNotMarket = models.BooleanField(default=False) # NOTE: Migrate values to case Object once deployed 

    objects = CaseManager()

    class Meta:
        verbose_name_plural = "Case Loss Data"

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    def enumCloseReason(self):
        try:
            return dict(self.closeReasonTypes)[self.closeReason]
        except:
            return None

    class Meta:
        verbose_name_plural = "Case Loss Data"


class FactFind(models.Model):

    lengthOfStayTypes = (
        (lengthOfStayEnum.LESS_1_YEAR.value, '< 1 Year'),
        (lengthOfStayEnum.ONE_YEAR.value, '1 Year'),
        (lengthOfStayEnum.TWO_YEAR.value, '2 Years'),
        (lengthOfStayEnum.THREE_YEAR.value, '3 Years'),
        (lengthOfStayEnum.FOUR_YEAR.value, '4 Years'),
        (lengthOfStayEnum.FIVE_YEAR.value, '5 Years'),
        (lengthOfStayEnum.SIX_YEAR.value, '6 Years'),
        (lengthOfStayEnum.SEVEN_YEAR.value, '7 Years'),
        (lengthOfStayEnum.EIGHT_YEAR.value, '8 Years'),
        (lengthOfStayEnum.NINE_YEAR.value, '9 Years'),
        (lengthOfStayEnum.TEN_YEAR.value, '10 Years'),
        (lengthOfStayEnum.MORE_THAN_10_YEAR.value, 'More than 10 Years'),
        (lengthOfStayEnum.LONG_AS_POSSIBLE.value, 'Long as possible'),
    )

    methodOfDischargeTypes = (
        (methodOfDischargeEnum.DEATH.value, 'Death'),
        (methodOfDischargeEnum.AGED_CARE.value, 'Aged Care'),
        (methodOfDischargeEnum.SALE.value, 'Sale'),
        (methodOfDischargeEnum.VOLUNTARY_REPAYMENT.value, 'Voluntary Repayment'),
    )

    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    backgroundNotes = models.TextField(blank=True, null=True)
    requirementsNotes = models.TextField(blank=True, null=True)
    topUpNotes = models.TextField(blank=True, null=True)
    refiNotes = models.TextField(blank=True, null=True)
    liveNotes = models.TextField(blank=True, null=True)
    giveNotes = models.TextField(blank=True, null=True)
    careNotes = models.TextField(blank=True, null=True)
    futureNotes = models.TextField(blank=True, null=True)
    clientNotes = models.TextField(blank=True, null=True)
    additionalNotes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    

    #meeting data
    all_applications_are_engaged = models.BooleanField(blank=True, null=True)
    applicants_disengagement_reason = models.TextField(blank=True, null=True)
    
    is_third_party_engaged = models.BooleanField(blank=True, null=True)
    reason_for_thirdparty_engagement = models.TextField(blank=True, null=True)

    applicant_poa_signing = models.BooleanField(blank=True, null=True)
    planned_length_of_stay = models.IntegerField(choices=lengthOfStayTypes, null=True, blank=True)
    planned_method_of_discharge = models.IntegerField(choices=methodOfDischargeTypes, null=True, blank=True)
    
    #customer Data 
    is_vulnerable_customer = models.BooleanField(blank=True, null=True)
    vulnerability_description = models.TextField(blank=True, null=True)
    considered_alt_downsizing_opts = models.BooleanField(blank=True, null=True)
    
    plan_for_future_giving = models.TextField(blank=True, null=True)
    plan_for_aged_care = models.TextField(blank=True, null=True)

    additional_info_credit = models.TextField(blank=True, null=True)

    objects = CaseManager()

    class Meta:
        verbose_name_plural = "Case Fact Find"

    def __str__(self):
        return smart_text(self.case.caseDescription)

    def __unicode__(self):
        return smart_text(self.case.caseDescription)

    @property
    def enumPlannedLengthOfStay(self):
        return dict(self.lengthOfStayTypes).get(self.planned_length_of_stay)

    @property
    def enumPlannedMethodOfDischarge(self):
        return dict(self.methodOfDischargeTypes).get(self.planned_method_of_discharge)