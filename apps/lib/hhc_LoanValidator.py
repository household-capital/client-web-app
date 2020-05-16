# Python Imports
import csv

# Django Imports
from django.conf import settings

# Local Application Imports
from apps.lib.site_Enums import dwellingTypesEnum, loanTypesEnum, productTypesEnum
from apps.lib.site_Globals import LOAN_LIMITS


class LoanValidator():
    # Utility class to validate whether a loan meets HHC lending guidelines and restrictions
    # Object is established through passing an initial dictionary (with required fields)
    # Loan limits and enumerations are imported
    # Two methods which return dictionaries with relevant details:
    #  - validateLoan - used to validate calculator, enquiries, cases etc
    #  - getStatus - used to provide loan status within client interface
    # calcLvr is a core utility method used by methods

    minimumDataList = ['dwellingType', 'loanType', 'age_1', 'valuation', 'postcode']

    loanDataList = ['topUpAmount', 'topUpDrawdownAmount', 'refinanceAmount', 'giveAmount', 'renovateAmount',
                    'travelAmount',
                    'careAmount', 'protectedEquity', 'mortgageDebt', 'careDrawdownAmount', 'topUpContingencyAmount',
                    'topUpPlanAmount', 'carePlanAmount', 'accruedInterest']

    POSTCODE_FILE = '/apps/lib/hhc_Postcodes.csv'

    def __init__(self, clientDict, loanDict=None, modelDict=None):

        # Check for minimum data
        self.initStatus = True
        self.initDict = {}
        self.initDict.update(clientDict)
        if loanDict:
            self.initDict.update(loanDict)
        if modelDict:
            self.initDict.update(modelDict)

        for item in self.minimumDataList:
            if not self.__valueExists(item, self.initDict):
                self.initStatus = False

        # Initialisation of Instance Variables
        if self.initStatus:

            if self.initDict['dwellingType'] == dwellingTypesEnum.HOUSE.value:
                self.isApartment = False
            else:
                self.isApartment = True

            if self.initDict['loanType'] == loanTypesEnum.JOINT_BORROWER.value:
                self.isCouple = True
                if self.__valueExists('age_2', self.initDict):
                    self.clientAge = min(self.initDict['age_1'], self.initDict['age_2'])
                else:
                    self.initStatus = False
            else:
                self.isCouple = False
                self.clientAge = self.initDict['age_1']

        # Set optional items = 0
        for item in self.loanDataList:
            if not self.__valueExists(item, self.initDict):
                self.initDict[item] = 0

        # Set / override establishment fee
        self.establishmentFee = LOAN_LIMITS['establishmentFee']
        if self.__valueExists('establishmentFeeRate', self.initDict):
            self.establishmentFee = self.initDict['establishmentFeeRate']

        # Limits
        self.maxLvr = 0
        self.maxLoan = 0
        self.loanLimit = 0
        self.refinanceLimit = 0
        self.giveLimit = 0
        self.travelLimit = 0
        self.drawdownLimit = 0
        self.maxDrawdownMonthly = 0

        # Refer Postcode
        self.isRefer = False

        # Product Type
        if 'productType' in self.initDict:
            self.productType = self.initDict['productType']
        else:
            self.productType = productTypesEnum.LUMP_SUM.value

    def validateLoan(self):
        # Checks basic borrower and loan restrictions providing a status and dictionary of data

        response = {}
        data = {}
        response['status'] = "Ok"

        # Check object instantiated properly
        if self.initStatus == False:
            response['status'] = "Error"
            response['responseText'] = 'Insufficient data'
            return response

        # Check Valid Postcode
        reader = csv.reader(open(settings.BASE_DIR + self.POSTCODE_FILE, 'r'))
        pcodeDict = {}

        for row in reader:
            pcodeDict[row[0]] = {"Acceptable": row[1], "MaxLoan": row[2]}

        if str(self.initDict['postcode']) in pcodeDict:
            if pcodeDict[str(self.initDict['postcode'])]['Acceptable'] == "Refer":
                data['postcode'] = "Refer"
                self.isRefer = True
            else:
                data['postcode'] = "Valid"
        else:
            response['status'] = "Error"
            response['responseText'] = 'Invalid Postcode'

        # Get maxLoan (from Postcode file)
        if str(self.initDict['postcode']) in pcodeDict:
            self.maxLoan = int(pcodeDict[str(self.initDict['postcode'])]['MaxLoan'])
        else:
            self.maxLoan = 0

        # Check Age
        if self.clientAge < LOAN_LIMITS['minSingleAge']:
            response['status'] = "Error"
            response['responseText'] = 'Youngest borrower must be 60'
            return response

        elif self.isCouple and self.clientAge < LOAN_LIMITS['minCoupleAge']:
            response['status'] = "Error"
            response['responseText'] = 'Youngest joint borrower must be 65'
            return response


        # Perform LVR calculations (for loan size validation)
        self.__calcLVR()


        # Check Min Loan Size
        if self.productType == productTypesEnum.LUMP_SUM.value:
            if self.maxLvr / 100 * self.initDict['valuation'] < LOAN_LIMITS['minLoanSize']:
                response['status'] = "Error"
                response['responseText'] = 'Minimum Loan Size cannot be met'
                return response
        else:
            if int(self.maxDrawdownMonthly) < LOAN_LIMITS['minIncomeDrawdown']:
                response['status'] = "Error"
                response['responseText'] = 'Minimum Loan Size cannot be met'
                return response

        # Check Mortgage Debt
        if int(self.initDict['mortgageDebt']) > int(
                self.maxLvr / 100 * self.initDict['valuation'] * LOAN_LIMITS['maxRefi']):
            response['status'] = "Error"
            response['responseText'] = 'Mortgage debt too large to be refinanced'
            return response

        # data
        data['maxLoan'] = int(self.loanLimit)
        data['maxFee'] = int(data['maxLoan'] * self.establishmentFee / (1 + self.establishmentFee))
        data['maxLVR'] = int(self.maxLvr)
        data['maxTopUp'] = LOAN_LIMITS['maxTopUp']
        data['maxCare'] = LOAN_LIMITS['maxCare']
        data['maxReno'] = LOAN_LIMITS['maxReno']
        data['maxRefi'] = int(self.refinanceLimit)
        data['maxGive'] = int(self.giveLimit)
        data['maxTravel'] = int(self.travelLimit)
        data['maxDrawdown'] = int(self.drawdownLimit)
        data['maxDrawdownMonthly'] = int(self.maxDrawdownMonthly)

        response['data'] = data

        return response

    def getStatus(self):
        # Provides detailed array based on primary purposes.
        # Designed to be utilised as user proceeds through the client app
        # Recognises that there can be interdependency between purposes

        # Note complication of establishment fee that reduces the usable loan proceeds
        # The totalLoanAmount is always correct based on % Establishment Fee
        # The available amount is an estimate based on the maximum $ establishment fee
        # (hence doesn't vary with the loan size or cause user confusion)

        # Loan may not be validated
        if self.maxLoan == 0:
            result = self.validateLoan()

        response = {}
        data = {}
        if self.initStatus == False:
            response['status'] = "Error"
            response['responseText'] = "Object not instantiated"
            return response

        self.__calcLVR()

        maxEstablishmentFee = self.loanLimit * (
                self.establishmentFee / (1 + self.establishmentFee))

        purposeAmount = (self.initDict['topUpAmount'] + self.initDict['topUpContingencyAmount'] + self.initDict[
            'topUpDrawdownAmount'] + self.initDict['refinanceAmount'] + self.initDict['giveAmount']
                         + self.initDict['renovateAmount'] + self.initDict['travelAmount'] + self.initDict[
                             'careAmount'] + self.initDict['careDrawdownAmount'])

        totalLoanAmount = purposeAmount * (1 + self.establishmentFee)

        # This is based on total 'plan' amounts

        planPurposeAmount = (self.initDict['topUpAmount'] + self.initDict['topUpContingencyAmount'] + self.initDict[
            'topUpPlanAmount'] + self.initDict['refinanceAmount'] + self.initDict['giveAmount']
                             + self.initDict['renovateAmount'] + self.initDict['travelAmount'] + self.initDict[
                                 'careAmount'] + self.initDict['carePlanAmount'])

        totalPlanAmount = planPurposeAmount * (1 + self.establishmentFee)

        # Available amount always deducts the maximum establishment fee, so need to add back the calculated
        # establishment fee from the total Loan Amount.
        # Reduce by any accrued interest
        availableAmount = round(
            self.loanLimit - totalPlanAmount / (1 + self.establishmentFee) - maxEstablishmentFee - self.initDict[
                'accruedInterest'], 0)

        # Determine if detailed title search required
        detailedTitle = self._chkDetailedTitle(totalPlanAmount)

        # Store primary output
        data['maxLVR'] = round(self.maxLvr, 1)
        data['maxNetLoanAmount'] = int(round(self.loanLimit - maxEstablishmentFee, 0))
        data['maxLoanAmount'] = int(round(self.loanLimit, 0))
        data['availableAmount'] = int(round(availableAmount, 0))

        data['maxDrawdownMonthly'] = int(self.maxDrawdownMonthly)
        data['maxDrawdownAmount'] = int(self.drawdownLimit)

        data['purposeAmount'] = purposeAmount
        data['establishmentFee'] = int(round(purposeAmount * self.establishmentFee, 0))
        data['totalLoanAmount'] = int(round(totalLoanAmount, 0))

        data['planPurposeAmount'] = planPurposeAmount
        data['planEstablishmentFee'] = int(round(planPurposeAmount * self.establishmentFee, 0))
        data['totalPlanAmount'] = int(round(totalPlanAmount, 0))

        data['actualLVR'] = round(totalLoanAmount / self.initDict['valuation'], 1) * 100
        data['maxLVRPercentile'] = int(self.__myround(self.maxLvr, 5))
        data['detailedTitle'] = detailedTitle

        # Validate against limits and add to output dictionary
        data['errors'] = False
        self.__chkStatusItem(data, 'availableStatus', availableAmount, int(0), "LT")
        self.__chkStatusItem(data, 'maxloanAmountStatus', int(round(totalPlanAmount, 0)), self.loanLimit, "GTE")
        self.__chkStatusItem(data, 'topUpStatus',
                             self.initDict['topUpAmount'] + self.initDict['topUpContingencyAmount'] + self.initDict[
                                 'topUpDrawdownAmount'], LOAN_LIMITS['maxTopUp'], "GTE")
        self.__chkStatusItem(data, 'topUpDrawdownStatus',
                             self.initDict['topUpAmount'] + self.initDict['topUpContingencyAmount'] + self.initDict[
                                 'topUpDrawdownAmount'], LOAN_LIMITS['maxTopUp'], "GTE")
        self.__chkStatusItem(data, 'topUpContingencyStatus',
                             self.initDict['topUpAmount'] + self.initDict['topUpDrawdownAmount'] + self.initDict[
                                 'topUpContingencyAmount'], LOAN_LIMITS['maxTopUp'], "GTE")
        self.__chkStatusItem(data, 'refinanceStatus', self.initDict['refinanceAmount'], self.refinanceLimit, "GTE")
        self.__chkStatusItem(data, 'giveStatus', self.initDict['giveAmount'], self.giveLimit, "GTE")
        self.__chkStatusItem(data, 'renovateStatus', self.initDict['renovateAmount'], LOAN_LIMITS['maxReno'], "GTE")
        self.__chkStatusItem(data, 'travelStatus', self.initDict['travelAmount'], self.travelLimit, "GTE")
        self.__chkStatusItem(data, 'careStatus', self.initDict['careAmount'] + self.initDict['careDrawdownAmount'],
                             LOAN_LIMITS['maxCare'], "GTE")
        self.__chkStatusItem(data, 'careDrawdownStatus',
                             self.initDict['careAmount'] + self.initDict['careDrawdownAmount'], LOAN_LIMITS['maxCare'],
                             "GTE")

        if self.productType == productTypesEnum.LUMP_SUM.value:
            self.__chkStatusItem(data, 'minloanAmountStatus', int(round(totalPlanAmount, 0)),
                                 LOAN_LIMITS['minLoanSize'],"LT")
        else:
            self.__chkStatusItem(data, 'minloanAmountStatus', int(round(self.maxDrawdownMonthly, 0)),
                                 LOAN_LIMITS['minIncomeDrawdown'], "LT")

        response['status'] = "Ok"
        response['data'] = data

        return response

    def __chkStatusItem(self, data, label, amount, limit, condition):
        # Utility function to check conditions and create response
        if condition == "LT":
            if amount < limit:
                itemStatus = "Error"
                data["errors"] = True
            else:
                itemStatus = "Ok"
        else:
            if amount > limit:
                itemStatus = "Error"
                data["errors"] = True
            else:
                itemStatus = "Ok"

        data[label] = itemStatus

    def __calcLVR(self):
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
        self.loanLimit = min(int(round(lvr * self.initDict['valuation'], 0)), self.maxLoan)

        # Limits - based actual Lvr adjusted, capped at Loan Limit
        self.refinanceLimit = min(int(lvr * self.initDict['valuation'] * LOAN_LIMITS['maxRefi']), self.loanLimit)
        self.giveLimit = self.loanLimit * LOAN_LIMITS['maxGive']
        self.travelLimit = self.loanLimit * LOAN_LIMITS['maxTravel']

        # TEMPORARY CALCULATION
        # Drawdown Limits - income product
        lvr = 0.08 + (self.clientAge - LOAN_LIMITS['baseLvrAge']) * 0.012
        if self.isApartment:
            lvr = lvr - LOAN_LIMITS['apartmentLvrAdj']
        lvr = lvr * (1 - self.initDict['protectedEquity'] / 100)
        if lvr < 0:
            lvr = 0

        self.drawdownLimit = min(int(round(lvr * self.initDict['valuation'], 0)), self.maxLoan)
        self.maxDrawdownMonthly =  round(((self.drawdownLimit / (10 * 12 ))/(1 + self.establishmentFee)),-1)

        return

    def __valueExists(self, item, sourceDict):
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

    def __myround(self, val, base=5):
        return base * round(val / base)

    def _chkDetailedTitle(self, totalPlanAmount):
        '''Determines whether long-form title required using loan limits'''

        isDetailedTitle = False
        if self.isRefer:
            isDetailedTitle = True
        if totalPlanAmount > self.loanLimit * LOAN_LIMITS['titleUtilTrigger']:
            isDetailedTitle = True
        if totalPlanAmount > LOAN_LIMITS['titleAmountTrigger']:
            isDetailedTitle = True

        return isDetailedTitle
