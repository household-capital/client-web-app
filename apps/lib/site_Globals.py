# Application Globals

LOAN_LIMITS = {
    # Age
    'minSingleAge': 60,
    'minCoupleAge': 60,

    # Loan Size
    'minLoanSize': 20000,
    'minIncomeDrawdown': 500,

    # Tenor
    'maxDrawdownYears': 1,

    # Purposes
    'maxTopUp': 500000,
    'maxCare': 550000,
    'maxReno': 200000,
    'maxRefi': 1.00,
    'maxTravel': 0.20,
    'maxGive': 0.20,
    'topUpBufferAmount': 5000,  # deprecated

    # Home Value
    'minHomeValue': 100000,
    'maxHomeValue': 5000000,

    # LVR Components
    'baseLvr': 0.15,
    'baseLvrAge': 60,
    'baseLvrIncrement': 0.01,
    'apartmentLvrAdj': 0.05,

    # Fees
    'establishmentFee': 0.015,

    # Detailed Title
    'titleUtilTrigger': 0.60,
    'titleAmountTrigger': 400000,

    # Product Specific
    'lumpSum20K': 20000,
    'lumpSumMinHomeValue': 400000
}

ECONOMIC = {'inflationRate': float(2.50),
            'housePriceInflation': float(3.00),
            'interestRate': float(0.75),
            'lendingMargin': float(4.40),
            'comparisonRateIncrement': float(0.06),
            'defaultMargin': float(2.00),
            }

APP_SETTINGS = {'minProjectionYears': 15,
                'intRateStress': 2,
                'hpiHighStressLevel': 0,
                'hpiLowStressLevel': 1.5,
                }
