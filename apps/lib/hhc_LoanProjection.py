#Python Imports
from math import log

#Local Imports
from apps.lib.site_Enums import loanTypesEnum, incomeFrequencyEnum
from apps.lib.site_Globals import APP_SETTINGS
from apps.lib.site_Globals import LOAN_LIMITS



class LoanProjection():

    # -- VERSION 2.0 --
    # -- MONTHLY CALCULATIONS --

    # Utility class used to generate a table of loan projections - superannuation, income, home equity
    # Primary method: getProjections
    # Additional methods return specific analytics
    # Object instantiated with dictionary
    # Consistent with ASIC projections
    # Stress projections can be generated through passing shocks via specified keyword arguments
    # Approach based on array calculation (no analytical solutions) to enable maximum flexibility and repeatability


    # Class variables

    minProjectionYears=APP_SETTINGS['minProjectionYears']

    minimumDataList = ['loanType',                  # Joint or Single
                       'age_1',                     # Borrower 1 Age
                       'valuation',                  # Initial house price value
                       'totalLoanAmount',           # Initial loan amount
                       'housePriceInflation',
                       'inflationRate',
                       'interestRate',              # Base interest rate
                       'lendingMargin',
                       'investmentRate',
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
                        'topUpContingencyAmount':0
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
        self.isVersion1 = False
        self.initDict = {}
        self.FREQUENCY = 12  # 12 = Monthly modelling, 1 = Annual Modelling

        self.payIntAmount = 0
        self.payIntPeriod = 0

        self.periodDrawdown=0
        self.drawdownPeriods=0
        self.totalDrawdownAmount=0

        self.carePeriodDrawdown=0
        self.careDrawdownPeriods=0
        self.careDrawdownAmount=0

        self.establishmentFee= LOAN_LIMITS['establishmentFee']

        #Income variables
        self.minAge=0
        self.incomeProjYears=0
        self.totalInterestRate=0
        self.currentSuperIncome=0
        self.topUpIncome=0

        # Primary Results Array
        self.calcArray=[]

    def create(self, initDict, isVersion1=False, frequency=12):

        self.isInit=True
        self.isVersion1=isVersion1
        self.FREQUENCY=frequency

        # Check for minimum data
        self.initDict.update(initDict)

        for item in self.minimumDataList:
            if not self.__valueExists(item, self.initDict):
                self.isInit = False
                return {'status': 'Error','responseText':'Missing Data - '+item}

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
                freqAdj=2
            else:
                freqAdj = 1

            self.periodDrawdown= self.initDict['topUpIncomeAmount'] *12 / self.FREQUENCY*freqAdj
            self.drawdownPeriods=self.initDict['topUpPeriod']*self.FREQUENCY
            #calculated drawdown amount with establishment fee - 12 months
            self.totalDrawdownAmount = self.periodDrawdown  * self.FREQUENCY * (1 + self.establishmentFee)

        # Regular Drawdown - Care
        if self.initDict['careRegularAmount'] != 0:
            if initDict['careFrequency'] == incomeFrequencyEnum.FORTNIGHTLY.value:
                freqAdj = 2
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

        # Important! 
        # Convert rates to equivalent compounding basis
        self.totalInterestRate   = self.__effectiveAnnual(self.initDict['interestRate'] + self.initDict['lendingMargin'],12/self.FREQUENCY) # Simple monthly rate
        self.inflationRate       = self.__simpleCompounding(self.initDict['inflationRate'],self.FREQUENCY)
        self.investmentRate      = self.__simpleCompounding(self.initDict['investmentRate'],self.FREQUENCY)
        self.hpiRate             = self.__simpleCompounding(self.initDict['housePriceInflation'],self.FREQUENCY)


        for item in self.incomeDefaultDict:
            if not self.__valueExists(item, self.initDict):
                self.initDict[item] = self.incomeDefaultDict[item]


        # Version1 related items
        if isVersion1:

            #Set income projection period (minimum 5 years)
            #Note this will be different than the required Loan/House projection period (15 years)
            self.incomeProjYears = self.initDict['projectionAge'] - self.minAge
            if self.incomeProjYears < 5:
                self.incomeProjYears=5

            # Calculate initial income amounts
            self.currentSuperIncome = self.__calcDrawdown(self.initDict['superAmount'])
            self.topUpIncome = self.__enhancedSuperIncome(self.initDict['topUpAmount'])


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

        if self.isVersion1:   # <-- VERSION 1 -->

            superIncome = self.topUpIncome

            self.calcArray=[{"BOPAge":0,"BOPSuperBalance":0,"SuperDrawdown":0,"Return":0,"EOPSuperBalance":0,'PensionIncome':0,
                        'TotalIncome':0,'PensionIncomePC':0,'CumulativeSuperIncome':0,'BOPHouseValue':0,
                        'BOPLoanValue':0,'BOPHomeEquity':0,'BOPHomeEquityPC':0}
                            for periods in range(((self.minProjectionYears+1) * self.FREQUENCY )+1)]

        else:
            self.calcArray = [{"BOPAge": 0, 'BOPHouseValue': 0,
                               'BOPLoanValue': 0, 'BOPHomeEquity': 0, 'BOPHomeEquityPC': 0,
                               'TotalIncome':0,'PensionIncome':0, 'PensionIncomePC':0}
                                    for periods in range(((self.minProjectionYears+1) * self.FREQUENCY) + 1)]

        #Initial Period
        self.calcArray[0]["BOPAge"] = self.minAge

        # Loan Value
        self.calcArray[0]["InterestPayment"] = 0
        self.calcArray[0]["LoanDrawdown"] = 0
        self.calcArray[0]['BOPLoanValue'] = self.initDict['totalLoanAmount'] - self.totalDrawdownAmount - self.careDrawdownAmount
        # Back out first year drawdown amounts (these are incorporated in future periods)

        if self.isVersion1:   # <-- VERSION 1 -->
            self.calcArray[0]["BOPSuperBalance"]=self.initDict['superAmount']+self.initDict['topUpAmount']
            self.calcArray[0]["SuperDrawdown"]=superIncome/self.FREQUENCY
            # Note: Return applied to average balance (assuming drawdown of income evenly over period)
            self.calcArray[0]["Return"]= (self.calcArray[0]["BOPSuperBalance"]-self.calcArray[0]["SuperDrawdown"]/2) * self.investmentRate/(100* self.FREQUENCY)
            self.calcArray[0]["EOPSuperBalance"]= self.calcArray[0]["BOPSuperBalance"] - self.calcArray[0]["SuperDrawdown"] + self.calcArray[0]["Return"]

            self.calcArray[0]["PensionIncome"]=self.initDict['annualPensionIncome']/self.FREQUENCY
            self.calcArray[0]["TotalIncome"]=self.calcArray[0]["SuperDrawdown"]+self.calcArray[0]["PensionIncome"]
            self.calcArray[0]["PensionIncomePC"] = self.__chkDivZero(self.calcArray[0]["PensionIncome"],self.calcArray[0]["TotalIncome"])*100
            self.calcArray[0]['CumulativeSuperIncome']=self.calcArray[0]["SuperDrawdown"]
        else:
            self.calcArray[0]["PensionIncome"]= 0
            self.calcArray[0]["TotalIncome"] = 0
            self.calcArray[0]["PensionIncomePC"] = 0


        # Home Value
        self.calcArray[0]['BOPHouseValue']=self.initDict['valuation']
        self.calcArray[0]['BOPHomeEquity'] = self.calcArray[0]['BOPHouseValue'] - self.calcArray[0]['BOPLoanValue']
        self.calcArray[0]['BOPHomeEquityPC'] = max(1 - self.calcArray[0]['BOPLoanValue'] / self.calcArray[0]['BOPHouseValue'], 0) * 100


        # Loop through future periods
        for period in range(1,(self.minProjectionYears+1) * self.FREQUENCY+1):

            # Loan Value
            if period < self.payIntPeriod + 1:
                self.calcArray[period]["InterestPayment"] = self.payIntAmount * payInterestFlag
                # Interest Flag removes interest payment via kwarg scenario
            else:
                self.calcArray[period]["InterestPayment"] = 0

            # ~ Top-Up Drawdown
            if period < self.drawdownPeriods + 1:
                self.calcArray[period]["LoanDrawdown"] = self.periodDrawdown  # No indexation, no establishment fee (below)
            else:
                self.calcArray[period]["LoanDrawdown"] = 0

            # ~ Care Drawdown
            if period < self.careDrawdownPeriods + 1:
                self.calcArray[period]["LoanDrawdown"] += self.carePeriodDrawdown  # No indexation, no establishment fee (below)

            self.calcArray[period]['BOPLoanValue'] = self.calcArray[period - 1]['BOPLoanValue'] * (1 + intRate / (100 * self.FREQUENCY)) \
                                                     - self.calcArray[period]["InterestPayment"] \
                                                     + (self.calcArray[period]["LoanDrawdown"] * (1 + self.establishmentFee))

            if self.isVersion1:  # <-- VERSION 1 -->
                # Income Calculations
                self.calcArray[period]["BOPSuperBalance"] = self.calcArray[period-1]["EOPSuperBalance"]

                # If starting balance == 0, no drawdown
                if self.calcArray[period]["BOPSuperBalance"]>0:
                    if self.initDict['inflationAdj']:
                        self.calcArray[period]["SuperDrawdown"] = self.calcArray[period-1]["SuperDrawdown"] * (1 + self.inflationRate/(100* self.FREQUENCY))
                    else:
                        self.calcArray[period]["SuperDrawdown"] = self.calcArray[period - 1]["SuperDrawdown"]
                else:
                    self.calcArray[period]["SuperDrawdown"] = 0

                self.calcArray[period]["Return"] = (self.calcArray[period]["BOPSuperBalance"] - self.calcArray[period]["SuperDrawdown"] / 2) * self.investmentRate/(100* self.FREQUENCY)
                self.calcArray[period]["EOPSuperBalance"] = self.calcArray[period]["BOPSuperBalance"] - self.calcArray[period]["SuperDrawdown"] + self.calcArray[period]["Return"]

                # Check for exhausted Super Balance in this period (ensure period and later periods forced to zero)
                if self.calcArray[period]["EOPSuperBalance"]<0:
                    self.calcArray[period]["Return"] = (self.calcArray[period]["BOPSuperBalance"] / 2) * self.investmentRate / (100* self.FREQUENCY)
                    self.calcArray[period]["SuperDrawdown"] =self.calcArray[period]["Return"]+self.calcArray[period]["BOPSuperBalance"]
                    self.calcArray[period]["EOPSuperBalance"] = self.calcArray[period]["BOPSuperBalance"] - self.calcArray[period]["SuperDrawdown"] + self.calcArray[period]["Return"]

                self.calcArray[period]["PensionIncome"] = self.calcArray[period-1]["PensionIncome"]* (1 + self.inflationRate/(100* self.FREQUENCY))
                self.calcArray[period]["TotalIncome"] = self.calcArray[period]["SuperDrawdown"] + self.calcArray[period]["PensionIncome"]
                self.calcArray[period]["PensionIncomePC"] = self.__chkDivZero(self.calcArray[period]["PensionIncome"] , self.calcArray[period]["TotalIncome"]) * 100
                self.calcArray[period]['CumulativeSuperIncome'] = self.calcArray[period]["SuperDrawdown"]+self.calcArray[period-1]['CumulativeSuperIncome']

            else:
                self.calcArray[period]["PensionIncome"] = self.initDict['annualPensionIncome']/self.FREQUENCY  \
                                                          * (1 + annualInflationRate/100)**(int((period-1)/self.FREQUENCY))
                                                          # calculate pension income indexation

                self.calcArray[period]["TotalIncome"] = self.calcArray[period]["PensionIncome"] \
                                                        + self.calcArray[period]["LoanDrawdown"]

                self.calcArray[period]["PensionIncomePC"] = self.__chkDivZero(self.calcArray[period]["PensionIncome"],
                                                                              self.calcArray[period]["TotalIncome"]) * 100 \
                                                                            / self.FREQUENCY


            self.calcArray[period]["BOPAge"] = self.calcArray[period - 1]["BOPAge"] + 1 / self.FREQUENCY


            #Home Value
            self.calcArray[period]['BOPHouseValue'] = self.calcArray[period-1]['BOPHouseValue']*(1 + hpi/(100* self.FREQUENCY))
            self.calcArray[period]['BOPHomeEquity']=self.calcArray[period]['BOPHouseValue']-self.calcArray[period]['BOPLoanValue']
            self.calcArray[period]['BOPHomeEquityPC'] = max(1 - self.calcArray[period]['BOPLoanValue'] / self.calcArray[period]['BOPHouseValue'], 0)*100
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

        

    # Version 1 Related Methods
    def getInitialIncome(self):
        # income - returns initial projected income (pension + super)
        if self.isInit and self.isVersion1:
            return {'status': 'Ok', 'data': self.currentSuperIncome + self.initDict['annualPensionIncome']}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getEnhancedIncome(self, superTopUp):
        # income - returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        if self.isInit and self.isVersion1:
            return {'status': 'Ok', 'data': self.__enhancedIncome(superTopUp)}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getEnhancedSuperIncome(self, superTopUp):
        # income - returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        if self.isInit and self.isVersion1:
            return {'status': 'Ok', 'data': self.__enhancedSuperIncome(superTopUp)}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getMaxEnhancedIncome(self):
        # income - returns the enhanced income from a max super topUp (existing super, topUp and pension income)
        if self.isInit and self.isVersion1:
            income = self.__enhancedIncome(self.initDict['maxNetLoanAmount'])
            return {'status': 'Ok', 'data': income}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getRequiredTopUp(self, totalIncome):
        # income - returns the required topUp amount for a given target income
        if self.isInit and self.isVersion1:
            topUp = self.__calcBalance(totalIncome - self.currentSuperIncome - self.initDict['annualPensionIncome'])

            return {'status': 'Ok', 'data': topUp}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getProjectionAge(self):
        if self.isInit and self.isVersion1:
            return {'status': 'Ok', 'data': self.minAge + self.incomeProjYears}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getEnhancedIncomeArray(self, incomeIntervals):
        # Returns income / top-up combinations for a range of incomes between current and maximum income
        # as well as projected home equity - used to produce Client 1.0 slider values

        if self.isInit and self.isVersion1:
            incomeArray = []
            maxSuperTopUp = self.initDict['maxNetLoanAmount']

            for item in range(incomeIntervals + 1):
                if item == incomeIntervals:
                    topUpAmount = maxSuperTopUp
                else:
                    topUpAmount = round((item * maxSuperTopUp / incomeIntervals) / 1000, 0) * 1000

                superIncome = self.__calcDrawdown(self.initDict['superAmount'] + topUpAmount)
                income = superIncome + self.initDict['annualPensionIncome']

                projectedEquity = round((1 -
                                         ((topUpAmount * (1 + self.totalInterestRate / 100) ** self.incomeProjYears) /
                                          (self.initDict['valuation'] * (
                                                      1 + self.hpiRate / 100) ** self.incomeProjYears))) * 100
                                        , 0)

                incomeArray.append({"item": item, "income": int(income), "topUp": int(topUpAmount),
                                    "homeEquity": round(projectedEquity, 2),
                                    "percentile": int(round(projectedEquity / 100, 1) * 10),
                                    "newSuperBalance": int(topUpAmount + self.initDict['superAmount']),
                                    "superIncome": int(superIncome)})

            return {'status': 'Ok', 'data': incomeArray}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def __calcTerminalBalance(self, superBalance, drawdown):
        # Primary calculation method used to calculate terminal balance at projection age given
        # a drawdown and superBalance

        calcArray=[{"BOPBalance":0,"Drawdown":0,"Return":0,"EOPBalance":0} for periods in range(((self.incomeProjYears*self.FREQUENCY)+1))]

        #Initial Period
        calcArray[0]["BOPBalance"]=superBalance
        calcArray[0]["Drawdown"]=drawdown/self.FREQUENCY

        calcArray[0]["Return"]= (calcArray[0]["BOPBalance"]-calcArray[0]["Drawdown"]/2) * self.investmentRate/(100* self.FREQUENCY)
                                #Return applied to average balance (assuming drawdown of income evenly over year)
        calcArray[0]["EOPBalance"]= calcArray[0]["BOPBalance"] - calcArray[0]["Drawdown"] + calcArray[0]["Return"]

        # Loop through future periods
        for period in range(1,((self.incomeProjYears*self.FREQUENCY)+1)):
            calcArray[period]["BOPBalance"] = calcArray[period-1]["EOPBalance"]

            if self.initDict['inflationAdj']:
                calcArray[period]["Drawdown"] = calcArray[period-1]["Drawdown"] * (1 + self.inflationRate/(100* self.FREQUENCY))
            else:
                calcArray[period]["Drawdown"] = calcArray[period - 1]["Drawdown"]

            calcArray[period]["Return"] = (calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] / 2) * self.investmentRate/(100* self.FREQUENCY)
            calcArray[period]["EOPBalance"] = calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] + calcArray[period]["Return"]


        return calcArray[self.incomeProjYears*self.FREQUENCY]["EOPBalance"]


    def __enhancedSuperIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        return self.__calcDrawdown(self.initDict['superAmount'] + superTopUp)

    def __enhancedIncome(self, superTopUp):
        # returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        return self.__calcDrawdown(self.initDict['superAmount'] + superTopUp) + self.initDict['annualPensionIncome']


    def __calcBalance(self,superDrawdown):
        # Half interval search for Balance that will enable given Drawdown at the projection age
        highValue=superDrawdown/.01
        lowValue=0
        cntr=0

        seed = (highValue + lowValue) / 2
        currentValue = self.__calcTerminalBalance(seed,superDrawdown)

        if currentValue<0:
            lowValue=seed
        else:
            highValue=seed

        while abs(currentValue)>1:

            if currentValue < 0:
                lowValue = seed
            else:
                highValue = seed

            seed = (highValue + lowValue) / 2
            currentValue =  self.__calcTerminalBalance(seed)

            cntr+=1
            if cntr > 100:
                raise Exception("Calculation Error")

        return seed

    def __calcDrawdown(self, superBalance):
        # Half interval search to calculate the drawdown that exhausts given balance at the projection age
        if superBalance == 0 or superBalance == None:
            return 0

        highValue = superBalance
        lowValue = 0
        cntr = 0

        seed = (highValue + lowValue) / 2
        currentValue = self.__calcTerminalBalance(superBalance, seed)

        if currentValue > 0:
            lowValue = seed
        else:
            highValue = seed

        while abs(currentValue) > 1:
            if currentValue > 0:
                lowValue = seed
            else:
                highValue = seed

            seed = (highValue + lowValue) / 2
            currentValue = self.__calcTerminalBalance(superBalance, seed)

            cntr += 1
            if cntr > 100:
                raise Exception("Calculation Error")

        return seed
