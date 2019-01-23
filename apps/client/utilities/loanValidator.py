
from .globals import LOAN_LIMITS

class LoanValidator():

    #Utility class to validate whether a loan meets HHC lending guidelines and restrictions
    #Object is established through passing loan and client dictionaries (with all required fields)
    #Two methods: chkClientDtails and getStatus return dictionaries (JSON like) with relevant details

    def __init__(self,loanDict,clientDict ):

        #Initialisation Variables
        self.aggDict = {}
        self.aggDict.update(loanDict)
        self.aggDict.update(clientDict)

        if self.aggDict['clientBuilding']=='House':
            self.aggDict['isApartment']=False
        else:
            self.aggDict['isApartment'] = True

        if self.aggDict['clientType'] == 'Couple':
            self.aggDict['isCouple'] = True
        else:
            self.aggDict['isCouple'] = False

        #Limits
        self.maxLvr =0
        self.loanLimit=0
        self.refinanceLimit = 0
        self.giveLimit =0
        self.travelLimit=0

        #Status
        self.availableAmount = 0
        self.status=[]

    def chkClientDetails(self):
        #Checks basic borrower / loan restrictions

        #Perform LVR calculations (for loan size validation)
        self.calcLVR()

        status={}
        status['status']="Ok"

        # Check Age
        if self.aggDict['clientAge'] < LOAN_LIMITS['minSingleAge']:
            status['status']="Error"
            status['details']='Youngest borrower must be 60'

        elif self.aggDict['isCouple'] and self.aggDict['clientAge'] < LOAN_LIMITS['minCoupleAge']:
            status['status'] = "Error"
            status['details'] = 'Youngest joint borrower must be 65'

        # Check Min Loan Size
        if self.maxLvr/100 * self.aggDict['clientValuation'] < LOAN_LIMITS['minLoanSize']:
            status['status'] = "Error"
            status['details'] = 'Minimum Loan Size cannot be met'

        return status


    def getStatus(self):
        # Provides detailed array based on primary purposes. Designed to be utilsied as the app procedures throught the application
        # Recognising that there can be interdependency between purposes

        self.status = {}
        self.calcLVR()
        self.availableAmount=self.loanLimit - self.aggDict['topUpAmount'] - self.aggDict['refinanceAmount'] - self.aggDict['giveAmount'] \
                              - self.aggDict['renovateAmount']-self.aggDict['travelAmount'] - self.aggDict['careAmount']

        self.status['maxLVR']=self.maxLvr
        self.status['maxLoanAmount']=self.maxLvr/100 * self.aggDict['clientValuation']
        self.status['availableAmount']=self.availableAmount

        self.chkStatusItem('availableStatus',self.availableAmount,0,"LTE")
        self.chkStatusItem('topUpStatus', self.aggDict['topUpAmount'], LOAN_LIMITS['maxTopUp'], "GTE")
        self.chkStatusItem('refinanceStatus', self.aggDict['refinanceAmount'], self.refinanceLimit, "GTE")
        self.chkStatusItem('giveStatus', self.aggDict['giveAmount'], self.giveLimit, "GTE")
        self.chkStatusItem('renovateStatus', self.aggDict['renovateAmount'], LOAN_LIMITS['maxReno'], "GTE")
        self.chkStatusItem('travelStatus', self.aggDict['travelAmount'], self.travelLimit, "GTE")
        self.chkStatusItem('careStatus', self.aggDict['careAmount'], LOAN_LIMITS['maxCare'], "GTE")

        return self.status

    def chkStatusItem(self,label,amount,limit,condition):
        #Utility function to check conditions and create response
        if condition=="LTE":
            if amount <= limit:
                itemStatus = "Error"
            else:
                itemStatus = "Ok"
        else:
            if amount > limit or amount > self.loanLimit:
                itemStatus = "Error"
            else:
                itemStatus = "Ok"

        self.status[label]=itemStatus


    def calcLVR(self):

        # Calculate LVR
        lvr = LOAN_LIMITS['baseLvr'] + (self.aggDict['clientAge'] - LOAN_LIMITS['baseLvrAge']) * LOAN_LIMITS['baseLvrIncrement']

        # Apartment Adjustment
        if self.aggDict['isApartment']:
            lvr = max(lvr - LOAN_LIMITS['apartmentLvrAdj'], 0)

        #Protected Equity
        lvr=lvr*(1-self.aggDict['protectedEquity'])

        if lvr<0:
            lvr=0

        # LVR
        self.maxLvr = lvr * 100

        #Limits
        self.loanLimit = int(round(lvr * self.aggDict['clientValuation'], 0))
        self.refinanceLimit=int(lvr * self.aggDict['clientValuation'] * LOAN_LIMITS['maxRefi'])
        self.giveLimit=int(lvr * self.aggDict['clientValuation'] * LOAN_LIMITS['maxGive'])
        self.travelLimit = int(lvr * self.aggDict['clientValuation'] * LOAN_LIMITS['maxTravel'])

