# Python Imports
import csv

# Django Imports
from django.conf import settings

# Local Application Imports
from apps.lib.enums import dwellingTypesEnum, loanTypesEnum
from apps.lib.globals import LOAN_LIMITS


class LoanValidator():
    # Utility class to validate whether a loan meets HHC lending guidelines and restrictions
    # Object is established through passing an initial dictionary (with required fields)
    # Loan limits and enumerations are imported
    # Two methods which return dictionaries with relevant details:
    #  - validateLoan - used to validate calculator, enquiries, cases etc
    #  - getStatus - used to provide loan status within client interface
    # calcLvr is a core utility method used by methods

    minimumDataList = ['dwellingType', 'loanType', 'age_1', 'valuation', 'postcode']

    loanDataList = ['topUpAmount', 'refinanceAmount', 'giveAmount', 'renovateAmount', 'travelAmount',
                    'careAmount', 'protectedEquity', 'mortgageDebt']

    def __init__(self, clientDict, loanDict=None):

        # Check for minimum data
        self.initStatus = True
        self.initDict={}
        self.initDict.update(clientDict)
        if loanDict:
            self.initDict.update(loanDict)

        for item in self.minimumDataList:
            if not self.valueExists(item, self.initDict):
                self.initStatus = False

        # Initialisation of Instance Variables
        if self.initStatus:

            if self.initDict['dwellingType'] == dwellingTypesEnum.HOUSE.value:
                self.isApartment = False
            else:
                self.isApartment = True

            if self.initDict['loanType'] == loanTypesEnum.JOINT_BORROWER.value:
                self.isCouple = True
                if self.valueExists('age_2', self.initDict):
                    self.clientAge = min(self.initDict['age_1'], self.initDict['age_2'])
                else:
                    self.initStatus = False
            else:
                self.isCouple = False
                self.clientAge = self.initDict['age_1']

        # Set optional items = 0
        for item in self.loanDataList:
            if not self.valueExists(item, self.initDict):
                self.initDict[item] = 0

        # Limits
        self.maxLvr = 0
        self.loanLimit = 0
        self.refinanceLimit = 0
        self.giveLimit = 0
        self.travelLimit = 0

    def validateLoan(self):
        # Checks basic borrower and loan restrictions providing a status and dictionary of restrictions

        status = {}
        status['status'] = "Ok"

        # Check object instantiated properly
        if self.initStatus == False:
            status['status'] = "Error"
            status['details'] = 'Insufficient data'
            return status

        # Check Valid Postcode
        reader = csv.reader(open(settings.BASE_DIR + '/apps/lib/Postcodes.csv', 'r'))
        pcodeDict = dict(reader)

        if str(self.initDict['postcode']) in pcodeDict:
            pass
        else:
            status['status'] = "Error"
            status['details'] = 'Invalid Postcode'

        # Check Age
        if self.clientAge < LOAN_LIMITS['minSingleAge']:
            status['status'] = "Error"
            status['details'] = 'Youngest borrower must be 60'
            return status

        elif self.isCouple and self.clientAge < LOAN_LIMITS['minCoupleAge']:
            status['status'] = "Error"
            status['details'] = 'Youngest joint borrower must be 65'
            return status

        # Perform LVR calculations (for loan size validation)
        self.calcLVR()

        # Check Min Loan Size
        if self.maxLvr / 100 * self.initDict['valuation'] < LOAN_LIMITS['minLoanSize']:
            status['status'] = "Error"
            status['details'] = 'Minimum Loan Size cannot be met'
            return status

        # Check Mortgage Debt
        if int(self.initDict['mortgageDebt']) > int(
                self.maxLvr / 100 * self.initDict['valuation'] * LOAN_LIMITS['maxRefi']):
            status['status'] = "Error"
            status['details'] = 'Mortgage debt too large to be refinanced'
            return status

        # Restrictions
        restrictions = {}

        restrictions['maxLoan'] = int(self.loanLimit)
        restrictions['maxFee'] = int(
            restrictions['maxLoan'] * LOAN_LIMITS['establishmentFee'] / (1 + LOAN_LIMITS['establishmentFee']))
        restrictions['maxLVR'] = int(self.maxLvr)
        restrictions['maxTopUp'] = LOAN_LIMITS['maxTopUp']
        restrictions['maxCare'] = LOAN_LIMITS['maxCare']
        restrictions['maxReno'] = LOAN_LIMITS['maxReno']
        restrictions['maxRefi'] = int(self.refinanceLimit)
        restrictions['maxGive'] = int(self.giveLimit)
        restrictions['maxTravel'] = int(self.travelLimit)

        status['restrictions'] = restrictions

        return status

    def getStatus(self):
        # Provides detailed array based on primary purposes.
        # Designed to be utilised as user proceeds through the client app
        # Recognises that there can be interdependency between purposes

        # Note complication of establishment fee that reduces the usable loan proceeds
        # The totalLoanAmount is always correct based on % Establishment Fee
        # The available amount is an estimate based on the maximum $ establishment fee
        # (hence doesn't vary with the loan size or cause user confusion)

        status = {}
        if self.initStatus == False:
            status['status'] = "Error"
            return status

        self.calcLVR()

        maxEstablishmentFee = self.loanLimit * (
                LOAN_LIMITS['establishmentFee'] / (1 + LOAN_LIMITS['establishmentFee']))

        totalLoanAmount = (self.initDict['topUpAmount'] + self.initDict['refinanceAmount'] + self.initDict['giveAmount']
                           + self.initDict['renovateAmount'] + self.initDict['travelAmount'] + self.initDict[
                               'careAmount']) * (
                                  1 + LOAN_LIMITS['establishmentFee'])

        # Available amount always deducts the maximum establishment fee, so need to add back the calculated
        # establishment fee from the total Loan Amount
        availableAmount = round(
            self.loanLimit - totalLoanAmount / (1 + LOAN_LIMITS['establishmentFee']) - maxEstablishmentFee, 0)

        # Store primary output
        status['maxLVR'] = round(self.maxLvr, 1)
        status['maxNetLoanAmount'] = int(round(self.loanLimit - maxEstablishmentFee, 0))
        status['availableAmount'] = int(round(availableAmount, 0))
        status['establishmentFee'] = int(round(
            totalLoanAmount / (1 + LOAN_LIMITS['establishmentFee']) * LOAN_LIMITS['establishmentFee'], 0))
        status['totalLoanAmount'] = int(round(totalLoanAmount, 0))
        status['actualLVR'] = round(totalLoanAmount / self.initDict['valuation'], 1) * 100

        # Validate against limits and add to output dictionary
        status['errors'] = False
        self.chkStatusItem(status, 'availableStatus', availableAmount, int(0), "LT")
        self.chkStatusItem(status, 'minloanAmountStatus', int(round(totalLoanAmount, 0)), LOAN_LIMITS['minLoanSize'],
                           "LT")
        self.chkStatusItem(status, 'maxloanAmountStatus', int(round(totalLoanAmount, 0)), self.loanLimit, "GTE")
        self.chkStatusItem(status, 'topUpStatus', self.initDict['topUpAmount'], LOAN_LIMITS['maxTopUp'], "GTE")
        self.chkStatusItem(status, 'refinanceStatus', self.initDict['refinanceAmount'], self.refinanceLimit, "GTE")
        self.chkStatusItem(status, 'giveStatus', self.initDict['giveAmount'], self.giveLimit, "GTE")
        self.chkStatusItem(status, 'renovateStatus', self.initDict['renovateAmount'], LOAN_LIMITS['maxReno'], "GTE")
        self.chkStatusItem(status, 'travelStatus', self.initDict['travelAmount'], self.travelLimit, "GTE")
        self.chkStatusItem(status, 'careStatus', self.initDict['careAmount'], LOAN_LIMITS['maxCare'], "GTE")

        status['status'] = "Ok"

        return status

    def chkStatusItem(self, status, label, amount, limit, condition):
        # Utility function to check conditions and create response
        if condition == "LT":
            if amount < limit:
                itemStatus = "Error"
                status["errors"] = True
            else:
                itemStatus = "Ok"
        else:
            if amount > limit:
                itemStatus = "Error"
                status["errors"] = True
            else:
                itemStatus = "Ok"

        status[label] = itemStatus

    def calcLVR(self):
        # Primary LVR calculator

        # Calculate LVR
        lvr = LOAN_LIMITS['baseLvr'] + (self.clientAge - LOAN_LIMITS['baseLvrAge']) * LOAN_LIMITS[
            'baseLvrIncrement']

        # Apartment Adjustment
        if self.isApartment:
            lvr = lvr - LOAN_LIMITS['apartmentLvrAdj']

        # Protected Equity
        lvr = lvr * (1 - self.initDict['protectedEquity'] / 100)

        if lvr < 0:
            lvr = 0

        self.maxLvr = lvr * 100

        # Limits - based on maxLvr
        self.loanLimit = min(int(round(lvr * self.initDict['valuation'], 0)), LOAN_LIMITS['maxLoanSize'])

        # Limits - based actual Lvr adjusted, capped at Loan Limit
        self.refinanceLimit = min(int(lvr * self.initDict['valuation'] * LOAN_LIMITS['maxRefi']), self.loanLimit)
        self.giveLimit = min(int(lvr * self.initDict['valuation'] * LOAN_LIMITS['maxGive']), self.loanLimit)
        self.travelLimit = min(int(lvr * self.initDict['valuation'] * LOAN_LIMITS['maxTravel']), self.loanLimit)

    def valueExists(self, item, sourceDict):
        if item in sourceDict:
            if sourceDict[item] == None:
                return False
            else:
                try:
                    self.checkNumber = int(sourceDict[item])
                    return True
                except ValueError:
                    return False
        else:
            return False
