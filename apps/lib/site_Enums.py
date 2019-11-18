#Python Imports
from enum import Enum

# Enum class is callable and the templating system will try and call it
# This decorator sets a property to prevent the call, ensuring the
# classes enumerate properly
def accessInTemplate(cls):
    cls.do_not_call_in_templates = True
    return cls


@accessInTemplate
class caseTypesEnum(Enum):
    DISCOVERY=0
    PRE_MEETING= 1
    MEETING_HELD= 2
    CLOSED=3
    APPLICATION=4
    DOCUMENTATION=5
    FUNDED = 6

@accessInTemplate
class clientTypesEnum(Enum):
    BORROWER= 0
    NOMINATED_OCCUPANT= 1
    POWER_OF_ATTORNEY= 2

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
    IND_FINANCIAL_ADVISERS=0
    INST_FINANCIAL_ADVISERS=1
    SUPER_FINANCIAL_ADVISERS=2
    AGED_CARE_ADVISERS=3
    AGED_CARE_PROVIDERS_CONSULTANTS=4
    ACCOUNTANTS=5
    CENTRELINK_ADVISERS=6
    BROKERS=7
    BANK_REFERRAL=8
    BANK_REFI=9
    SUPER_MEMBERS_DIRECT=10
    DIRECT_ACQUISITION=11

@accessInTemplate
class directTypesEnum(Enum):
    PHONE = 0
    EMAIL = 1
    WEB_CALCULATOR = 2
    WEB_ENQUIRY = 3
    REFERRAL=4
    OTHER=100

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
    OTHER = 12

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