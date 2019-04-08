
# Application Globals

LOAN_LIMITS={'minSingleAge' : 60,
             'minCoupleAge' : 65,
             'minLoanSize' : 50000,
             'maxLoanSize': 550000,
             'maxTopUp' : 500000,
             'maxCare' : 550000,
             'maxReno' : 200000,
             'maxRefi' : 0.25,
             'maxTravel' : 0.20,
             'maxGive' : 0.20,
             'baseLvr' : 0.15,
             'baseLvrAge' : 60,
             'baseLvrIncrement' : 0.01,
             'apartmentLvrAdj' : 0.05,
             'establishmentFee':0.015
}

ECONOMIC={'inflationRate' :float(2.50),
          'investmentRate' : float(6.00),
          'housePriceInflation' : float(3.00),
          'interestRate' :float(1.50),
          'lendingMargin':float(4.40),
          'comparisonRateIncrement':float(0.06),
          'projectionAge' : 90
}

APP_SETTINGS={'incomeIntervals' : 500,
              'minProjectionPeriods': 16,
              'intRateStress':2,
              'hpiHighStressLevel':0,
              'hpiLowStressLevel':1.5,
}


