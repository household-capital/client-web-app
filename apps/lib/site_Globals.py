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
            'interestRate': float(0.10),
            'lendingMargin': float(4.85),
            'comparisonRateIncrement': float(0.06),
            'defaultMargin': float(2.00),
            }

LOAN_LIMITS_PRODUCT_TYPE = {
    "HHC.RM.2021": {
        "FEE_TYPE": "FLAT",
        "ESTABLISHMENT_FEE_AMOUNT": 950,
        # Drawdowns fees
        "DRAWDOWN_FEE_TYPE": None,
        "DRAWDOWN_FEE_AMOUNT": None,
        # Variations fees
        "VARIATION_FEE_TYPE": "FLAT",
        "VARIATION_FEE_AMOUNT": 250,
        # Discharge fees
        "DISCHARGE_FEE_TYPE": "FLAT",
        "DISCHARGE_FEE_AMOUNT": 250
    },
    "HHC.RM.2018": {
        "FEE_TYPE": "PERCENTAGE",
        "ESTABLISHMENT_FEE_AMOUNT": 0.015,
        # Drawdowns fees
        "DRAWDOWN_FEE_TYPE": "PERCENTAGE",
        "DRAWDOWN_FEE_AMOUNT": 0.015,
        # Variations fees
        "VARIATION_FEE_TYPE": None,
        "VARIATION_FEE_AMOUNT": None,
        # Discharge fees
        "DISCHARGE_FEE_TYPE": None,
        "DISCHARGE_FEE_AMOUNT": None
    }
} 

APP_SETTINGS = {'minProjectionYears': 15,
                'incomeProjectionYears': 10,
                'intRateStress': 2,
                'hpiHighStressLevel': 0,
                'hpiLowStressLevel': 1.5,
                }
