import csv
import logging
from datetime import datetime

from django.conf import settings

logger = logging.getLogger('myApps')


def write_applog(log_level, log_module, log_function, log_message):
    log_entry = str(datetime.now()) + "|" + log_level + "|" + log_module + "|" + log_function + "|" + log_message

    if log_level=="INFO":
        logger.info(log_entry)
    elif log_level=="ERROR":
        logger.info(log_entry)

def chkCreditCriteria(isJoint,age, isApartment,postcode,valuation):

    resultDict={}
    lvrAge=0
    lvr=0


    resultDict['calculated']=True
    resultDict['youngestAge']=age
    resultDict['isJoint']=isJoint
    resultDict['postcode']=postcode
    resultDict['valuation']=int(round(valuation,0))
    resultDict['isApartment'] = isApartment

    #Check Age
    if age < 60:
        resultDict['ageCriteria'] = '[Fail] Youngest borrower must be 60'

    elif isJoint and age<65:
        resultDict['ageCriteria'] = '[Fail] Youngest joint borrower must be 65'

    else:
        resultDict['ageCriteria'] = 'Age criteria satisfied'
        lvrAge=age

    #Calculate LVR
    if lvrAge>0:
        lvr=.15+(lvrAge-60)*.01

    if isApartment:
        lvr=max(lvr-.05,0)

    #Check Postcode
    validPostcode=chkPostcode(postcode)
    if validPostcode:
        resultDict['postcodeCriteria']='Eligible postcode'
    else:
        resultDict['postcodeCriteria'] = '[Fail] InEligible postcode'
        lvr=0

    #Check Min Loan Size
    if lvr!=0:
        if lvr*valuation<30000:
            resultDict['minLoanSize']='[Fail] Minimum Loan Size not met $'+"{:,}".format(int(lvr*valuation))
            lvr=0
        else:
            resultDict['minLoanSize'] = 'Minimum Loan Size met'

    #Amounts
    resultDict['maxLvr']=round(lvr*100,1)

    resultDict['maxLoan']=int(round(lvr*valuation,0))

    if lvr==0:
        resultDict['eligible'] = False
    else:
        resultDict['eligible'] = True

    resultDict['maxSuper']=500000
    resultDict['maxAgeCare'] = 550000
    resultDict['maxReno']=200000
    resultDict['maxRefi']= int(lvr*valuation*.25)
    resultDict['maxGive']= int(lvr*valuation*.20)
    resultDict['maxSecond']= int(lvr*valuation*.20)

    return resultDict

def chkPostcode(postcode):
    reader = csv.reader(open(settings.BASE_DIR+'/apps/eligibility/Postcodes.csv', 'r'))
    pcodeDict = dict(reader)

    if postcode in pcodeDict:
        return True
    else:
        return False
