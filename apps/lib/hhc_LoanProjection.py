"""
Primary projection class - calculates projected loan, home value, home equity values

.. note::
    All projections are based on monthly compounding.
    All rates converted to monthly compounded rates

*Version 2.3*

    * Prior model frequency properly removed
    * Loan equity projections corrected to be monthly based
    * Array data can be produced net or gross of fees (calculator vs client application usage)

*Version 2.2*

    * Updated to reflect contracted and planned drawdowns (monthly or fortnightly - not annual)
    * Input data still serialised
    * Change to Monthly model (frequency fixed)

*Version 2.1*

    * Utility class used to generate a table of loan projections - income, home equity
    * Primary method: getProjections
    * Additional methods return specific analytics
    * Object instantiated with dictionary
    * Consistent with ASIC projections
    * Stress projections can be generated through passing shocks via specified keyword arguments
    * Approach based on array calculation (no analytical solutions) to enable maximum flexibility and transparency
"""


# Python Imports
from math import log

# Local Imports
from apps.lib.site_Enums import loanTypesEnum, incomeFrequencyEnum
from apps.lib.site_Globals import APP_SETTINGS
from apps.lib.site_Globals import LOAN_LIMITS


class LoanProjection():
    """Calculates projected loan, home value, home equity values"""

    minProjectionAge = 90
    minProjectionYears = 10

    minimumDataList = ['loanType',  # Joint or Single
                       'age_1',  # Borrower 1 Age
                       'valuation',  # Initial house price value
                       'totalLoanAmount',  # Initial loan amount
                       'housePriceInflation',
                       'inflationRate',
                       'interestRate',  # Base interest rate
                       'lendingMargin',
                       'maxLoanAmount', #For slider calculations
                       'maxDrawdownMonthly' #For slider calculations
                       ]

    optionalDefaultDict = {
        'interestPayAmount': 0,  # Planned interest payment (monthly)
        'interestPayPeriod': 0,  # Interest payment period (years)

        'topUpIncomeAmount': 0,  # Regular loan drawdown
        'topUpFrequency': 0,
        'topUpPlanDrawdowns': 0,
        'topUpContractDrawdowns': 0,

        'careRegularAmount': 0,
        'careFrequency': 0,
        'carePlanDrawdowns': 0,
        'careContractDrawdowns': 0,

        'topUpContingencyAmount': 0,
        'establishmentFeeRate': LOAN_LIMITS['establishmentFee'],

        'annualPensionIncome': 0,
        'accruedInterest': 0,
    }

    def __init__(self):
        # instance variables

        self.isInit = False
        self.initDict = {}
        self.projectionYears = 15
        self.minAge = 0
        self.totalInterestRate = 0

        # Interest Payment
        self.payIntAmount = 0
        self.payIntPeriod = 0

        # Regular Drawdown
        self.periodDrawdown = 0
        self.drawdownPeriods = 0
        self.totalDrawdownAmount = 0

        self.carePeriodDrawdown = 0
        self.careDrawdownPeriods = 0
        self.careDrawdownAmount = 0

        # Primary Results Array
        self.calcArray = []

    def create(self, initDict):
        """Populate class - check for underspecified initial dictionary"""

        self.isInit = True

        # Check for minimum data
        self.initDict.update(initDict)

        for item in self.minimumDataList:
            if not self.__valueExists(item, self.initDict):
                self.isInit = False
                return {'status': 'Error', 'responseText': 'Missing Data - ' + item}

        # Set defaults for optional items
        for item in self.optionalDefaultDict:
            if not self.__valueExists(item, self.initDict):
                self.initDict[item] = self.optionalDefaultDict[item]

        # Establishment Fee
        self.establishmentFee = self.initDict['establishmentFeeRate']

        # Interest Payment
        if self.initDict['interestPayAmount'] != 0:
            self.payIntAmount = self.initDict['interestPayAmount']  # monthly amount
            self.payIntPeriod = self.initDict['interestPayPeriod'] * 12  # convert to months
        else:
            self.payIntAmount = 0
            self.payIntPeriod = 0

        # Regular Drawdown - Top-Up
        if self.initDict['topUpIncomeAmount'] != 0:
            if initDict['topUpFrequency'] == incomeFrequencyEnum.FORTNIGHTLY.value:
                paymentFreqAdj = 13 / 6
            else:
                paymentFreqAdj = 1

            self.periodDrawdown = self.initDict['topUpIncomeAmount'] * paymentFreqAdj  # Convert to monthly amount
            self.drawdownPeriods = round(self.initDict['topUpPlanDrawdowns'] / paymentFreqAdj,0)  # in months
            self.drawdownContractPeriods = round(self.initDict['topUpContractDrawdowns'] / paymentFreqAdj,0)  # in months


            # calculate drawdown amount with establishment fee for contracted period
            self.totalDrawdownAmount = self.periodDrawdown * self.drawdownContractPeriods \
                                       * (1 + self.establishmentFee)

        # Regular Drawdown - Care
        if self.initDict['careRegularAmount'] != 0:
            if initDict['careFrequency'] == incomeFrequencyEnum.FORTNIGHTLY.value:
                paymentFreqAdj = 13 / 6
            else:
                paymentFreqAdj = 1

            self.carePeriodDrawdown = self.initDict['careRegularAmount'] * paymentFreqAdj  # Convert to monthly amount
            self.careDrawdownPeriods = round(self.initDict['carePlanDrawdowns'] / paymentFreqAdj,0)  # in months
            self.careContractPeriods = round(self.initDict['careContractDrawdowns'] / paymentFreqAdj,0)  # in months

            # calculate drawdown amount with establishment fee for contracted period
            self.careDrawdownAmount = self.carePeriodDrawdown * self.careContractPeriods \
                                      * (1 + self.establishmentFee)

        # Initially Calculated Variables
        if self.initDict['loanType'] == loanTypesEnum.SINGLE_BORROWER.value:
            self.minAge = self.initDict['age_1']
        else:
            if self.__valueExists('age_2', self.initDict):
                self.minAge = min(self.initDict['age_1'], self.initDict['age_2'])
            else:
                self.isInit = False
                return {'status': 'Error', 'responseText': 'Missing Data - age_2'}

        # Projection Years
        projectionAge = max(self.minProjectionAge, self.minAge + self.minProjectionYears)
        self.projectionYears = projectionAge - self.minProjectionYears

        if self.minAge < 75:
            self.asicProjAge1 = self.minAge + 15
        elif self.minAge < 80:
            self.asicProjAge1 = self.minAge + 10
        else:
            self.asicProjAge1 = self.minAge + 5

        self.asicProjAge2 = projectionAge

        # Important! Convert rates to equivalent monthly compounding basis
        self.totalInterestRate = (self.initDict['interestRate'] + self.initDict['lendingMargin']) # Already a monthly rate
        self.inflationRate = self.__simpleCompounding(self.initDict['inflationRate'], 12)
        self.hpiRate = self.__simpleCompounding(self.initDict['housePriceInflation'], 12)

        return {'status': 'Ok'}


    # Public Methods - Projections

    def calcProjections(self, **kwargs):
        """Calculate projection array - primary projection method. Calculation method, results not returned"""

        if not self.isInit:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}


        # Step 1 - Perturb assumptions based on stress parameters passed as keyword arguments

        #(a) Interest Rates - monthly compounded
        intRate = self.totalInterestRate

        if 'intRateStress' in kwargs:
            intRate = (self.initDict['interestRate'] + self.initDict['lendingMargin'] + kwargs['intRateStress'])

        if 'intRateStressLevel' in kwargs:
            intRate = kwargs['intRateStressLevel']

        #(b) House Price Inflation - monthly compounded
        hpi = self.hpiRate

        if 'hpiStress' in kwargs:
            hpi = self.__simpleCompounding(self.initDict['housePriceInflation'] + kwargs['hpiStress'], 12)

        if 'hpiStressLevel' in kwargs:
            hpi = self.__simpleCompounding(kwargs['hpiStressLevel'], 12)

        #(c) Interest payment flag
        if 'makeIntPayment' in kwargs:
            payInterestFlag = int(kwargs['makeIntPayment'])
        else:
            payInterestFlag = 0

        #(d) Inflation rate (used for pension projections)
        #Converted back to an annual rate for specific used in an annual step function in main projection loop
        annualInflationRate = self.__effectiveAnnual(self.inflationRate, 12)


        # Step 2 - Define structure of return array - for explanation

        # The dictionary elements are like columns; and
        # The period index are like rows
        # Monthly projections
        # Nb: project for an extra year for income calculation purposes

        self.calcArray = []

        self.calcArray = [{'BOPAge': 0,
                           'DDLumpSum': 0, 'DDRegular': 0, 'DDFee': 0, 'DDTotal': 0, 'DDIntPay': 0,
                           'BOPLoanValue': 0,
                           'BOPHouseValue': 0, 'BOPHomeEquity': 0, 'BOPHomeEquityPC': 0,
                           'TotalIncome': 0, 'PensionIncome': 0, 'PensionIncomePC': 0,
                           'CumLumpSum': 0, 'CumRegular': 0, 'CumFee': 0, 'CumDrawn': 0, 'CumInt': 0}

                          for periods in range(((self.projectionYears + 1) * 12) + 1)]


        # Step 3 - Initial Period Calculations

        self.calcArray[0]["BOPAge"] = self.minAge

        #(a) Loan Drawdown Amounts
        # Back out contracted drawdown amounts (these are incorporated in future periods)
        # Back out establishment fee
        self.calcArray[0]["DDLumpSum"] = (self.initDict['totalLoanAmount'] - self.totalDrawdownAmount
                                          - self.careDrawdownAmount) / (1 + self.establishmentFee)
        self.calcArray[0]["DDRegular"] = 0
        self.calcArray[0]["DDFee"] = self.calcArray[0]["DDLumpSum"] * self.establishmentFee
        self.calcArray[0]["DDTotal"] = self.calcArray[0]["DDLumpSum"] + self.calcArray[0]["DDRegular"] \
                                       + self.calcArray[0]["DDFee"]
        self.calcArray[0]["DDIntPay"] = 0

        #(b) Loan Balance
        self.calcArray[0]['BOPLoanValue'] = self.calcArray[0]["DDTotal"] + self.initDict['accruedInterest']
        # For variations any accrued interest is included in projections - added to the loan balance and
        # appears as period zero interest owing

        #(c) House Value
        self.calcArray[0]['BOPHouseValue'] = self.initDict['valuation']
        self.calcArray[0]['BOPHomeEquity'] = self.calcArray[0]['BOPHouseValue'] - self.calcArray[0]['BOPLoanValue']
        self.calcArray[0]['BOPHomeEquityPC'] = max(
            1 - self.calcArray[0]['BOPLoanValue'] / self.calcArray[0]['BOPHouseValue'], 0) * 100

        #(d) Income Totals
        self.calcArray[0]["PensionIncome"] = 0
        self.calcArray[0]["TotalIncome"] = 0
        self.calcArray[0]["PensionIncomePC"] = 0

        #(e) Cumulative Totals
        self.calcArray[0]["CumLumpSum"] = self.calcArray[0]["DDLumpSum"]
        self.calcArray[0]["CumRegular"] = self.calcArray[0]["DDRegular"]
        self.calcArray[0]["CumFee"] = self.calcArray[0]["DDFee"]
        self.calcArray[0]["CumDrawn"] = self.calcArray[0]["DDTotal"]
        self.calcArray[0]["CumInt"] = self.calcArray[0]["BOPLoanValue"] - self.calcArray[0]["CumDrawn"]


        # Step 4 - Loop through future periods

        for period in range(1, (self.projectionYears + 1) * 12 + 1):

            self.calcArray[period]["BOPAge"] = self.calcArray[period - 1]["BOPAge"] + 1 / 12

            #(a) Loan Drawdown Amounts

            self.calcArray[period]["DDLumpSum"] = 0

            # ~ Top-Up Drawdown
            if period < self.drawdownPeriods + 1:
                self.calcArray[period]["DDRegular"] = self.periodDrawdown
            else:
                self.calcArray[period]["DDRegular"] = 0

            # ~ Care Drawdown
            if period < self.careDrawdownPeriods + 1:
                self.calcArray[period]["DDRegular"] += self.carePeriodDrawdown

            self.calcArray[period]["DDFee"] = self.calcArray[period]["DDRegular"] * self.establishmentFee

            self.calcArray[period]["DDTotal"] = self.calcArray[period]["DDLumpSum"] + self.calcArray[period][
                "DDRegular"] \
                                                + self.calcArray[period]["DDFee"]

            if period < self.payIntPeriod + 1:
                self.calcArray[period]["DDIntPay"] = self.payIntAmount * payInterestFlag
                # Interest Flag removes interest payment via kwarg scenario
            else:
                self.calcArray[period]["DDIntPay"] = 0

            #(b) Loan Balance

            self.calcArray[period]['BOPLoanValue'] = self.calcArray[period - 1]['BOPLoanValue'] \
                                                     * (1 + intRate / (100 * 12)) \
                                                     - self.calcArray[period]["DDIntPay"] \
                                                     + self.calcArray[period]["DDTotal"]

            #(c) Home Value
            self.calcArray[period]['BOPHouseValue'] = self.calcArray[period - 1]['BOPHouseValue'] \
                                                      * (1 + hpi / (100 * 12))
            self.calcArray[period]['BOPHomeEquity'] = self.calcArray[period]['BOPHouseValue'] - self.calcArray[period][
                'BOPLoanValue']
            self.calcArray[period]['BOPHomeEquityPC'] = max(
                1 - self.calcArray[period]['BOPLoanValue'] / self.calcArray[period]['BOPHouseValue'], 0) * 100

            #(d) Income Totals

            # calculate pension income indexation (note: is annual step function)
            self.calcArray[period]["PensionIncome"] = self.initDict['annualPensionIncome'] / 12 \
                                                      * (1 + annualInflationRate / 100) ** (
                                                          int((period - 1) /12))

            self.calcArray[period]["TotalIncome"] = self.calcArray[period]["PensionIncome"] \
                                                    + self.calcArray[period]["DDRegular"]

            self.calcArray[period]["PensionIncomePC"] = self.__chkDivZero(self.calcArray[period]["PensionIncome"],
                                                                          self.calcArray[period]["TotalIncome"]) \
                                                        * 100 / 12

            #(e) Cumulative Totals
            self.calcArray[period]["CumLumpSum"] = self.calcArray[period - 1]["CumLumpSum"] + self.calcArray[period][
                "DDLumpSum"]
            self.calcArray[period]["CumRegular"] = self.calcArray[period - 1]["CumRegular"] + self.calcArray[period][
                "DDRegular"]
            self.calcArray[period]["CumFee"] = self.calcArray[period - 1]["CumFee"] + self.calcArray[period]["DDFee"]
            self.calcArray[period]["CumDrawn"] = self.calcArray[period - 1]["CumDrawn"] + self.calcArray[period][
                "DDTotal"]
            self.calcArray[period]["CumInt"] = self.calcArray[period]["BOPLoanValue"] - self.calcArray[period][
                "CumDrawn"]

        return {'status': 'Ok'}


    def getProjections(self, **kwargs):
        """Returns full results array """
        if len(self.calcArray) == 0:
            result = self.calcProjections(**kwargs)
            if result['status'] != 'Ok':
                return result

        return {'status': 'Ok', 'data': self.calcArray}


    def getResultsList(self, keyName, **kwargs):
        """Returns results list for keyName
        * standard result points 0, 5, 10 and 15 years
        * primarily for used to pass to templates in Django views
        * optionally calculates scaling for images
         """
        if len(self.calcArray) == 0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}

        scaleList = []

        if 'Income' in keyName:
            # Flow variables (next 12 months)
            figuresList = []
            for period in [0, 5, 10, 15]:
                income = 0
                for subPeriod in range(12):
                    income += self.calcArray[(period * 12) + subPeriod + 1][keyName]

                figuresList.append(int(round(income, 0)))
        else:
            # Stock variables (point in time)
            figuresList = [int(round(self.calcArray[i * 12][keyName], 0)) for i in [0, 5, 10, 15]]

        if 'imageSize' in kwargs:
            if kwargs['imageMethod'] == 'exp':
                # Use a log scaling method for images (arbitrary)
                maxValueLog = self.__logOrZero(max(figuresList)) ** 3
                if maxValueLog == 0:
                    maxValueLog = 1
                scaleList = [int(self.__logOrZero(figuresList[i]) ** 3 / maxValueLog * kwargs['imageSize']) for i
                             in range(4)]
            elif kwargs['imageMethod'] == 'lin':
                maxValueLog = max(figuresList)
                scaleList = [int(figuresList[i] / maxValueLog * kwargs['imageSize']) for i in range(4)]

        return {'status': 'Ok', 'data': figuresList + scaleList}


    def getPeriodResults(self, period, **kwargs):
        """Returns results for specific period"""

        if len(self.calcArray) == 0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}

        results = self.calcArray[period * 12]
        results['HomeEquityPercentile'] = str(int(self.__myround(results['BOPHomeEquityPC'], 5)))

        return self.calcArray[period * 12]

    def getAsicProjectionPeriods(self):
        """Returns two point ASIC projection ages"""
        return self.asicProjAge1 - self.minAge, self.asicProjAge2 - self.minAge


    def getImageList(self, keyName, imageURL):
        """Returns populated image list for specific keyName"""

        if len(self.calcArray) == 0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}

        figuresList = self.getResultsList(keyName)['data']
        imageList = [imageURL.replace('{0}', str(int(self.__myround(figuresList[i], 5)))) for i in range(4)]

        return {'status': 'Ok', 'data': imageList}


    def getFutureEquityArray(self, projectionYears=15, increment=1000, netOfFee=False):
        """
        Returns loan and projected equity combinations (for slider) for:
        - specified (default) projection period (in years); and
        - for intervals of drawdown (minimum amount to maximum amount) in increments of 'increment' (default)
        Assumes establishment fee included in the loan amount
        Rates and calculations monthly compounded

        args:
        - projectionYears: terminal year that results are calculate for
        - increment: step size between each slider value (i.e., we set increments and calculate the number of intervals)
        - netOfFee: interval amounts based on 'purpose amounts' (amounts paid to client) instead of 'total loan' amounts (calculator)
        """

        if increment < 100:
            increment = 100

        if netOfFee:
            maxLoanAmount = self.initDict['maxLoanAmount'] /  (1 + self.establishmentFee)
        else:
            maxLoanAmount = self.initDict['maxLoanAmount']

        if self.isInit:
            dataArray = []
            intervals = int(maxLoanAmount / increment) + 1
            intervalCount = -1

            homeValue = self.initDict['valuation'] * ((1 + self.hpiRate / 1200) ** (projectionYears*12))

            for item in range(intervals + 1):
                if item == intervals:
                    loanAmount = maxLoanAmount
                else:
                    loanAmount = round((item * increment), 0)

                if (loanAmount == 0) or (loanAmount >= LOAN_LIMITS['minLoanSize']):
                    intervalCount += 1

                    loanBalance = loanAmount * ((1 + self.totalInterestRate / 1200) ** (projectionYears*12))

                    # Add interest if input is before fees
                    if netOfFee:
                        loanBalance = loanBalance * (1 + self.establishmentFee)

                    projectedEquity = homeValue - loanBalance

                    dataArray.append({'item': item,
                                      "loanAmount": round(loanAmount,0),
                                      "loanPercentile": int(
                                          self.__myround(loanAmount / self.initDict['valuation'] * 100)),
                                      "futLoanBalance": round(loanBalance,0),
                                      "futHomeEquity": int(round(projectedEquity, 0)),
                                      "futHomeEquityPC": int(round(projectedEquity / homeValue * 100, 0)),
                                      "percentile": int(self.__myround(projectedEquity / homeValue * 100))
                                      })

            return {'status': 'Ok',
                    'data': {"intervals": intervalCount, "futHomeValue": int(round(homeValue,0)), "dataArray": dataArray}}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}


    def getFutureIncomeEquityArray(self, projectionYears=10, increment=20, lumpSumComponent = 0, netOfFee = False):
        """
        Returns loan and projected equity combinations (for slider) for:
        - specified (default) projection period (in years); and
        - for intervals of income drawdown (minimumn amount to maximum amount) in increments of 'increment' (default)
        - adjusting maximum amount by lumpSumComponent
        Assumes establishment fee included in the drawdown amount
        Rates and calculations monthly compounded

        args:
        - projectionYears: terminal year that results are calculate for
        - increment: step size between each slider value (i.e., we set increments and calculate the number of intervals)
        - lumSumComponent: used to reduce the maxLoanAmount if some of this has already been allocated
        - netOfFee: interval amounts based on 'purpose amounts' (amounts paid to client) instead of 'total loan' amounts (calculator)
        """

        if increment < 10:
            increment = 10

        if netOfFee:
            maxDrawdownMonthly = self.initDict['maxDrawdownMonthly'] /  (1 + self.establishmentFee)
        else:
            maxDrawdownMonthly = self.initDict['maxDrawdownMonthly']

        #Optional reduction for lump sum
        if lumpSumComponent > 0:
            maxDrawdownMonthly -= lumpSumComponent / (10 * 12) # based on 10 year monthly draw assumption
            if maxDrawdownMonthly < 0:
                maxDrawdownMonthly = 0

        if self.initDict['topUpFrequency'] == incomeFrequencyEnum.FORTNIGHTLY.value:
            paymentFreqAdj = 13 / 6
        else:
            paymentFreqAdj = 1

        if self.isInit:
            # Model monthly and adjust for payment frequency
            dataArray = []
            intervals = int(maxDrawdownMonthly / increment) + 1
            intervalCount = -1

            planYears = min(self.drawdownPeriods / 12, projectionYears)
            residualYears = projectionYears - planYears

            homeValue = (self.initDict['valuation'] * (1 + self.hpiRate / 1200) ** (projectionYears*12))

            for item in range(intervals + 1):
                if item == intervals:
                    loanAmount = maxDrawdownMonthly
                else:
                    loanAmount = round((item * increment), -1)

                if (loanAmount == 0) or (loanAmount >= LOAN_LIMITS['minIncomeDrawdown']):
                    # Future value annuity formula for drawdown plan years
                    intervalCount += 1

                    loanBalance = loanAmount * \
                                  ((((1+self.totalInterestRate/1200) ** (planYears * 12)) - 1) / (self.totalInterestRate/1200))

                    # Add interest if input is before fees
                    if netOfFee:
                        loanBalance = loanBalance * (1 + self.establishmentFee)

                    # Compound the loan for residual years
                    loanBalance = loanBalance * ((1+self.totalInterestRate/1200) ** (residualYears*12))

                    # Add any lump sum component
                    additionalAmount =  lumpSumComponent * (1 + self.totalInterestRate / 1200) ** (projectionYears * 12)
                    if netOfFee:
                        additionalAmount = additionalAmount * (1 + self.establishmentFee)

                    loanBalance += additionalAmount

                    projectedEquity = homeValue - loanBalance

                    dataArray.append({'item': item,
                                      "loanAmount": round((loanAmount/paymentFreqAdj),-1),
                                      "loanPercentile": int(self.__myround(loanAmount / self.initDict['valuation'] * 100)),
                                      "futLoanBalance": int(round(loanBalance,0)),
                                      "futHomeEquity": int(round(projectedEquity, 0)),
                                      "futHomeEquityPC": int(round(projectedEquity / homeValue * 100, 0)),
                                      "percentile": int(self.__myround(projectedEquity / homeValue * 100))
                                      })

            return {'status': 'Ok',
                    'data': {"intervals": intervalCount, "futHomeValue": int(round(homeValue,0)), "dataArray": dataArray}}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}


    # INTERNAL METHODS

    def __myround(self, val, base=5):
        if val == 100:
            return 100
        else:
            #Floor of 2% for graph purposes
            return min(base * round(val / base), 98)

    def __logOrZero(self, val):
        if val <= 0:
            return 0
        return log(val)

    def __effectiveAnnual(self, rate, compounding):
        return (((1 + rate / (compounding * 100)) ** compounding) - 1) * 100

    def __simpleCompounding(self, rate, compounding):
        return (((1 + rate / 100) ** (1 / compounding)) - 1) * compounding * 100

    def __chkDivZero(self, numerator, divisor):
        if divisor == 0:
            return 0
        else:
            return numerator / divisor

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
