#Python Imports
from enum import Enum

# Enum class is callable and the templating system will try and call it
# This decorator sets a property to prevent the call, ensuring the
# classes enumerate properly

def accessInTemplate(cls):
    cls.do_not_call_in_templates = True
    return cls


@accessInTemplate
class appTypesEnum(Enum):
    NEW_APPLICATION = 0
    VARIATION = 1

@accessInTemplate
class caseStagesEnum(Enum):
    WAIT_LIST = 18
    DISCOVERY=0
    PRE_MEETING= 1
    MEETING_HELD= 2
    CLOSED=3
    APPLICATION=4
    DOCUMENTATION=5
    FUNDED = 6
    # Breakdown of discovery stage
    UNQUALIFIED_CREATED = 7 
    MARKETING_QUALIFIED = 8 
    SQ_GENERAL_INFO = 9 
    SQ_BROCHURE_SENT = 10
    SQ_CUSTOMER_SUMMARY_SENT = 11 
    SQ_FUTURE_CALL = 12 

    SQ_NO_ANSWER = 14 
    SQ_VOICEMAIL = 15 
    SQ_EMAIL_SENT = 16

    MEETING_BOOKED = 17

    SALES_ACTIVE = 13

PRE_MEETING_STAGES = [
    'WAIT_LIST',
    'UNQUALIFIED_CREATED',
    'MARKETING_QUALIFIED',
    'SQ_GENERAL_INFO',
    'SQ_BROCHURE_SENT',
    'SQ_CUSTOMER_SUMMARY_SENT',
    'SQ_FUTURE_CALL', 
    'SALES_ACTIVE',

    'SQ_NO_ANSWER',
    'SQ_VOICEMAIL',
    'SQ_EMAIL_SENT',
    'MEETING_BOOKED',
    
    'DISCOVERY',
]

EDITABLE_STAGES = PRE_MEETING_STAGES + ['MEETING_HELD', 'APPLICATION', 'CLOSED']


# Unqualified / Lead created (automatic state when a lead is created through any channel)
# Marketing Qualified (set when we know the lead is eligible, i.e. not ineligible)
# SQ - General Info
# SQ - Brochure sent
# SQ - Customer summary sent
# SQ - Future call

@accessInTemplate
class clientSexEnum(Enum):
    FEMALE=0
    MALE=1

@accessInTemplate
class pensionTypesEnum(Enum):
    FULL_PENSION =0
    PARTIAL_PENSION =1
    NO_PENSION =2

@accessInTemplate
class investmentTypesEnum(Enum):
    SUPER = 0
    SHARES =1
    PROPERTY = 2
    COMBINED = 3

@accessInTemplate
class productTypesEnum(Enum):
    LUMP_SUM = 0
    INCOME = 1
    COMBINATION = 2
    CONTINGENCY_20K = 3
    REFINANCE = 4

@accessInTemplate
class loanTypesEnum(Enum):
    SINGLE_BORROWER=0
    JOINT_BORROWER=1

@accessInTemplate
class dwellingTypesEnum(Enum):
    HOUSE=0
    APARTMENT=1

@accessInTemplate
class ragTypesEnum(Enum):
    RED=0
    AMBER=1
    GREEN=2

@accessInTemplate
class channelTypesEnum(Enum):
    DIRECT_ACQUISITION=11    
    PARTNER = 12
    BROKER=7
    ADVISER = 13
    IND_FINANCIAL_ADVISERS = 0  # Deprecated
    INST_FINANCIAL_ADVISERS = 1  # Deprecated
    SUPER_FINANCIAL_ADVISERS = 2  # Deprecated
    AGED_CARE_ADVISERS = 3  # Deprecated
    AGED_CARE_PROVIDERS_CONSULTANTS = 4  # Deprecated
    ACCOUNTANTS = 5  # Deprecated
    CENTRELINK_ADVISERS = 6  # Deprecated
    BANK_REFERRAL = 8  # Deprecated
    BANK_REFI = 9  # Deprecated
    SUPER_MEMBERS_DIRECT = 10  # Deprecated

@accessInTemplate
class directTypesEnum(Enum):
    PHONE = 0
    EMAIL = 1
    WEB_CALCULATOR = 2
    WEB_ENQUIRY = 3
    BROKER=4
    PARTNER = 5
    SOCIAL = 6
    ADVISER = 7
    OTHER=100


@accessInTemplate
class marketingTypesEnum(Enum):
    TV_ADVERT = 1
    TV_ADVERTORIAL = 2
    RADIO = 3
    WORD_OF_MOUTH = 4
    ADVISER = 5
    COMPETITOR = 6
    DIRECT_MAIL = 7
    WEB_SEARCH = 11
    DIRECT_EMAIL = 12
    FACEBOOK = 8
    LINKEDIN = 9
    YOUR_LIFE_CHOICES = 10
    STARTS_AT_60 = 13
    CARE_ABOUT = 14
    BROKER_SPECIALIST = 15
    BROKER_REFERRAL = 16
    FINANCIAL_ADVISER = 17
    AGED_CARE_ADVISER = 18
    NATIONAL_SENIORS = 19
    FACEBOOK_INTERACTIVE = 20
    FACEBOOK_CALCULATOR = 21
    OTHER = 100


@accessInTemplate
class stateTypesEnum(Enum):
    NSW = 0
    VIC = 1
    ACT = 2
    QLD = 3
    SA = 4
    WA = 5
    TAS = 6
    NT = 7

@accessInTemplate
class incomeFrequencyEnum(Enum):
    FORTNIGHTLY = 1
    MONTHLY = 2
    WEEKLY = 3
    QUARTERLY = 4
    ANNUALLY = 5

@accessInTemplate
class enquiryStagesEnum(Enum):
    GENERAL_INFORMATION = 1
    BROCHURE_SENT = 2
    SUMMARY_SENT = 3
    DISCOVERY_MEETING = 4
    LOAN_INTERVIEW = 5
    LIVE_TRANSFER = 6
    DUPLICATE = 7
    FUTURE_CALL = 8
    DID_NOT_QUALIFY = 9
    NOT_PROCEEDING = 10
    FOLLOW_UP_NO_ANSWER = 11
    FOLLOW_UP_VOICEMAIL = 12
    INITIAL_NO_ANSWER = 13
    NVN_EMAIL_SENT = 14
    MORE_TIME_TO_THINK = 15
    WAIT_LIST = 16

@accessInTemplate
class closeReasonEnum(Enum):
    AGE_RESTRICTION=1
    POSTCODE_RESTRICTION = 2
    MINIMUM_LOAN_AMOUNT=3
    CREDIT = 4
    MORTGAGE = 5
    SHORT_TERM = 6
    TENANTS = 7
    UNSUITABLE_PROPERTY = 8
    UNSUITABLE_PURPOSE = 9
    ALTERNATIVE_SOLUTION=10
    COMPETITOR=11
    NO_CLIENT_ACTION=13
    CALL_ONLY = 14
    ANTI_REVERSE_MORTGAGE = 15
    FEES = 15
    DUPLICATE = 16
    OTHER = 12


# Below minimum age
# Invalid or rejected refer postcode
# Below minimum loan amount
# Above maximum loan amount
# Refinance too large
# Unsuitable purpose
# Unsuitable property
# Unsuitable title ownership
# Deceased borrower
# Not proceeding
# Other
@accessInTemplate
class closeReasonEnumUpdated(Enum): 
    AGE_RESTRICTION=1
    POSTCODE_RESTRICTION = 2
    MINIMUM_LOAN_AMOUNT=3
    CREDIT = 4
    MORTGAGE = 5
    SHORT_TERM = 6
    TENANTS = 7
    UNSUITABLE_PROPERTY = 8
    UNSUITABLE_PURPOSE = 9
    ALTERNATIVE_SOLUTION=10
    COMPETITOR=11
    NO_CLIENT_ACTION=13
    CALL_ONLY = 14
    ANTI_REVERSE_MORTGAGE = 15
    FEES = 15
    DUPLICATE = 16
    OTHER = 12
    
    ### ^^ OLD ^^ ###

    BELOW_MIN_AGE = 31
    INVALID_REFER_POSTCODE = 32
    BELOW_MIN_LOAN_AMOUNT = 33
    ABOVE_MAX_LOAN_AMOUNT = 34
    REFI_TOO_LARGE = 35
    UNSUITABLE_TITLE_OWNERSHIP = 38
    DECEASED_BORROWER = 39
    NOT_PROCEEDING = 40
    DOESNT_LIKE_REV_MORTGAGES = 41
    FEE_INTEREST_TOO_HIGH = 43

    #Doesn’t like Reverse Mortgages
    #Fees or interest rate too high



@accessInTemplate
class salutationEnum(Enum):
    MR = 1
    MS = 2
    MRS = 3
    DR = 4
    PROF = 5

@accessInTemplate
class maritalEnum(Enum):
    SINGLE = 1
    MARRIED = 2
    DIVORCED = 3
    WIDOWED = 4
    DEFACTO = 5
    SEPARATED = 6

@accessInTemplate
class clientTypesEnum(Enum):
    BORROWER= 0
    NOMINATED_OCCUPANT= 1
    POWER_OF_ATTORNEY= 2
    PERMITTED_COHABITANT = 3

@accessInTemplate
class roleEnum(Enum):
    PRINCIPAL_BORROWER = 0
    SECONDARY_BORROWER = 1
    BORROWER = 2
    NOMINATED_OCCUPANT = 3
    PERMITTED_COHABITANT = 4
    POWER_OF_ATTORNEY = 5
    AUTH_3RD_PARTY = 6
    DISTRIBUTION_PARTNER = 7
    ADVISER = 8
    LOAN_ORIGINATOR = 9
    LOAN_WRITER = 10
    VALUER = 11
    EXECUTOR = 12
    SOLICITOR = 13
    BENEFICIAL_OWNER = 14
    DOCUMENT_CUSTODIAN = 15


@accessInTemplate
class authTypesEnum(Enum):
    NO = 0
    YES = 1
    REFER_POA = 2


@accessInTemplate
class facilityStatusEnum(Enum):
    INACTIVE = 0
    ACTIVE = 1
    REPAID = 2
    SUSPENDED = 3

@accessInTemplate
class purposeCategoryEnum(Enum):
    TOP_UP = 1
    REFINANCE = 2
    LIVE = 3
    GIVE = 4
    CARE = 5

@accessInTemplate
class purposeIntentionEnum(Enum):
    INVESTMENT = 1
    CONTINGENCY = 2
    REGULAR_DRAWDOWN = 3
    GIVE_TO_FAMILY = 4
    RENOVATIONS = 5
    TRANSPORT_AND_TRAVEL = 6
    LUMP_SUM = 7
    MORTGAGE  = 8

@accessInTemplate
class appStatusEnum(Enum):
    CREATED = 0
    IN_PROGRESS = 1
    EXPIRED = 2
    SUBMITTED = 3
    CONTACT = 4
    CLOSED = 5

@accessInTemplate
class documentTypesEnum(Enum):
    RATES=1
    INSURANCE=2
    STRATA_LEVIES = 3
    OTHER = 100



#Squash migrations and delete
class closeReasonTypes(Enum):
    AGE_RESTRICTION=1
    POSTCODE_RESTRICTION = 2
    MINIMUM_LOAN_AMOUNT=3
    CREDIT = 4
    MORTGAGE = 5
    SHORT_TERM = 6
    TENANTS = 7
    UNSUITABLE_PROPERTY = 8
    UNSUITABLE_PURPOSE = 9
    ALTERNATIVE_SOLUTION=10
    COMPETITOR=11
    NO_CLIENT_ACTION=13
    OTHER = 12

class lengthOfStayEnum(Enum):
    LESS_1_YEAR = 1
    ONE_YEAR = 2
    TWO_YEAR = 3
    THREE_YEAR = 4
    FOUR_YEAR = 5
    FIVE_YEAR = 6
    SIX_YEAR = 7
    SEVEN_YEAR = 8
    EIGHT_YEAR = 9
    NINE_YEAR = 10
    TEN_YEAR = 11
    MORE_THAN_10_YEAR = 12
    LONG_AS_POSSIBLE = 13 

class methodOfDischargeEnum(Enum):
    DEATH = 1
    AGED_CARE = 2
    SALE = 3 
    VOLUNTARY_REPAYMENT = 4  
    
@accessInTemplate
class propensityCategoriesEnum(Enum):
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5
    F = 6


propensityChoices = [
    (propensityCategoriesEnum.A.value, 'A'),
    (propensityCategoriesEnum.B.value, 'B'),
    (propensityCategoriesEnum.C.value, 'C'),
    (propensityCategoriesEnum.D.value, 'D'),
    (propensityCategoriesEnum.E.value, 'E'),
    (propensityCategoriesEnum.F.value, 'F'),
]

propensityChoicesReverseDict = {
    y:x 
    for x,y in propensityChoices
}

marketingReferrerDict = {
    "TV_ADVERT":"OTHER",
    "TV_ADVERTORIAL": "OTHER", 
    "RADIO": "OTHER",
    "WORD_OF_MOUTH": "OTHER", 
    "ADVISER": "ADVISOR",
    "COMPETITOR": "OTHER", 
    "DIRECT_MAIL": "OTHER", 
    "WEB_SEARCH": "WEB_ENQUIRY", 
    "DIRECT_EMAIL": "EMAIL", 
    "FACEBOOK": "SOCIAL", 
    "LINKEDIN": "SOCIAL",
    "YOUR_LIFE_CHOICES": "PARTNER", 
    "STARTS_AT_60": "PARTNER", 
    "CARE_ABOUT": "PARTNER", 
    "BROKER_SPECIALIST": "BROKER", 
    "BROKER_REFERRAL": "BROKER", 
    "FINANCIAL_ADVISER": "ADVISOR", 
    "AGED_CARE_ADVISER": "ADVISOR", 
    "NATIONAL_SENIORS": "PARTNER", 
    "OTHER": "OTHER" 
}

RESET_DO_NOT_MARKET = [
    directTypesEnum.PARTNER.value,
    directTypesEnum.SOCIAL.value,
    directTypesEnum.WEB_CALCULATOR.value,
    directTypesEnum.WEB_ENQUIRY.value
]