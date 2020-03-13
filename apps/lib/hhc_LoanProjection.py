#Python Imports
from math import log

#Local Imports
from apps.lib.site_Enums import loanTypesEnum, incomeFrequencyEnum
from apps.lib.site_Globals import APP_SETTINGS
from apps.lib.site_Globals import LOAN_LIMITS



class LoanProjection():

    # -- VERSION 2.1 --
    # -- MONTHLY CALCULATIONS --
    # -- ADDITIONAL DISCLOSURES --

    # Utility class used to generate a table of loan projections - income, home equity
    # Primary method: getProjections
    # Additional methods return specific analytics
    # Object instantiated with dictionary
    # Consistent with ASIC projections
    # Stress projections can be generated through passing shocks via specified keyword arguments
    # Approach based on array calculation (no analytical solutions) to enable maximum flexibility and transparency


    # Class variables

    minProjectionAge = 90
    minProjectionYears = 10

    minimumDataList = ['loanType',                  # Joint or Single
                       'age_1',                     # Borrower 1 Age
                       'valuation',                  # Initial house price value
                       'totalLoanAmount',           # Initial loan amount
                       'housePriceInflation',
                       'inflationRate',
                       'interestRate',              # Base interest rate
                       'lendingMargin',
                       'maxLoanAmount']


    optionalDataDict = {'interestPayAmount':0,           # Planned interest payment (monthly)
                        'interestPayPeriod':0,           # Interest payment period (years)
                        'topUpIncomeAmount':0,          # Regular loan drawdown
                        'topUpFrequency':0,
                        'topUpPeriod':0,                # Planned drawdown period (years)
                        'topUpBuffer':0,
                        'careRegularAmount':0,
                        'careFrequency':0,
                        'carePeriod':0,
                        'topUpContingencyAmount':0,
                        'establishmentFee': 0,
                        }

    incomeDefaultDict = {'inflationAdj':True,
                         'maxNetLoanAmount':0,       # Maximum loan (used for maximum income calcs)
                         'superAmount':0,
                         'annualPensionIncome':0,
                         'topUpAmount':0,
                         'projectionAge':90}


    def __init__(self):
        #instance variables

        self.isInit = False
        self.initDict = {}
        self.FREQUENCY = 12  # 12 = Monthly modelling, 1 = Annual Modelling

        self.projectionYears = 15

        self.payIntAmount = 0
        self.payIntPeriod = 0

        self.periodDrawdown=0
        self.drawdownPeriods=0
        self.totalDrawdownAmount=0

        self.carePeriodDrawdown=0
        self.careDrawdownPeriods=0
        self.careDrawdownAmount=0

        #Income variables
        self.minAge=0
        self.incomeProjYears=0
        self.totalInterestRate=0
        self.currentSuperIncome=0
        self.topUpIncome=0

        # Primary Results Array
        self.calcArray=[]

    def create(self, initDict, frequency=12):

        self.isInit=True
        self.FREQUENCY=frequency

        # Check for minimum data
        self.initDict.update(initDict)

        for item in self.minimumDataList:
            if not self.__valueExists(item, self.initDict):
                self.isInit = False
                return {'status': 'Error','responseText':'Missing Data - '+item}

        #Check for establishment fee override
        self.establishmentFee = LOAN_LIMITS['establishmentFee']
        if self.__valueExists('establishmentFeeRate',self.optionalDataDict):
            self.establishmentFee = self.optionalDataDict['establishmentFeeRate']

        # Set defaults for optional items
        for item in self.optionalDataDict:
            if not self.__valueExists(item, self.initDict):
                self.initDict[item] = self.optionalDataDict[item]

        # Interest Payment
        if self.initDict['interestPayAmount']!=0:
            self.payIntAmount=self.initDict['interestPayAmount']*12/self.FREQUENCY
            self.payIntPeriod=self.initDict['interestPayPeriod']*self.FREQUENCY
        else:
            self.payIntAmount=0
            self.payIntPeriod=0

        # Regular Drawdown
        if self.initDict['topUpIncomeAmount'] != 0:
            if initDict['topUpFrequency']==incomeFrequencyEnum.FORTNIGHTLY.value:
                freqAdj = 13/6
            else:
                freqAdj = 1

            self.periodDrawdown= self.initDict['topUpIncomeAmount'] *12 / self.FREQUENCY*freqAdj
            self.drawdownPeriods=self.initDict['topUpPeriod']*self.FREQUENCY
            #calculated drawdown amount with establishment fee - 12 months
            self.totalDrawdownAmount = self.periodDrawdown  * self.FREQUENCY * (1 + self.establishmentFee)

        # Regular Drawdown - Care
        if self.initDict['careRegularAmount'] != 0:
            if initDict['careFrequency'] == incomeFrequencyEnum.FORTNIGHTLY.value:
                freqAdj = 13 /6
            else:
                freqAdj = 1

            self.carePeriodDrawdown = self.initDict['careRegularAmount'] * 12 / self.FREQUENCY * freqAdj
            self.careDrawdownPeriods = self.initDict['carePeriod'] * self.FREQUENCY
            # calculated drawdown amount with establishment fee - 12 months
            self.careDrawdownAmount = self.carePeriodDrawdown * self.FREQUENCY * (1 + self.establishmentFee)

        # Initially Calculated Variables
        if self.initDict['loanType']==loanTypesEnum.SINGLE_BORROWER.value:
            self.minAge=self.initDict['age_1']
        else:
            if self.__valueExists('age_2', self.initDict):
                self.minAge = min(self.initDict['age_1'], self.initDict['age_2'])
            else:
                self.isInit = False
                return {'status': 'Error','responseText':'Missing Data - age_2'}

        #Projection Years
        projectionAge = max(self.minProjectionAge,self.minAge + self.minProjectionYears)
        self.projectionYears = projectionAge - self.minProjectionYears

        if self.minAge < 75:
            self.asicProjAge1 = self.minAge + 15
        elif self.minAge < 80:
            self.asicProjAge1 = self.minAge + 10
        else:
            self.asicProjAge1 = self.minAge + 5

        self.asicProjAge2 = projectionAge

        # Important! 
        # Convert rates to equivalent compounding basis
        self.totalInterestRate   = self.__effectiveAnnual(self.initDict['interestRate'] + self.initDict['lendingMargin'],12/self.FREQUENCY) # Simple monthly rate
        self.inflationRate       = self.__simpleCompounding(self.initDict['inflationRate'],self.FREQUENCY)
        self.hpiRate             = self.__simpleCompounding(self.initDict['housePriceInflation'],self.FREQUENCY)


        for item in self.incomeDefaultDict:
            if not self.__valueExists(item, self.initDict):
                self.initDict[item] = self.incomeDefaultDict[item]

        return {'status':'Ok'}


    # Public Methods - Projections

    # Primary Projecton Method
    def calcProjections(self,**kwargs):
        if not self.isInit:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

        # Perturb assumptions based on stress parameters passed as keyword arguments

        intRate=self.totalInterestRate
        annualInflationRate=self.__effectiveAnnual(self.inflationRate,self.FREQUENCY)

        if 'intRateStress' in kwargs:
            intRate =  self.__effectiveAnnual(self.initDict['interestRate'] + self.initDict['lendingMargin'] + kwargs['intRateStress'],12/self.FREQUENCY)

        if 'intRateStressLevel' in kwargs:
            intRate = self.__effectiveAnnual(kwargs['intRateStressLevel'],12/self.FREQUENCY)

        hpi=self.hpiRate

        if 'hpiStress' in kwargs:
            hpi=self.__simpleCompounding(self.initDict['housePriceInflation']+kwargs['hpiStress'],self.FREQUENCY)

        if 'hpiStressLevel' in kwargs:
            hpi = self.__simpleCompounding(kwargs['hpiStressLevel'],self.FREQUENCY)

        if 'makeIntPayment' in kwargs:
            payInterestFlag = int(kwargs['makeIntPayment'])
        else:
            payInterestFlag = 0

        # Define structure of the return array
        # - the dictionary elements are like columns; and
        # - the period index are like rows
        # List comprehension to replicate the dictionary for the required number of periods
        # Project for an extra year for income calculation purposes

        self.calcArray = []

        self.calcArray = [{'BOPAge': 0,
                           'DDLumpSum':0, 'DDRegular':0, 'DDFee':0, 'DDTotal':0, 'DDIntPay':0,
                           'BOPLoanValue':0,
                           'BOPHouseValue':0, 'BOPHomeEquity':0, 'BOPHomeEquityPC':0,
                           'TotalIncome':0, 'PensionIncome':0, 'PensionIncomePC':0,
                           'CumLumpSum':0, 'CumRegular':0, 'CumFee':0, 'CumDrawn':0, 'CumInt':0}
                          for periods in range(((self.projectionYears + 1 ) * self.FREQUENCY) + 1)]


        # Initial Period Calculations

        self.calcArray[0]["BOPAge"] = self.minAge

        ## Loan Drawdown Amounts
        self.calcArray[0]["DDLumpSum"] = (self.initDict['totalLoanAmount'] - self.totalDrawdownAmount
                                          - self.careDrawdownAmount) / (1 + self.establishmentFee)
            # Back out first year drawdown amounts (these are incorporated in future periods)
            # Back out establishment fee

        self.calcArray[0]["DDRegular"] = 0
        self.calcArray[0]["DDFee"] = self.calcArray[0]["DDLumpSum"] * self.establishmentFee
        self.calcArray[0]["DDTotal"] = self.calcArray[0]["DDLumpSum"] + self.calcArray[0]["DDRegular"] \
                                       + self.calcArray[0]["DDFee"]
        self.calcArray[0]["DDIntPay"] = 0

        ## Loan Balance

        self.calcArray[0]['BOPLoanValue'] = self.calcArray[0]["DDTotal"]

        ## House Value
        self.calcArray[0]['BOPHouseValue']=self.initDict['valuation']
        self.calcArray[0]['BOPHomeEquity'] = self.calcArray[0]['BOPHouseValue'] - self.calcArray[0]['BOPLoanValue']
        self.calcArray[0]['BOPHomeEquityPC'] = max(1 - self.calcArray[0]['BOPLoanValue'] / self.calcArray[0]['BOPHouseValue'], 0) * 100

        ## Income Totals
        self.calcArray[0]["PensionIncome"] = 0
        self.calcArray[0]["TotalIncome"] = 0
        self.calcArray[0]["PensionIncomePC"] = 0

        ## Cumulative Totals
        self.calcArray[0]["CumLumpSum"] = self.calcArray[0]["DDLumpSum"]
        self.calcArray[0]["CumRegular"] = self.calcArray[0]["DDRegular"]
        self.calcArray[0]["CumFee"] = self.calcArray[0]["DDFee"]
        self.calcArray[0]["CumDrawn"] = self.calcArray[0]["DDTotal"]
        self.calcArray[0]["CumInt"] = self.calcArray[0]["DDIntPay"]


        # Loop through future periods

        for period in range(1,(self.projectionYears +1) * self.FREQUENCY+1):

            self.calcArray[period]["BOPAge"] = self.calcArray[period - 1]["BOPAge"] + 1 / self.FREQUENCY

            ## Loan Drawdown Amounts

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

            self.calcArray[period]["DDTotal"] = self.calcArray[period]["DDLumpSum"] + self.calcArray[period]["DDRegular"] \
                                           + self.calcArray[period]["DDFee"]

            if period < self.payIntPeriod + 1:
                self.calcArray[period]["DDIntPay"] = self.payIntAmount * payInterestFlag
                # Interest Flag removes interest payment via kwarg scenario
            else:
                self.calcArray[period]["DDIntPay"] = 0

            ## Loan Balance

            self.calcArray[period]['BOPLoanValue'] = self.calcArray[period - 1]['BOPLoanValue'] * (1 + intRate / (100 * self.FREQUENCY)) \
                                                     - self.calcArray[period]["DDIntPay"] \
                                                     + self.calcArray[period]["DDTotal"]

            #Home Value
            self.calcArray[period]['BOPHouseValue'] = self.calcArray[period-1]['BOPHouseValue']*(1 + hpi/(100* self.FREQUENCY))
            self.calcArray[period]['BOPHomeEquity']=self.calcArray[period]['BOPHouseValue']-self.calcArray[period]['BOPLoanValue']
            self.calcArray[period]['BOPHomeEquityPC'] = max(1 - self.calcArray[period]['BOPLoanValue'] / self.calcArray[period]['BOPHouseValue'], 0)*100


            ## Income Totals

            self.calcArray[period]["PensionIncome"] = self.initDict['annualPensionIncome']/self.FREQUENCY  \
                                                          * (1 + annualInflationRate/100)**(int((period-1)/self.FREQUENCY))
                                                          # calculate pension income indexation

            self.calcArray[period]["TotalIncome"] = self.calcArray[period]["PensionIncome"] \
                                                        + self.calcArray[period]["DDRegular"]

            self.calcArray[period]["PensionIncomePC"] = self.__chkDivZero(self.calcArray[period]["PensionIncome"],
                                                                              self.calcArray[period]["TotalIncome"]) * 100 \
                                                                            / self.FREQUENCY

            ## Cumulative Totals
            self.calcArray[period]["CumLumpSum"] = self.calcArray[period-1]["CumLumpSum"] + self.calcArray[period]["DDLumpSum"]
            self.calcArray[period]["CumRegular"] = self.calcArray[period-1]["CumRegular"] + self.calcArray[period]["DDRegular"]
            self.calcArray[period]["CumFee"] = self.calcArray[period-1]["CumFee"] + self.calcArray[period]["DDFee"]
            self.calcArray[period]["CumDrawn"] = self.calcArray[period-1]["CumDrawn"] + self.calcArray[period]["DDTotal"]
            self.calcArray[period]["CumInt"] = self.calcArray[period]["BOPLoanValue"] - self.calcArray[period]["CumDrawn"]

        return {'status': 'Ok'}


    def getProjections(self,**kwargs):
        if len(self.calcArray)==0:
            result=self.calcProjections(**kwargs)
            if result['status']!='Ok':
                return result

        return {'status': 'Ok', 'data': self.calcArray}

    def getResultsList(self, keyName, **kwargs):
        # Builds a results list to pass to the template
        # Optionally calculates scaling for images
        if len(self.calcArray)==0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}

        scaleList = []

        if 'Income' in keyName:
            #Flow variables (next 12 months)
            figuresList=[]
            for period in [0, 5, 10, 15]:
                income=0
                for subPeriod in range(self.FREQUENCY):
                    income += self.calcArray[(period*self.FREQUENCY)+subPeriod+1][keyName]

                figuresList.append(int(round(income,0)))
        else:
            # Stock variables (point in time)
            figuresList = [int(round(self.calcArray[i * self.FREQUENCY][keyName],0)) for i in [0, 5, 10, 15]]

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
        # Returns results for specific period
        if len(self.calcArray)==0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}

        results = self.calcArray[period * self.FREQUENCY]
        results['HomeEquityPercentile'] = str(int(self.__myround(results['BOPHomeEquityPC'],5)))

        return self.calcArray[period * self.FREQUENCY]


    def getAsicProjectionPeriods(self):
        return self.asicProjAge1 -  self.minAge ,self.asicProjAge2 - self.minAge


    def getImageList(self, keyName, imageURL):
        if len(self.calcArray)==0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}

        figuresList=self.getResultsList(keyName)['data']
        imageList = [imageURL.replace('{0}', str(int(self.__myround(figuresList[i],5)))) for i in range(4)]

        return {'status': 'Ok', 'data': imageList}

    def getNegativeEquityAge(self):
        if self.isInit:
            return {'status': 'Ok', 'data': self.__calcNegAge}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getFutureEquityArray(self, projectionYears=15, increment=1000):
        # Returns loan / projected equity combinations (for slider)
        if increment<100:
            increment=100

        if self.isInit:
            dataArray = []
            intervals=int(self.initDict['maxLoanAmount']/ increment)+1

            homeValue = (self.initDict['valuation'] * (1 + self.hpiRate / 100) ** projectionYears)

            for item in range(intervals + 1):
                if item == intervals:
                    loanAmount = self.initDict['maxLoanAmount']
                else:
                    loanAmount = round((item * increment), 0)


                loanBalance = loanAmount * (1 + self.totalInterestRate / 100) ** projectionYears
                projectedEquity = homeValue-loanBalance

                dataArray.append({ 'item':item,
                                   "loanAmount":int(loanAmount),
                                   "loanPercentile": int(self.__myround(loanAmount/self.initDict['valuation']* 100)),
                                   "futLoanBalance": int(loanBalance),
                                   "futHomeEquity": int(round(projectedEquity, 0)),
                                   "futHomeEquityPC": int(round(projectedEquity/homeValue*100,0)),
                                   "percentile": int(self.__myround(projectedEquity/homeValue*100))
                                    })

            return {'status': 'Ok', 'data': {"intervals":intervals, "futHomeValue":int(homeValue),"dataArray":dataArray}}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    # INTERNAL METHODS
    def __myround(self, val, base=5):
        return base * round(val / base)

    def __logOrZero(self, val):
        if val <= 0:
            return 0
        return log(val)
 
    def __calcNegAge(self):
        periods=log(1/(self.initDict['totalLoanAmount']/self.initDict['valuation']))/log((1+self.totalInterestRate/(100* self.FREQUENCY))/(1 + self.hpiRate/(100* self.FREQUENCY)))
        return self.minAge + int(periods/self.FREQUENCY)

    def __effectiveAnnual(self, rate, compounding):
        return (((1 + rate/(compounding * 100)) ** compounding)-1)*100

    def __simpleCompounding(self,rate,compounding):
        return (((1+rate/100)**(1/compounding))-1)*compounding*100

    def __chkDivZero(self,numerator, divisor):
        if divisor==0:
            return 0
        else:
            return numerator/divisor

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
