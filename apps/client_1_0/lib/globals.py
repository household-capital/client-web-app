

# Test Harness Variables

DEFAULT_CLIENT={'clientDescription':'Murray - Neutral Bay',
                'clientSurname': 'Murray',
                'clientFirstname':'Paul',
                'clientAge':70,
                'clientStreet':'14 Hayes Street, Neutral Bay',
                'clientPostcode':'2089',
                'clientValuation':500000,
                'clientMortgageDebt':'0',
                'clientSuperName':'Sunsuper',
                'clientSuperAmount':100000,
                'clientPension':916,
                'dwelling':'House',
                'clientType':'Single'
}

# Application Globals

LOAN_LIMITS={'minSingleAge' : 60,
             'minCoupleAge' : 65,
             'minLoanSize' : 30000,
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

ECONOMIC={'inflation' :float(2.50),
          'investmentReturn' : float(6.00),
          'housePriceInflation' : float(3.00),
          'interestRate' :float(1.50),
          'lendingMargin':float(4.40),
          'comparisonIncrement':float(0.06)
}

APP_SETTINGS={'projectionAge' : 90,
              'incomeIntervals' : 50,
              'minProjectionPeriods': 16,
              'intRateStress':2,
              'hpiHighStressLevel':0,
              'hpiLowStressLevel':1.5,
              'Api2PdfKey':'748cd2c9-6239-4c49-8d33-4dab286e4eda'
}

LOAN={  'protectedEquity':int(0),
        'topUpAmount':int(0),
        'topUpIncome':int(0),
        'refinanceAmount':int(0),
        'giveAmount':int(0),
        'renovateAmount':int(0),
        'travelAmount':int(0),
        'careAmount':int(0),
        'totalLoanAmount':int(0),
        'establishmentFee':int(0),
        'giveDescription':'',
        'renovateDescription': '',
        'travelDescription':'',
        'careDescription':'',
        'incomeObjective':int(0),
        'annualPensionIncome':int(0),
        'clientChoices':{}}
