import csv

from apps.lib.globals import LOAN_LIMITS
from django.conf import settings

class LoanValidator():

    #Utility class to validate whether a loan meets HHC lending guidelines and restrictions
    #Object is established through passing loan and client dictionaries (with all required fields)
    #Two methods: chkClientDtails and getStatus return dictionaries (JSON like) with relevant details

    def __init__(self,loanDict,clientDict ):

        #Initialisation Variables
        self.aggDict = {}
        self.aggDict.update(loanDict)
        self.aggDict.update(clientDict)

        if self.aggDict['dwellingType']==0:
            self.isApartment=False
        else:
            self.isApartment = True

        if self.aggDict['loanType']==1:
            self.isCouple = True
            self.clientAge = min(self.aggDict['age_1'],self.aggDict['age_2'])
        else:
            self.isCouple = False
            self.clientAge = self.aggDict['age_1']

        if 'protectedEquity' not in self.aggDict.keys():
            self.aggDict['protectedEquity']=0

        #Limits
        self.maxLvr =0
        self.loanLimit=0
        self.refinanceLimit = 0
        self.giveLimit =0
        self.travelLimit=0

        #Status
        self.availableAmount = 0
        self.status=[]
        self.maxEstablishmentFee=0


    def chkClientDetails(self):
        #Checks basic borrower / loan restrictions
        status={}
        status['status']="Ok"

        #Check for minimum data points
        minimumData=['dwellingType','loanType','age_1','valuation', 'postcode']
        for item in minimumData:
            if self.aggDict[item]==None:
                status['status'] = "Error"
                status['details'] = 'Insufficient data'
                return status

        #Check Postcode

        reader = csv.reader(open(settings.BASE_DIR + '/apps/lib/Postcodes.csv', 'r'))
        pcodeDict = dict(reader)

        if str(self.aggDict['postcode']) in pcodeDict:
            pass
        else:
            status['status'] = "Error"
            status['details'] = 'Invalid Postcode'


        if self.aggDict['loanType'] == 1 and self.aggDict['age_2'] == None:
            status['status'] = "Error"
            status['details'] = 'Missing Age'
            return status

        # Check Age
        if self.clientAge < LOAN_LIMITS['minSingleAge']:
            status['status']="Error"
            status['details']='Youngest borrower must be 60'
            return status

        elif self.isCouple and self.clientAge < LOAN_LIMITS['minCoupleAge']:
            status['status'] = "Error"
            status['details'] = 'Youngest joint borrower must be 65'
            return status

        #Perform LVR calculations (for loan size validation)
        self.calcLVR()

        # Check Min Loan Size
        if self.maxLvr/100 * self.aggDict['valuation'] < LOAN_LIMITS['minLoanSize']:
            status['status'] = "Error"
            status['details'] = 'Minimum Loan Size cannot be met'

        return status


    def getStatus(self):
        # Provides detailed array based on primary purposes. Designed to be utilsied as the app procedures throught the application
        # Recognising that there can be interdependency between purposes

        #Note complication of establishment fee that reduces the usable loan proceeds
        #The totalLoanAmount is always correct based on % Establsihment Fee
        #The available amount is an estimate based on the maximum $ establishment fee (hence doesn't vary with the loan
        #size and cause user confusion)

        self.status = {}
        self.calcLVR()
        self.maxEstablishmentFee=self.loanLimit*(LOAN_LIMITS['establishmentFee']/(1+LOAN_LIMITS['establishmentFee']))

        self.totalLoanAmount= (self.aggDict['topUpAmount'] + self.aggDict['refinanceAmount'] + self.aggDict['giveAmount'] + self.aggDict['renovateAmount']
                               +self.aggDict['travelAmount'] + self.aggDict['careAmount'])*(1+LOAN_LIMITS['establishmentFee'])



        self.availableAmount=round(self.loanLimit - self.totalLoanAmount/(1+LOAN_LIMITS['establishmentFee'])-self.maxEstablishmentFee,0)
        #Available amount always deducts the maximum establishment fee, so need to add back the calculated establsihment
        #fee from the total Loan Amount


        self.status['maxLVR']=int(round(self.maxLvr,0))
        self.status['maxNetLoanAmount']=round(self.loanLimit-self.maxEstablishmentFee,0)
        self.status['availableAmount']=int(round(self.availableAmount,0))
        self.status['establishmentFee']=int(round(self.totalLoanAmount/(1+LOAN_LIMITS['establishmentFee'])*LOAN_LIMITS['establishmentFee'],0))
        self.status['totalLoanAmount']=int(round(self.totalLoanAmount,0))

        self.status['errors']=False
        self.chkStatusItem('availableStatus',self.availableAmount,int(0),"LT")
        self.chkStatusItem('minloanAmountStatus',int(round(self.totalLoanAmount,0)),LOAN_LIMITS['minLoanSize'],"LT")
        self.chkStatusItem('maxloanAmountStatus',int(round(self.totalLoanAmount,0)),self.loanLimit,"GTE")
        self.chkStatusItem('topUpStatus', self.aggDict['topUpAmount'], LOAN_LIMITS['maxTopUp'], "GTE")
        self.chkStatusItem('refinanceStatus', self.aggDict['refinanceAmount'], self.refinanceLimit, "GTE")
        self.chkStatusItem('giveStatus', self.aggDict['giveAmount'], self.giveLimit, "GTE")
        self.chkStatusItem('renovateStatus', self.aggDict['renovateAmount'], LOAN_LIMITS['maxReno'], "GTE")
        self.chkStatusItem('travelStatus', self.aggDict['travelAmount'], self.travelLimit, "GTE")
        self.chkStatusItem('careStatus', self.aggDict['careAmount'], LOAN_LIMITS['maxCare'], "GTE")

        print(self.status)
        return self.status

    def chkStatusItem(self,label,amount,limit,condition):
        #Utility function to check conditions and create response
        if condition=="LT":
            if amount < limit:
                itemStatus = "Error"
                self.status["errors"] = True
            else:
                itemStatus = "Ok"
        else:
            if amount > limit:
                itemStatus = "Error"
                self.status["errors"] = True
            else:
                itemStatus = "Ok"

        self.status[label]=itemStatus


    def calcLVR(self):

        # Calculate LVR
        lvr = LOAN_LIMITS['baseLvr'] + (self.clientAge - LOAN_LIMITS['baseLvrAge']) * LOAN_LIMITS['baseLvrIncrement']

        # Apartment Adjustment
        if self.isApartment:
            lvr = max(lvr - LOAN_LIMITS['apartmentLvrAdj'], 0)

        #Protected Equity
        lvr=lvr*(1-self.aggDict['protectedEquity']/100)

        if lvr<0:
            lvr=0

        # LVR
        self.maxLvr = lvr * 100

        #Limits
        self.loanLimit = int(round(lvr * self.aggDict['valuation'], 0))
        self.refinanceLimit=int(lvr * self.aggDict['valuation'] * LOAN_LIMITS['maxRefi'])
        self.giveLimit=int(lvr * self.aggDict['valuation'] * LOAN_LIMITS['maxGive'])
        self.travelLimit = int(lvr * self.aggDict['valuation'] * LOAN_LIMITS['maxTravel'])

