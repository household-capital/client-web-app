#Python Imports
from math import log

#Local Imports
from apps.lib.site_Enums import loanTypesEnum
from apps.lib.site_Globals import APP_SETTINGS


class LoanProjection():

    # Utility class used to generate a table of loan projections (list of dictionaries) - superannuation, income, home equity
    # Primary method: getProjections
    # Additional methods return specific analytics
    # Object instantiated with dictionary
    # Consistent with ASIC projections
    # Stress projections can be generated through passing shocks via specified keyword arguments
    # Approach based on brute-force array calculation (no analytical solutions) to enable maximum flexibility and repeatability

    # Class variables [imported]
    incomeIntervals=APP_SETTINGS['incomeIntervals']
    minProjectionPeriods=APP_SETTINGS['minProjectionPeriods']

    minimumDataList = ['loanType','age_1','valuation',
                       'projectionAge','maxNetLoanAmount','housePriceInflation','inflationRate','interestRate',
                       'lendingMargin','investmentRate','totalLoanAmount']

    optionalDataList = ['superAmount', 'annualPensionIncome','topUpAmount']


    def __init__(self):
        #instance variables
        self.initStatus = False
        self.initDict = {}
        self.minAge=0
        self.noPeriods=0
        self.totalInterestRate=0
        self.currentSuperIncome=0
        self.topUpIncome=0

        # Primary Results Array
        self.calcArray=[]


    def create(self, initDict):

        self.initStatus=True

        # Check for minimum data
        self.initDict.update(initDict)

        for item in self.minimumDataList:
            if not self.__valueExists(item, self.initDict):
                self.initStatus = False
                return {'status': 'Error','responseText':'Missing Data - '+item}

        # Set optional items = 0
        for item in self.optionalDataList:
            if not self.__valueExists(item, self.initDict):
                self.initDict[item] = 0

        # Initially Calculated Variables
        if self.initDict['loanType']==loanTypesEnum.SINGLE_BORROWER.value:
            self.minAge=self.initDict['age_1']
        else:
            if self.__valueExists('age_2', self.initDict):
                self.minAge = min(self.initDict['age_1'], self.initDict['age_2'])
            else:
                self.initStatus = False
                return {'status': 'Error','responseText':'Missing Data - age_2'}


        #Set minimum period
        self.noPeriods = self.initDict['projectionAge'] - self.minAge
        if self.noPeriods < 2:
            self.noPeriods=5

         # Important! convert interest rate to effective annual (monthly compounded)
        self.totalInterestRate = self.__effectiveAnnual(self.initDict['interestRate'] + self.initDict['lendingMargin'], 12)

        # Calculate initial super income
        self.currentSuperIncome = self.__calcDrawdown(self.initDict['superAmount'])

        # Calculate top-up income (saved top-up amount driver)
        self.topUpIncome= self.__enhancedSuperIncome(self.initDict['topUpAmount'])

        return {'status':'Ok'}


    # Object's Public Analytic Methods

    def getInitialIncome(self):
        #returns initial projected income (pension + super)
        if self.initStatus:
            return {'status':'Ok', 'data':self.currentSuperIncome+self.initDict['annualPensionIncome']}
        else:
            return {'status':'Error', 'responseText':'Object not instantiated'}

    def getEnhancedIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        if self.initStatus:
             return {'status':'Ok', 'data':self.__enhancedIncome(superTopUp)}
        else:
            return {'status':'Error', 'responseText':'Object not instantiated'}

    def getEnhancedSuperIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        if self.initStatus:
            return {'status':'Ok', 'data':self.__enhancedSuperIncome(superTopUp)}
        else:
            return {'status':'Error', 'responseText':'Object not instantiated'}

    def getMaxEnhancedIncome(self):
        #returns the enhanced income from a max super topUp (existing super, topUp and pension income)
        if self.initStatus:

            income = self.__enhancedIncome(self.initDict['maxNetLoanAmount'])
            return {'status': 'Ok', 'data': income}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getNegativeEquityAge(self):
        if self.initStatus:
            return {'status': 'Ok', 'data': self.__calcNegAge}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getRequiredTopUp(self, totalIncome):
        # Returns the required topUp amount for a given target income
        if self.initStatus:
            topUp = self.__calcBalance(totalIncome - self.currentSuperIncome - self.initDict['annualPensionIncome'])

            return {'status': 'Ok', 'data': topUp}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getProjectionAge(self):
        if self.initStatus:
            return {'status': 'Ok', 'data': self.minAge + self.noPeriods}
        else:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

    def getEnhancedIncomeArray(self):
        #Returns income / top-up combinations for a range of incomes between current and maximum income
        #as well as projected home equity - used to produce Client 1.0 slider values
        if not self.initStatus:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

        incomeArray = []
        maxSuperTopUp=self.initDict['maxNetLoanAmount']

        for item in range(self.incomeIntervals+1):
            #number of intervals is specified as a class variable
            if item==self.incomeIntervals:
                topUpAmount = maxSuperTopUp
            else:
                topUpAmount = round((item * maxSuperTopUp / self.incomeIntervals)/1000,0)*1000


            superIncome= self.__calcDrawdown(self.initDict['superAmount'] +topUpAmount)
            income = superIncome+ self.initDict['annualPensionIncome']


            projectedEquity=round((1-
                    ((topUpAmount * ( 1 + self.totalInterestRate / 100) ** self.noPeriods)/
                    (self.initDict['valuation'] * ( 1 + self.initDict['housePriceInflation'] /100 ) ** self.noPeriods)))*100
                                  ,0)

            incomeArray.append({"item":item,"income":int(income),"topUp":int(topUpAmount),
                                "homeEquity":round(projectedEquity,2),"percentile":int(round(projectedEquity/100,1)*10),
                                "newSuperBalance":int(topUpAmount+self.initDict['superAmount']),
                                "superIncome":int(superIncome)})

        return {'status': 'Ok', 'data': incomeArray}

    def getProjections(self):
        if len(self.calcArray)==0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}
        else:
            return {'status': 'Ok', 'data': self.calcArray}

    # Primary Projecton Method

    def calcProjections(self,**kwargs):
        if not self.initStatus:
            return {'status': 'Error', 'responseText': 'Object not instantiated'}

        # Peturb assumptions based on stress parameters passed as keyword arguments
        intRate=self.totalInterestRate
        if 'intRateStress' in kwargs:
            intRate = self.__effectiveAnnual(
                self.initDict['interestRate'] + self.initDict['lendingMargin'] + kwargs['intRateStress'], 12)
        if 'intRateStressLevel' in kwargs:
            intRate = self.__effectiveAnnual(kwargs['intRateStressLevel'],12)

        hpi=self.initDict['housePriceInflation']
        if 'hpiStress' in kwargs:
            hpi=hpi+kwargs['hpiStress']
        if 'hpiStressLevel' in kwargs:
            hpi = kwargs['hpiStressLevel']

        superIncome= self.topUpIncome

        # Define structure of the return array
        # - the dictionary elements are like columns; and
        # - the period index are like rows
        # List comprehension to replicate the dictionary for the required number of periods

        self.calcArray = []

        self.calcArray=[{"BOPAge":0,"BOPBalance":0,"Drawdown":0,"Return":0,"EOPBalance":0,'PensionIncome':0,
                    'TotalIncome':0,'PensionIncomePC':0,'CumulativeSuperIncome':0,'BOPHouseValue':0,
                    'BOPLoanValue':0,'BOPHomeEquity':0,'BOPHomeEquityPC':0} for periods in range(self.minProjectionPeriods)]


        #Initial Period
        self.calcArray[0]["BOPAge"] = self.minAge
        self.calcArray[0]["BOPBalance"]=self.initDict['superAmount']+self.initDict['topUpAmount']
        self.calcArray[0]["Drawdown"]=superIncome

        # Note: Return applied to average balance (assuming drawdown of income evenly over year)
        self.calcArray[0]["Return"]= (self.calcArray[0]["BOPBalance"]-self.calcArray[0]["Drawdown"]/2) * self.initDict['investmentRate']/100

        self.calcArray[0]["EOPBalance"]= self.calcArray[0]["BOPBalance"] - self.calcArray[0]["Drawdown"] + self.calcArray[0]["Return"]
        self.calcArray[0]["PensionIncome"]=self.initDict['annualPensionIncome']
        self.calcArray[0]["TotalIncome"]=self.calcArray[0]["Drawdown"]+self.calcArray[0]["PensionIncome"]
        self.calcArray[0]["PensionIncomePC"] = self.__chkDivZero(self.calcArray[0]["PensionIncome"],self.calcArray[0]["TotalIncome"])*100
        self.calcArray[0]['CumulativeSuperIncome']=self.calcArray[0]["Drawdown"]

        self.calcArray[0]['BOPHouseValue']=self.initDict['valuation']
        self.calcArray[0]['BOPLoanValue']=self.initDict['totalLoanAmount']
        self.calcArray[0]['BOPHomeEquity'] = self.calcArray[0]['BOPHouseValue'] - self.calcArray[0]['BOPLoanValue']
        self.calcArray[0]['BOPHomeEquityPC'] = max(1 - self.calcArray[0]['BOPLoanValue'] / self.calcArray[0]['BOPHouseValue'], 0) * 100

        # Loop through future periods
        for period in range(1,self.minProjectionPeriods):
            self.calcArray[period]["BOPAge"] = self.calcArray[period-1]["BOPAge"]+1
            self.calcArray[period]["BOPBalance"] = self.calcArray[period-1]["EOPBalance"]

            # If starting balance == 0, no drawdown
            if self.calcArray[period]["BOPBalance"]>0:
                self.calcArray[period]["Drawdown"] = self.calcArray[period-1]["Drawdown"] * (1 + self.initDict['inflationRate']/100)
            else:
                self.calcArray[period]["Drawdown"] = 0

            self.calcArray[period]["Return"] = (self.calcArray[period]["BOPBalance"] - self.calcArray[period]["Drawdown"] / 2) * self.initDict['investmentRate']/100
            self.calcArray[period]["EOPBalance"] = self.calcArray[period]["BOPBalance"] - self.calcArray[period]["Drawdown"] + self.calcArray[period]["Return"]

            # Check for exhausted Super Balance in this period (ensure period and later periods forced to zero)
            if self.calcArray[period]["EOPBalance"]<0:
                self.calcArray[period]["Return"] = (self.calcArray[period]["BOPBalance"] / 2) * self.initDict['investmentRate'] / 100
                self.calcArray[period]["Drawdown"] =self.calcArray[period]["Return"]+self.calcArray[period]["BOPBalance"]
                self.calcArray[period]["EOPBalance"] = self.calcArray[period]["BOPBalance"] - self.calcArray[period]["Drawdown"] + self.calcArray[period]["Return"]

            self.calcArray[period]["PensionIncome"] = self.calcArray[period-1]["PensionIncome"]* (1 + self.initDict['inflationRate']/100)
            self.calcArray[period]["TotalIncome"] = self.calcArray[period]["Drawdown"] + self.calcArray[period]["PensionIncome"]
            self.calcArray[period]["PensionIncomePC"] = self.__chkDivZero(self.calcArray[period]["PensionIncome"] , self.calcArray[period]["TotalIncome"]) * 100
            self.calcArray[period]['CumulativeSuperIncome'] = self.calcArray[period]["Drawdown"]+self.calcArray[period-1]['CumulativeSuperIncome']
            self.calcArray[period]['BOPHouseValue'] = self.calcArray[period-1]['BOPHouseValue']*(1 + hpi/100)
            self.calcArray[period]['BOPLoanValue'] = self.calcArray[period-1]['BOPLoanValue']*(1+intRate/100)
            self.calcArray[period]['BOPHomeEquity']=self.calcArray[period]['BOPHouseValue']-self.calcArray[period]['BOPLoanValue']
            self.calcArray[period]['BOPHomeEquityPC'] = max(1 - self.calcArray[period]['BOPLoanValue'] / self.calcArray[period]['BOPHouseValue'], 0)*100

        return {'status': 'Ok'}


    def getResultsList(self, keyName, **kwargs):
        # Builds a results list to pass to the template
        # Optionally calculates scaling for images
        if len(self.calcArray)==0:
            return {'status': 'Error', 'responseText': 'Projections not calculated'}

        scaleList = []

        figuresList = [int(self.calcArray[i][keyName]) for i in [0, 5, 10, 15]]

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

        figuresList = [int(round(self.calcArray[i][keyName] / 10, 0)) for i in [0, 5, 10, 15]]
        imageList = [imageURL.replace('{0}', str(figuresList[i])) for i in range(4)]

        return {'status': 'Ok', 'data': imageList}


    # INTERNAL METHODS

    def __logOrZero(self, val):
        if val <= 0:
            return 0
        return log(val)

    def __calcDrawdown(self,superBalance):
        # Half interval search to calculate the drawdown that exhausts given balance at the projection age

        if superBalance == 0 or superBalance == None:
            return 0

        highValue=superBalance
        lowValue=0
        cntr=0

        seed = (highValue + lowValue) / 2
        currentValue = self.__calcTerminalBalance(superBalance,seed)

        if currentValue>0:
            lowValue=seed
        else:
            highValue=seed

        while abs(currentValue)>1:
            if currentValue > 0:
                lowValue = seed
            else:
                highValue = seed

            seed = (highValue + lowValue) / 2
            currentValue =  self.__calcTerminalBalance(superBalance,seed)

            cntr+=1
            if cntr > 100:
                raise Exception("Calculation Error")

        return seed

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
            currentValue =  self.__calcTerminalBalance(seed,superDrawdown)

            cntr+=1
            if cntr > 100:
                raise Exception("Calculation Error")

        return seed


    def __calcTerminalBalance(self,superBalance,drawdown):
        # Primary calculation method used to calculate terminal balance at projection age given
        # a drawdown and superBalance. Simple array (using python list-dictionary for readability)

        calcArray=[{"BOPBalance":0,"Drawdown":0,"Return":0,"EOPBalance":0} for periods in range(self.noPeriods)]

        #Initial Period
        calcArray[0]["BOPBalance"]=superBalance
        calcArray[0]["Drawdown"]=drawdown

        calcArray[0]["Return"]= (calcArray[0]["BOPBalance"]-calcArray[0]["Drawdown"]/2) * self.initDict['investmentRate']/100
                                #Return applied to average balance (assuming drawdown of income evenly over year)
        calcArray[0]["EOPBalance"]= calcArray[0]["BOPBalance"] - calcArray[0]["Drawdown"] + calcArray[0]["Return"]

        # Loop through future periods
        for period in range(1,self.noPeriods):
            calcArray[period]["BOPBalance"] = calcArray[period-1]["EOPBalance"]
            calcArray[period]["Drawdown"] = calcArray[period-1]["Drawdown"] * (1 + self.initDict['inflationRate']/100)
            calcArray[period]["Return"] = (calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] / 2) * self.initDict['investmentRate']/100
            calcArray[period]["EOPBalance"] = calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] + calcArray[period]["Return"]

        return calcArray[self.noPeriods-1]["EOPBalance"]


    def __enhancedSuperIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        return self.__calcDrawdown(self.initDict['superAmount'] + superTopUp)

    def __enhancedIncome(self, superTopUp):
        # returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        return self.__calcDrawdown(self.initDict['superAmount'] + superTopUp) + self.initDict['annualPensionIncome']

    def __calcNegAge(self):
        periods=log(1/(self.initDict['totalLoanAmount']/self.initDict['valuation']))/log((1+self.totalInterestRate/100)/(1 + self.initDict['housePriceInflation']/100))

        return self.minAge + int(periods)

    def __effectiveAnnual(self, rate, compounding):
        return (((1 + rate/(compounding * 100)) ** compounding)-1)*100

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


