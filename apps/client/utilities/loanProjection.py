from .globals import APP_SETTINGS


class LoanProjection():

    # CLASS VARIABLES

    projectionAge=APP_SETTINGS['projectionAge']
    incomeIntervals=APP_SETTINGS['incomeIntervals']

    def __init__(self,loanDict,clientDict,economicDict, loanStatusDict):

        #Initialisation Variables
        self.aggDict = {}
        self.aggDict.update(loanDict)
        self.aggDict.update(clientDict)
        self.aggDict.update(economicDict)
        self.aggDict.update(loanStatusDict)

        self.noPeriods=self.projectionAge - self.aggDict['clientAge']
        self.currentSuperIncome=self.calcDrawdown(self.aggDict['clientSuperAmount'])  #Calculate initial super income
        self.pensionIncome=self.aggDict['clientPension']*26
        self.totalInterestRate = self.aggDict['interestRate'] + self.aggDict['lendingMargin']

        if self.noPeriods<2:
            raise Exception("Too short period")


    # EXTERNAL METHODS

    def getInitialIncome(self):
        #returns initial projected income (pension + super)
        return self.currentSuperIncome+self.pensionIncome

    def getEnhancedIncome(self,superTopUp):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        income=self.calcDrawdown(self.aggDict['clientSuperAmount'] + superTopUp) + self.pensionIncome
        return income

    def getMaxEnhancedIncome(self):
        #returns the enhanced income from a given super topUp (existing super, topUp and pension income)
        superTopUp=self.aggDict['maxLoanAmount']
        return self.getEnhancedIncome(superTopUp)


    def getEnhancedIncomeArray(self):
        #Returns income / top-up combinations for a range of incomes between current and maximum income
        #as well as projected home equity
        incomeArray = []
        maxSuperTopUp=self.aggDict['maxLoanAmount']

      #  maxIncome=self.calcDrawdown( self.aggDict['clientSuperAmount'] + maxSuperTopUp) + self.pensionIncome
      # initialIncome=self.currentSuperIncome+self.pensionIncome

        for item in range(self.incomeIntervals+1):
            #number of intervals is specified as a class variable
            topUpAmount = item*maxSuperTopUp / self.incomeIntervals
            income = self.calcDrawdown(self.aggDict['clientSuperAmount'] +topUpAmount)+ self.pensionIncome

            projectedEquity=round((1-((topUpAmount * ( 1 + self.totalInterestRate / 100) ** self.noPeriods)
                               /(self.aggDict['clientValuation'] * ( 1 + self.aggDict['housePriceInflation'] /100 ) ** self.noPeriods)))*100,0)

            incomeArray.append({"item":item,"income":int(income),"topUp":int(topUpAmount),
                                "homeEquity":round(projectedEquity,2),"percentile":int(round(projectedEquity/100,1)*10),
                                "newSuperBalance":int(topUpAmount+self.aggDict['clientSuperAmount'])})

        return incomeArray

    def getRequiredTopUp(self,totalIncome):
        #Returns the required topUp amount for a given target income
        topUp = self.calcBalance( totalIncome - self.currentSuperIncome - self.pensionIncome)
        return topUp

    # INTERNAL METHODS

    def calcDrawdown(self,superBalance):
        # Half interval search to calculate the drawdown that exhausts given balance at the projection age
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

        calcArray[0]["Return"]= (calcArray[0]["BOPBalance"]-calcArray[0]["Drawdown"]/2) * self.aggDict['investmentReturn']/100
                                #Return applied to average balance (assuming drawdown of income evenly over year)
        calcArray[0]["EOPBalance"]= calcArray[0]["BOPBalance"] - calcArray[0]["Drawdown"] + calcArray[0]["Return"]

        # Loop through future periods
        for period in range(1,self.noPeriods):
            calcArray[period]["BOPBalance"] = calcArray[period-1]["EOPBalance"]
            calcArray[period]["Drawdown"] = calcArray[period-1]["Drawdown"] * (1 + self.aggDict['inflation']/100)
            calcArray[period]["Return"] = (calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] / 2) * self.aggDict['investmentReturn']/100
            calcArray[period]["EOPBalance"] = calcArray[period]["BOPBalance"] - calcArray[period]["Drawdown"] + calcArray[period]["Return"]

        return calcArray[self.noPeriods-1]["EOPBalance"]









