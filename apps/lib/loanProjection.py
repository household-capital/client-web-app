#Python Imports
from math import log

#Local Imports
from apps.lib.enums import loanTypesEnum
from apps.lib.globals import APP_SETTINGS


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


    def __init__(self,initDict):

        # Check for minimum data
        self.initStatus = True
        self.initDict = {}
        self.initDict.update(initDict)

        for item in self.minimumDataList:
            if not self.valueExists(item, self.initDict):
                self.initStatus = False

        # Set optional items = 0
        for item in self.optionalDataList:
            if not self.valueExists(item, self.initDict):
                self.initDict[item] = 0

        # Initially Calculated Variables
        if self.initDict['loanType']==loanTypesEnum.SINGLE_BORROWER.value:
            self.minAge=self.initDict['age_1']
        else:
            if self.valueExists('age_2', self.initDict):
                self.minAge = min(self.initDict['age_1'], self.initDict['age_2'])
            else:
                self.initStatus = False

        #Set minimum period
        self.noPeriods = self.initDict['projectionAge'] - self.minAge
        if self.noPeriods < 2:
            self.noPeriods=5

         # Important! convert interest rate to effective annual (monthly compounded)
        self.totalInterestRate = self.effectiveAnnual(self.initDict['interestRate'] + self.initDict['lendingMargin'], 12)

        # Calculate initial super income
        self.currentSuperIncome = self.calcDrawdown(self.initDict['superAmount'])

        # Calculate top-up income (saved top-up amount driver)
        self.topUpIncome= self.getEnhancedSuperIncome(self.initDict['topUpAmount'])


    # Analytic Methods

    def getInitialIncome(self):
        #returns initial projected income (pension + super)
        return self.currentSuperIncome+self.initDict['annualPensionIncome']

    def getEnhancedIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        income=self.calcDrawdown(self.initDict['superAmount'] + superTopUp) + self.initDict['annualPensionIncome']
        return income

    def getEnhancedSuperIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        income=self.calcDrawdown(self.initDict['superAmount'] + superTopUp)
        return income

    def getMaxEnhancedIncome(self):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        return self.getEnhancedIncome(self.initDict['maxNetLoanAmount'])

    def getNegativeEquityAge(self):
        negAge=self.calcNegAge
        return negAge

    def getEnhancedIncomeArray(self):
        #Returns income / top-up combinations for a range of incomes between current and maximum income
        #as well as projected home equity - used to produce Client 1.0 slider values
        incomeArray = []
        maxSuperTopUp=self.initDict['maxNetLoanAmount']

        for item in range(self.incomeIntervals+1):
            #number of intervals is specified as a class variable
            if item==self.incomeIntervals:
                topUpAmount = maxSuperTopUp
            else:
                topUpAmount = round((item * maxSuperTopUp / self.incomeIntervals)/1000,0)*1000


            superIncome= self.calcDrawdown(self.initDict['superAmount'] +topUpAmount)
            income = superIncome+ self.initDict['annualPensionIncome']


            projectedEquity=round((1-
                    ((topUpAmount * ( 1 + self.totalInterestRate / 100) ** self.noPeriods)/
                    (self.initDict['valuation'] * ( 1 + self.initDict['housePriceInflation'] /100 ) ** self.noPeriods)))*100
                                  ,0)

            incomeArray.append({"item":item,"income":int(income),"topUp":int(topUpAmount),
                                "homeEquity":round(projectedEquity,2),"percentile":int(round(projectedEquity/100,1)*10),
                                "newSuperBalance":int(topUpAmount+self.initDict['superAmount']),
                                "superIncome":int(superIncome)})

        return incomeArray

    def getRequiredTopUp(self,totalIncome):
        #Returns the required topUp amount for a given target income

        topUp = self.calcBalance( totalIncome - self.currentSuperIncome - self.initDict['annualPensionIncome'])
        return topUp

    def getProjectionAge(self):
        return self.minAge+self.noPeriods



    # Primary Projecton Method

    def getProjections(self,**kwargs):

        # Peturb assumptions based on stress paramaters passed as keyword arguments
        intRate=self.totalInterestRate
        if 'intRateStress' in kwargs:
            intRate = self.effectiveAnnual(
                self.initDict['interestRate'] + self.initDict['lendingMargin'] + kwargs['intRateStress'], 12)
        if 'intRateStressLevel' in kwargs:
            intRate = self.effectiveAnnual(kwargs['intRateStressLevel'],12)

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

        calcArray=[{"BOPAge":0,"BOPBalance":0,"Drawdown":0,"Return":0,"EOPBalance":0,'PensionIncome':0,
                    'TotalIncome':0,'PensionIncomePC':0,'CumulativeSuperIncome':0,'BOPHouseValue':0,
                    'BOPLoanValue':0,'BOPHomeEquity':0,'BOPHomeEquityPC':0} for periods in range(self.minProjectionPeriods)]


        #Initial Period
        calcArray[0]["BOPAge"] = self.minAge
        calcArray[0]["BOPBalance"]=self.initDict['superAmount']+self.initDict['topUpAmount']
        calcArray[0]["Drawdown"]=superIncome

        # Note: Return applied to average balance (assuming drawdown of income evenly over year)
        calcArray[0]["Return"]= (calcArray[0]["BOPBalance"]-calcArray[0]["Drawdown"]/2) * self.initDict['investmentRate']/100

        calcArray[0]["EOPBalance"]= calcArray[0]["BOPBalance"] - calcArray[0]["Drawdown"] + calcArray[0]["Return"]
        calcArray[0]["PensionIncome"]=self.initDict['annualPensionIncome']
        calcArray[0]["TotalIncome"]=calcArray[0]["Drawdown"]+calcArray[0]["PensionIncome"]
        calcArray[0]["PensionIncomePC"] = self.chkDivZero(calcArray[0]["PensionIncome"],calcArray[0]["TotalIncome"])*100
        calcArray[0]['CumulativeSuperIncome']=calcArray[0]["Drawdown"]

        # Note: BOP HouseValue does not have loan deducted (for presentational reasons)
        calcArray[0]['BOPHouseValue']=self.initDict['valuation']
        calcArray[0]['BOPLoanValue']=self.initDict['totalLoanAmount']
        calcArray[0]['BOPHomeEquity']=calcArray[0]['BOPHouseValue'] #Prior to loan
        calcArray[0]['BOPHomeEquityPC']=100 #Prior to loan

        # Loop through future periods
        for period in range(1,self.minProjectionPeriods):
            calcArray[period]["BOPAge"] = calcArray[period-1]["BOPAge"]+1
            calcArray[period]["BOPBalance"] = calcArray[period-1]["EOPBalance"]

            # If starting balance == 0, no drawdown
            if calcArray[period]["BOPBalance"]>0:
                calcArray[period]["Drawdown"] = calcArray[period-1]["Drawdown"] * (1 + self.initDict['inflationRate']/100)
            else:
                calcArray[period]["Drawdown"] = 0

            calcArray[period]["Return"] = (calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] / 2) * self.initDict['investmentRate']/100
            calcArray[period]["EOPBalance"] = calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] + calcArray[period]["Return"]

            # Check for exhausted Super Balance in this period (ensure period and later periods forced to zero)
            if calcArray[period]["EOPBalance"]<0:
                calcArray[period]["Return"] = (calcArray[period]["BOPBalance"] / 2) * self.initDict['investmentRate'] / 100
                calcArray[period]["Drawdown"] =calcArray[period]["Return"]+calcArray[period]["BOPBalance"]
                calcArray[period]["EOPBalance"] = calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] + calcArray[period]["Return"]

            calcArray[period]["PensionIncome"] = calcArray[period-1]["PensionIncome"]* (1 + self.initDict['inflationRate']/100)
            calcArray[period]["TotalIncome"] = calcArray[period]["Drawdown"] + calcArray[period]["PensionIncome"]
            calcArray[period]["PensionIncomePC"] = self.chkDivZero(calcArray[period]["PensionIncome"] , calcArray[period]["TotalIncome"]) * 100
            calcArray[period]['CumulativeSuperIncome'] = calcArray[period]["Drawdown"]+calcArray[period-1]['CumulativeSuperIncome']
            calcArray[period]['BOPHouseValue'] = calcArray[period-1]['BOPHouseValue']*(1 + hpi/100)
            calcArray[period]['BOPLoanValue'] = calcArray[period-1]['BOPLoanValue']*(1+intRate/100)
            calcArray[period]['BOPHomeEquity']=calcArray[period]['BOPHouseValue']-calcArray[period]['BOPLoanValue']
            calcArray[period]['BOPHomeEquityPC'] = max(1 - calcArray[period]['BOPLoanValue'] / calcArray[period]['BOPHouseValue'], 0)*100

        return calcArray


    # INTERNAL METHODS

    def calcDrawdown(self,superBalance):
        # Half interval search to calculate the drawdown that exhausts given balance at the projection age

        if superBalance == 0 or superBalance == None:
            return 0

        highValue=superBalance
        lowValue=0
        cntr=0

        seed = (highValue + lowValue) / 2
        currentValue = self.calcTerminalBalance(superBalance,seed)

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
            currentValue =  self.calcTerminalBalance(superBalance,seed)

            cntr+=1
            if cntr > 100:
                raise Exception("Calculation Error")

        return seed

    def calcBalance(self,superDrawdown):
        # Half interval search for Balance that will enable given Drawdown at the projection age
        highValue=superDrawdown/.01
        lowValue=0
        cntr=0

        seed = (highValue + lowValue) / 2
        currentValue = self.calcTerminalBalance(seed,superDrawdown)

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
            currentValue =  self.calcTerminalBalance(seed,superDrawdown)

            cntr+=1
            if cntr > 100:
                raise Exception("Calculation Error")

        return seed


    def calcTerminalBalance(self,superBalance,drawdown):
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

    def calcNegAge(self):
        periods=log(1/(self.initDict['totalLoanAmount']/self.initDict['valuation']))/log((1+self.totalInterestRate/100)/(1 + self.initDict['housePriceInflation']/100))

        return self.minAge+ int(periods)

    def effectiveAnnual(self, rate, compounding):
        return (((1 + rate/(compounding * 100)) ** compounding)-1)*100

    def chkDivZero(self,numerator, divisor):
        if divisor==0:
            return 0
        else:
            return numerator/divisor

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


