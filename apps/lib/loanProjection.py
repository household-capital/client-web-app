from apps.lib.globals import APP_SETTINGS
from math import log

class LoanProjection():

    # CLASS VARIABLES

    incomeIntervals=APP_SETTINGS['incomeIntervals']
    minProjectionPeriods=APP_SETTINGS['minProjectionPeriods']

    def __init__(self,aggregateDictionary):

        #Initialisation Variables
        self.aggDict = {}
        self.aggDict.update(aggregateDictionary)

        self.projectionAge = self.aggDict['projectionAge']
        if self.aggDict['loanType']==0:
            self.minAge=self.aggDict['age_1']
        else:
            self.minAge = min(self.aggDict['age_1'],self.aggDict['age_2'])

        self.noPeriods=self.projectionAge - self.minAge
        self.currentSuperIncome=self.calcDrawdown(self.aggDict['superAmount'])  #Calculate initial super income
 
        self.totalInterestRate = self.effectiveAnnual(self.aggDict['interestRate'] + self.aggDict['lendingMargin'],12)
        # Important convert interest rate to effective annual (monthly compounded)

        if self.noPeriods<2:
            raise Exception("Too short period")


    # EXTERNAL METHODS

    def getInitialIncome(self):
        #returns initial projected income (pension + super)
        return self.currentSuperIncome+self.aggDict['annualPensionIncome']

    def getEnhancedIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        income=self.calcDrawdown(self.aggDict['superAmount'] + superTopUp) + self.aggDict['annualPensionIncome']
        return income

    def getEnhancedSuperIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        income=self.calcDrawdown(self.aggDict['superAmount'] + superTopUp)
        return income


    def getMaxEnhancedIncome(self):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        superTopUp=self.aggDict['maxNetLoanAmount']
        return self.getEnhancedIncome(superTopUp)

    def getNegativeEquityAge(self):
        negAge=self.calcNegAge
        return negAge

    def getEnhancedIncomeArray(self):
        #Returns income / top-up combinations for a range of incomes between current and maximum income
        #as well as projected home equity
        incomeArray = []
        maxSuperTopUp=self.aggDict['maxNetLoanAmount']

      #  maxIncome=self.calcDrawdown( self.aggDict['superAmount'] + maxSuperTopUp) + self.aggDict['annualPensionIncome']
      # initialIncome=self.currentSuperIncome+self.aggDict['annualPensionIncome']

        for item in range(self.incomeIntervals+1):
            #number of intervals is specified as a class variable
            topUpAmount = item*maxSuperTopUp / self.incomeIntervals
            superIncome= self.calcDrawdown(self.aggDict['superAmount'] +topUpAmount)
            income = superIncome+ self.aggDict['annualPensionIncome']


            projectedEquity=round((1-((topUpAmount * ( 1 + self.totalInterestRate / 100) ** self.noPeriods)
                               /(self.aggDict['valuation'] * ( 1 + self.aggDict['housePriceInflation'] /100 ) ** self.noPeriods)))*100,0)

            incomeArray.append({"item":item,"income":int(income),"topUp":int(topUpAmount),
                                "homeEquity":round(projectedEquity,2),"percentile":int(round(projectedEquity/100,1)*10),
                                "newSuperBalance":int(topUpAmount+self.aggDict['superAmount']),
                                "superIncome":int(superIncome)})

        return incomeArray

    def getRequiredTopUp(self,totalIncome):
        #Returns the required topUp amount for a given target income
        topUp = self.calcBalance( totalIncome - self.currentSuperIncome - self.aggDict['annualPensionIncome'])
        return topUp

    def getProjectionAge(self):
        return self.minAge+self.noPeriods

    # INTERNAL METHODS

    def calcDrawdown(self,superBalance):
        # Half interval search to calculate the drawdown that exhausts given balance at the projection age
        highValue=superBalance
        lowValue=0
        cntr=0

        if superBalance == 0:
            return 0

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

        calcArray[0]["Return"]= (calcArray[0]["BOPBalance"]-calcArray[0]["Drawdown"]/2) * self.aggDict['investmentRate']/100
                                #Return applied to average balance (assuming drawdown of income evenly over year)
        calcArray[0]["EOPBalance"]= calcArray[0]["BOPBalance"] - calcArray[0]["Drawdown"] + calcArray[0]["Return"]

        # Loop through future periods
        for period in range(1,self.noPeriods):
            calcArray[period]["BOPBalance"] = calcArray[period-1]["EOPBalance"]
            calcArray[period]["Drawdown"] = calcArray[period-1]["Drawdown"] * (1 + self.aggDict['inflationRate']/100)
            calcArray[period]["Return"] = (calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] / 2) * self.aggDict['investmentRate']/100
            calcArray[period]["EOPBalance"] = calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] + calcArray[period]["Return"]

        return calcArray[self.noPeriods-1]["EOPBalance"]


    def getProjections(self,**kwargs):

        intRate=self.totalInterestRate
        if 'intRateStress' in kwargs:
            intRate = self.effectiveAnnual(
                self.aggDict['interestRate'] + self.aggDict['lendingMargin'] + kwargs['intRateStress'], 12)
        if 'intRateStressLevel' in kwargs:
            intRate = self.effectiveAnnual(kwargs['intRateStressLevel'],12)



        hpi=self.aggDict['housePriceInflation']
        if 'hpiStress' in kwargs:
            hpi=hpi+kwargs['hpiStress']
        if 'hpiStressLevel' in kwargs:
            hpi = kwargs['hpiStressLevel']

        superIncome= self.aggDict['topUpIncome']

        calcArray=[{"BOPAge":0,"BOPBalance":0,"Drawdown":0,"Return":0,"EOPBalance":0,'PensionIncome':0,
                    'TotalIncome':0,'PensionIncomePC':0,'CumulativeSuperIncome':0,'BOPHouseValue':0,
                    'BOPLoanValue':0,'BOPHomeEquity':0,'BOPHomeEquityPC':0} for periods in range(self.minProjectionPeriods)]

        #Initial Period
        calcArray[0]["BOPAge"] = self.minAge
        calcArray[0]["BOPBalance"]=self.aggDict['superAmount']+self.aggDict['topUpAmount']
        calcArray[0]["Drawdown"]=superIncome

        calcArray[0]["Return"]= (calcArray[0]["BOPBalance"]-calcArray[0]["Drawdown"]/2) * self.aggDict['investmentRate']/100

        #Return applied to average balance (assuming drawdown of income evenly over year)
        calcArray[0]["EOPBalance"]= calcArray[0]["BOPBalance"] - calcArray[0]["Drawdown"] + calcArray[0]["Return"]
        calcArray[0]["PensionIncome"]=self.aggDict['annualPensionIncome']
        calcArray[0]["TotalIncome"]=calcArray[0]["Drawdown"]+calcArray[0]["PensionIncome"]
        calcArray[0]["PensionIncomePC"] = self.chkDivZero(calcArray[0]["PensionIncome"],calcArray[0]["TotalIncome"])*100
        calcArray[0]['CumulativeSuperIncome']=calcArray[0]["Drawdown"]
        calcArray[0]['BOPHouseValue']=self.aggDict['valuation']
        calcArray[0]['BOPLoanValue']=self.aggDict['totalLoanAmount']
        calcArray[0]['BOPHomeEquity']=calcArray[0]['BOPHouseValue'] #Prior to loan
        calcArray[0]['BOPHomeEquityPC']=100 #Prior to loan

        # Loop through future periods
        for period in range(1,self.minProjectionPeriods):
            calcArray[period]["BOPAge"] = calcArray[period-1]["BOPAge"]+1
            calcArray[period]["BOPBalance"] = calcArray[period-1]["EOPBalance"]

            calcArray[period]["Drawdown"] = calcArray[period-1]["Drawdown"] * (1 + self.aggDict['inflationRate']/100)
            calcArray[period]["Return"] = (calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] / 2) * self.aggDict['investmentRate']/100
            #Check for exhausted Super Balance
            calcArray[period]["EOPBalance"] = calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] + calcArray[period]["Return"]

            calcArray[period]["PensionIncome"] = calcArray[period-1]["PensionIncome"]* (1 + self.aggDict['inflationRate']/100)
            calcArray[period]["TotalIncome"] = calcArray[period]["Drawdown"] + calcArray[period]["PensionIncome"]
            calcArray[period]["PensionIncomePC"] = self.chkDivZero(calcArray[period]["PensionIncome"] , calcArray[period]["TotalIncome"]) * 100
            calcArray[period]['CumulativeSuperIncome'] = calcArray[period]["Drawdown"]+calcArray[period-1]['CumulativeSuperIncome']
            calcArray[period]['BOPHouseValue'] = calcArray[period-1]['BOPHouseValue']*(1 + hpi/100)
            calcArray[period]['BOPLoanValue'] = calcArray[period-1]['BOPLoanValue']*(1+intRate/100)
            calcArray[period]['BOPHomeEquity']=calcArray[period]['BOPHouseValue']-calcArray[period]['BOPLoanValue']
            calcArray[period]['BOPHomeEquityPC'] = max(1 - calcArray[period]['BOPLoanValue'] / calcArray[period]['BOPHouseValue'], 0)*100
        return calcArray


    def calcNegAge(self):
        periods=log(1/(self.aggDict['totalLoanAmount']/self.aggDict['valuation']))/log((1+self.totalInterestRate/100)/(1 + self.aggDict['housePriceInflation']/100))

        return self.minAge+ int(periods)

    def effectiveAnnual(self, rate, compounding):
        return (((1 + rate/(compounding * 100)) ** compounding)-1)*100

    def chkDivZero(self,numerator, divisor):
        if divisor==0:
            return 0
        else:
            return numerator/divisor


