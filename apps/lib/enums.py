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
    LEAD=0
    OPPORTUNITY= 1
    MEETING_HELD= 2
    CLOSED=3
    APPLICATION=4

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
    IND_FINANCIAL_ADVISORS=0
    INST_FINANCIAL_ADVISORS=1
    SUPER_FINANCIAL_ADVISORS=2
    AGED_CARE_ADVISORS=3
    AGED_CARE_PROVIDERS_CONSULTANTS=4
    ACCOUNTANTS=5
    CENTRELINK_ADVISORS=6
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
    OTHER=100