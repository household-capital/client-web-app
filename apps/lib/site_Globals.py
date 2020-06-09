
# Application Globals

LOAN_LIMITS={'minSingleAge' : 60,
             'minCoupleAge' : 60,
             'minLoanSize' : 20000,
             'minIncomeDrawdown' : 500,
             'maxTopUp' : 500000,
             'maxCare' : 550000,
             'maxReno' : 200000,
             'maxRefi' : 1.00,
             'maxTravel' : 0.20,
             'maxGive' : 0.20,
             'baseLvr' : 0.15,
             'baseLvrAge' : 60,
             'baseLvrIncrement' : 0.01,
             'apartmentLvrAdj' : 0.05,
             'establishmentFee':0.015,
             'topUpBufferAmount':5000,
             'titleUtilTrigger': 0.60,
             'titleAmountTrigger':400000,
             'maxDrawdownYears': 1,
             'lumpSum20K': 20000,
}

ECONOMIC={'inflationRate' :float(2.50),
          'housePriceInflation' : float(3.00),
          'interestRate' :float(0.75),
          'lendingMargin':float(4.40),
          'comparisonRateIncrement':float(0.06),
          'defaultMargin': float(2.00),
}

APP_SETTINGS={'minProjectionYears': 15,
              'incomeProjectionYears': 10,
              'intRateStress':2,
              'hpiHighStressLevel':0,
              'hpiLowStressLevel':1.5,
}





