
from enum import Enum

# Enum class is callable and the templating system will try and call it
# This decorator sets a property to prevent the call, ensuring the
# classes enumeraye properly
def accessInTemplate(cls):
    cls.do_not_call_in_templates = True
    return cls


@accessInTemplate
class caseTypesEnum(Enum):
    LEAD=0
    OPPORTUNITY= 1
    MEETING_HELD= 2
    CLOSED=3

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


