#Python Imports
import json
import pickle
from math import log

#Django Imports
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template,render_to_string
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View

#Third-party Imports
from api2pdf import Api2Pdf

#Local Application Imports
from .forms import ClientDetailsForm, SettingsForm, IntroChkBoxForm,topUpForm, debtRepayForm
from .forms import giveAmountForm, renovateAmountForm, travelAmountForm, careAmountForm, DetailedChkBoxForm
from .lib.globals import DEFAULT_CLIENT, ECONOMIC, LOAN, APP_SETTINGS
from .lib.loanValidator import LoanValidator
from .lib.loanProjection import LoanProjection


# MIXINS

class LoginRequiredMixin(object):
    #Ensures views will not render undless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

class ClientDataMixin(object):
    #Adds client data dictionaries to the context for relevant views
    def get_context_data(self, **kwargs):
        if 'clientDict' in self.request.session:
            if self.extra_context is None:
                self.extra_context={}
            self.extra_context.update(self.request.session['clientDict'])
        context = super(ClientDataMixin, self).get_context_data(**kwargs)
        return context

#Utilities
class ResultsHelper():

    def createResultsList(self, projFigures, keyName, **kwargs):
        # Builds a results list to pass to the template
        # Optionally calculates scaling for images

        scaleList = []

        figuresList = [int(projFigures[i][keyName]) for i in [0, 5, 10, 15]]

        if 'imageSize' in kwargs:
            if kwargs['imageMethod'] == 'exp':
                # Use a log scaling method for images (arbitrary)
                maxValueLog = self.logOrZero(max(figuresList)) ** 3
                if maxValueLog == 0:
                    maxValueLog = 1
                scaleList = [int(self.logOrZero(figuresList[i]) ** 3 / maxValueLog * kwargs['imageSize']) for i
                             in range(4)]
            elif kwargs['imageMethod'] == 'lin':
                maxValueLog = max(figuresList)
                scaleList = [int(figuresList[i] / maxValueLog * kwargs['imageSize']) for i in range(4)]

        return figuresList + scaleList

    def logOrZero(self, val):
        if val == 0:
            return 0
        return log(val)

    def createImageList(self, projFigures, keyName, imageURL):
        figuresList = [int(round(projFigures[i][keyName] / 10, 0)) for i in [0, 5, 10, 15]]
        imageList = [imageURL.replace('{0}', str(figuresList[i])) for i in range(4)]

        return imageList



# CLASS BASED VIEWS

# Landing View
class LandingView(LoginRequiredMixin, TemplateView):

    template_name = "client_1_0/landing.html"

    def get_context_data(self, **kwargs):

        #Add's client information to the context (if it exists) for navigation purposes
        context = super(LandingView,self).get_context_data(**kwargs)
        if 'clientDict' in self.request.session:
            context['clientSet'] = True
            context['clientSurname']=self.request.session["clientDict"]["clientSurname"]
            return context
        else:
            context['clientSet'] = False

        return context

    def get(self, request, *args, **kwargs):
        #As this is the intial view - sets up dictionaries to be used by the app (overriding the get method)
        #Add dictionaries to the session variables

        if 'economicDict' not in self.request.session:
            economicDict={}
            economicDict.update(ECONOMIC)
            self.request.session['economicDict']=economicDict

        if 'loanDict' not in self.request.session:
            loanDict={}
            loanDict.update(LOAN)
            self.request.session['loanDict'] = loanDict

        return super(LandingView,self).get(self, request, *args, **kwargs)


# Introduction Views
class IntroductionView1(LoginRequiredMixin, ClientDataMixin, TemplateView):

    template_name = "client_1_0/introduction1.html"

    def get_context_data(self, **kwargs):
        context = super(IntroductionView1,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:landing')
        context['nextUrl']=reverse_lazy('client:introduction2')
        return context

class IntroductionView2(LoginRequiredMixin, ClientDataMixin, FormView):

    template_name = "client_1_0/introduction2.html"
    form_class=IntroChkBoxForm
    success_url = reverse_lazy('client:introduction3')

    def get_context_data(self, **kwargs):
        context = super(IntroductionView2,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction1')
        context['nextIsButton']=True
        context.update(self.request.session['clientDict'])
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Please confirm your objectives ")
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        #All three check boxes to be checked
        if len(form.cleaned_data['clientChoices'])==3:
            # if ok, add to dictionary and render the success_url as normal
            loanDict=self.request.session['loanDict']
            loanDict['clientChoices']={'clientRetireAtHome':True,
                                         'clientAvoidDownsizing':True,
                                         'clientAccessFunds':True}
            self.request.session['loanDict']=loanDict

            return super(IntroductionView2, self).form_valid(form)
        else:
            messages.error(self.request, "Please confirm your objectives ")
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        initFormData= super(IntroductionView2, self).get_initial()
        if 'clientDict' in self.request.session:
            initFormData.update(self.request.session["clientDict"])
        return initFormData.copy()

class IntroductionView3(LoginRequiredMixin, ClientDataMixin, TemplateView):

    template_name = "client_1_0/introduction3.html"

    def get_context_data(self, **kwargs):
        context = super(IntroductionView3,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction2')
        context['nextUrl']=reverse_lazy('client:introduction4')

        # Loan Validation
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatus=loanObj.getStatus()
        context.update(loanStatus)

        return context

class IntroductionView4(LoginRequiredMixin, ClientDataMixin, TemplateView):

    template_name = "client_1_0/introduction4.html"

    def get_context_data(self, **kwargs):
        context = super(IntroductionView4,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction3')
        context['nextUrl']=reverse_lazy('client:topUp1')
        context['clientPensionAnnual']=context['clientPension']*26

        #Page uses post_id (slug) to expose images using same view
        context['post_id']=kwargs.get("post_id")

        context['imgPath'] = settings.STATIC_URL + 'img/'

        return context


# Top Up Views
class TopUp1(LoginRequiredMixin, ClientDataMixin, TemplateView):
        template_name = "client_1_0/topUp1.html"

        def get_context_data(self, **kwargs):
            context = super(TopUp1, self).get_context_data(**kwargs)
            context['title'] = 'Top Up'
            context['previousUrl'] = reverse_lazy('client:introduction4')+"/4"
            context['nextUrl'] = reverse_lazy('client:topUp2')

            # Page uses post_id (slug) to expose images using same view
            context['post_id'] = kwargs.get("post_id")

            # Loan Status Information
            loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
            loanStatusDict = loanObj.getStatus()

            print("Set projection")
            loanProj = LoanProjection(self.request.session['clientDict'],
                                      self.request.session['loanDict'],
                                      self.request.session['economicDict'],
                                      loanStatusDict)

            projectionAge=loanProj.getProjectionAge()
            print("Get initial")
            currentIncomeProj = loanProj.getInitialIncome()
            print("Get max")
            boostedIncomeProj = loanProj.getMaxEnhancedIncome()
            context['currentIncomeProj']=int(currentIncomeProj)
            context['boostedIncomeProj']=int(boostedIncomeProj)
            context['projectionAge']=projectionAge

            return context

class TopUp2(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client_1_0/topUp2.html"
    form_class=topUpForm
    success_url = reverse_lazy('client:topUp3')

    def get_context_data(self, **kwargs):
        context = super(TopUp2, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['previousUrl'] = reverse_lazy('client:topUp1') + "/1"
        context['nextIsButton']=True

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()

        loanProj = LoanProjection(self.request.session['clientDict'],
                                  self.request.session['loanDict'],
                                  self.request.session['economicDict'],
                                  loanStatusDict)

        sliderData = loanProj.getEnhancedIncomeArray()
        currentIncomeProj = loanProj.getInitialIncome()
        boostedIncomeProj = loanProj.getMaxEnhancedIncome()

        context['currentIncomeProj'] = int(currentIncomeProj)
        context['boostedIncomeProj'] = int(boostedIncomeProj)
        context['sliderData']=json.dumps(sliderData)
        context['sliderPoints']=APP_SETTINGS['incomeIntervals']
        context['imgPath']=settings.STATIC_URL+'img/icons/equity_10_icon.png'
        self.request.session['clientDict']

        return context

    def form_valid(self, form):
        loanDict = self.request.session['loanDict']
        loanDict['topUpAmount'] = int(form.cleaned_data['topUpAmount'])
        loanDict['topUpIncome'] = int(form.cleaned_data['topUpIncome'])

        loanDict['annualPensionIncome']=int(self.request.session['clientDict']['clientPension']*26)
        loanDict['incomeObjective']=loanDict['topUpIncome']+loanDict['annualPensionIncome']



        self.request.session['loanDict'] = loanDict

        return super(TopUp2, self).form_valid(form)


class TopUp3(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client_1_0/topUp3.html"
    form_class=debtRepayForm
    success_url = reverse_lazy('client:live1')

    def get_context_data(self, **kwargs):
        context = super(TopUp3, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['previousUrl'] = reverse_lazy('client:topUp2')
        context['nextIsButton']=True

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        context.update(loanStatusDict)
        context.update(self.request.session['clientDict'])
        context.update(self.request.session['loanDict'])

        return context

    def form_valid(self, form):
        #number formatting and validation
        loanDict = self.request.session['loanDict']
        #Data has been validated - can be converted to float
        loanDict['refinanceAmount'] = int(form.cleaned_data['clientMortgageDebt'].replace(",",""))
        self.request.session['loanDict'] = loanDict

        return super(TopUp3, self).form_valid(form)

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        initFormData= super(TopUp3, self).get_initial()
        if self.request.session['loanDict']['refinanceAmount']!=0:
            initFormData["clientMortgageDebt"] = "{:,}".format(self.request.session['loanDict']['refinanceAmount'])
        else:
           initFormData["clientMortgageDebt"]="{:,}".format(self.request.session["clientDict"]['clientMortgageDebt'])

        return initFormData



# Live Views
class Live1(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client_1_0/live1.html"
    form_class=renovateAmountForm
    success_url = reverse_lazy('client:live2')

    def get_context_data(self, **kwargs):
        context = super(Live1, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['previousUrl'] = reverse_lazy('client:topUp3')
        context['nextIsButton']=True

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        context.update(loanStatusDict)
        context.update(self.request.session['clientDict'])
        context.update(self.request.session['loanDict'])

        return context

    def form_valid(self, form):
        #number formatting and validation
        loanDict = self.request.session['loanDict']
        loanDict['renovateAmount'] = int(form.cleaned_data['renovateAmount'].replace(",",""))
        loanDict['renovateDescription']=form.cleaned_data['renovateDescription']
        self.request.session['loanDict'] = loanDict

        return super(Live1, self).form_valid(form)

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        initFormData= super(Live1, self).get_initial()
        if self.request.session['loanDict']['renovateAmount']!=0:
            initFormData["renovateAmount"]=self.request.session['loanDict']['renovateAmount']
            initFormData["renovateDescription"] = self.request.session['loanDict']['renovateDescription']
        else:
            initFormData["renovateAmount"] = int(0)

        return initFormData

class Live2(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client_1_0/live2.html"
    form_class=travelAmountForm
    success_url = reverse_lazy('client:give')

    def get_context_data(self, **kwargs):
        context = super(Live2, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['previousUrl'] = reverse_lazy('client:live1')
        context['nextIsButton']=True

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        context.update(loanStatusDict)
        context.update(self.request.session['clientDict'])
        context.update(self.request.session['loanDict'])
        return context

    def form_valid(self, form):
        #number formatting and validation
        loanDict = self.request.session['loanDict']
        loanDict['travelAmount'] = int(form.cleaned_data['travelAmount'].replace(",",""))
        loanDict['travelDescription']=form.cleaned_data['travelDescription']
        self.request.session['loanDict'] = loanDict

        return super(Live2, self).form_valid(form)

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        initFormData= super(Live2, self).get_initial()
        if self.request.session['loanDict']['travelAmount']!=0:
            initFormData["travelAmount"]=self.request.session['loanDict']['travelAmount']
            initFormData["travelDescription"] = self.request.session['loanDict']['travelDescription']
        else:
            initFormData["travelAmount"] = int(0)

        return initFormData




# Give Views
class Give(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client_1_0/give.html"
    form_class=giveAmountForm
    success_url = reverse_lazy('client:care')

    def get_context_data(self, **kwargs):
        context = super(Give, self).get_context_data(**kwargs)
        context['title'] = 'Give'
        context['previousUrl'] = reverse_lazy('client:live1')
        context['nextIsButton']=True

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        context.update(loanStatusDict)
        context.update(self.request.session['clientDict'])
        context.update(self.request.session['loanDict'])
        return context

    def form_valid(self, form):
        #number formatting and validation
        loanDict = self.request.session['loanDict']
        loanDict['giveAmount'] = int(form.cleaned_data['giveAmount'].replace(",",""))
        loanDict['giveDescription']=form.cleaned_data['giveDescription']
        loanDict['protectedEquity'] = int(form.cleaned_data['protectedEquity'])
        self.request.session['loanDict'] = loanDict

        return super(Give, self).form_valid(form)

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        initFormData= super(Give, self).get_initial()
        if self.request.session['loanDict']['giveAmount']!=0:
            initFormData["giveAmount"]=self.request.session['loanDict']['giveAmount']
            initFormData["giveDescription"] = self.request.session['loanDict']['giveDescription']
        else:
            initFormData["giveAmount"] = int(0)

        if self.request.session['loanDict']['protectedEquity']!=0:
            initFormData["protectedEquity"] = self.request.session['loanDict']['protectedEquity']
        else:
            initFormData["protectedEquity"]=int(0)

        return initFormData





# Care Views
class Care(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client_1_0/care.html"
    form_class=careAmountForm
    success_url = reverse_lazy('client:results1')

    def get_context_data(self, **kwargs):
        context = super(Care, self).get_context_data(**kwargs)
        context['title'] = 'Care'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextIsButton']=True

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        context.update(loanStatusDict)
        context.update(self.request.session['clientDict'])
        context.update(self.request.session['loanDict'])
        return context

    def form_valid(self, form):
        #number formatting and validation
        loanDict = self.request.session['loanDict']
        loanDict['careAmount'] = int(form.cleaned_data['careAmount'].replace(",",""))
        loanDict['careDescription']=form.cleaned_data['careDescription']
        self.request.session['loanDict'] = loanDict

        return super(Care, self).form_valid(form)

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        initFormData= super(Care, self).get_initial()
        if self.request.session['loanDict']['careAmount']!=0:
            initFormData["careAmount"]=self.request.session['loanDict']['careAmount']
            initFormData["careDescription"] = self.request.session['loanDict']['careDescription']
        else:
            initFormData["careAmount"] = int(0)

        return initFormData


# Results Views

class Results1(LoginRequiredMixin, ClientDataMixin, TemplateView):
    template_name = "client_1_0/results1.html"

    def get(self, request, *args, **kwargs):
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        if loanStatusDict['errors']==False:
            return HttpResponseRedirect(reverse_lazy('client:results2'))
        return super(Results1, self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(Results1, self).get_context_data(**kwargs)
        context['title'] = 'Results'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextUrl']=reverse_lazy('client:results1')

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        context.update(loanStatusDict)
        context.update(self.request.session['clientDict'])
        context.update(self.request.session['loanDict'])
        return context


class Results2(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client_1_0/results2.html"
    form_class=DetailedChkBoxForm
    success_url = reverse_lazy('client:results3')

    def get_context_data(self, **kwargs):
        context = super(Results2, self).get_context_data(**kwargs)
        context['title'] = 'Results'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextIsButton']=True

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        context.update(loanStatusDict)
        context.update(self.request.session['clientDict'])
        context.update(self.request.session['loanDict'])
        return context

    def form_valid(self, form):
        #update client dictionary
        loanDict=self.request.session['loanDict']
        loanDict['clientChoices'].update(form.cleaned_data)

        #update loan dictionary (calculate the establishment fee)
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()
        loanDict['establishmentFee']=int(round(loanStatusDict['establishmentFee'],0))

        # update loan dictionary (totalLoanAmount)
        loanDict['totalLoanAmount'] = int(round(loanStatusDict['totalLoanAmount'],0))

        self.request.session['loanDict'] = loanDict

        return super(Results2, self).form_valid(form)


    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        self.initFormData= super(Results2, self).get_initial()

        self.setInitialValues('clientTopUp',[self.request.session['loanDict']['topUpAmount']])
        self.setInitialValues('clientRefinance',[self.request.session['loanDict']['refinanceAmount']])
        self.setInitialValues('clientGive',[self.request.session['loanDict']['giveAmount']])
        self.setInitialValues('clientReserve',[self.request.session['loanDict']['protectedEquity']])
        self.setInitialValues('clientLive', [self.request.session['loanDict']['renovateAmount'],
                                             self.request.session['loanDict']['travelAmount']])
        self.setInitialValues('clientCare',[self.request.session['loanDict']['careAmount']])

        return self.initFormData

    def setInitialValues(self,fieldName, dictName):

        initial=False
        for field in dictName:
            if field!=0:
               initial=True

        self.initFormData[fieldName]=initial


class Results3(ResultsHelper, LoginRequiredMixin, ClientDataMixin, TemplateView):
    template_name = "client_1_0/results3.html"
    success_url = reverse_lazy('client:pdfProduction')

    def get_context_data(self, **kwargs):
        context = super(Results3, self).get_context_data(**kwargs)

        context['title'] = 'Results'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextIsButton'] = True

        #Key Dictionaries
        context.update(self.request.session['loanDict'])
        context.update(self.request.session['economicDict'])

        # Loan Status Information
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatusDict = loanObj.getStatus()

        loanProj = LoanProjection(self.request.session['clientDict'],
                                  self.request.session['loanDict'],
                                  self.request.session['economicDict'],
                                  loanStatusDict)

        projectionFigures=loanProj.getProjections()
        print(projectionFigures)

        #Build results dictionaries

        #Check for no top-up Amount
        if context["topUpAmount"]==0:
            context['topUpProjections']=False
        else:
            context['topUpProjections'] = True
            context['resultsCumulative'] = self.createResultsList(projectionFigures,'CumulativeSuperIncome', imageSize=100,
                                                                  imageMethod='exp')
            context['resultsTotalIncome'] = self.createResultsList(projectionFigures,'TotalIncome', imageSize=150, imageMethod='lin')
            context['resultsSuperBalance'] = self.createResultsList(projectionFigures,'BOPBalance', imageSize=100, imageMethod='exp')
            context['resultsIncomeImages'] = self.createImageList(projectionFigures,'PensionIncomePC',
                                                                  settings.STATIC_URL + 'img/icons/income_{0}_icon.png')

        context['resultsAge']=self.createResultsList(projectionFigures,'BOPAge')
        context['resultsHomeEquity'] = self.createResultsList(projectionFigures,'BOPHomeEquity')
        context['resultsHomeEquityPC'] = self.createResultsList(projectionFigures,'BOPHomeEquityPC')
        context['resultsHomeImages'] = self.createImageList(projectionFigures,'BOPHomeEquityPC',
                                                              settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')
        context['resultsHouseValue'] = self.createResultsList(projectionFigures,'BOPHouseValue', imageSize=100, imageMethod='lin')

        context['totalInterestRate']=context['interestRate']+context['lendingMargin']

        context['resultsNegAge']=loanProj.getNegativeEquityAge()



        #Temporary

        dir=settings.MEDIA_ROOT

        pickle_out = open(settings.MEDIA_ROOT+"/clientDict", "wb")
        pickle.dump(self.request.session['clientDict'], pickle_out)
        pickle_out.close()

        pickle_out = open(settings.MEDIA_ROOT + "/loanDict", "wb")
        pickle.dump(self.request.session['loanDict'], pickle_out)
        pickle_out.close()

        pickle_out = open(settings.MEDIA_ROOT + "/economicDict", "wb")
        pickle.dump(self.request.session['economicDict'], pickle_out)
        pickle_out.close()


        return context


# Settings Views
class SetClientView(LoginRequiredMixin, FormView):

    #Sets the initial client data (in associated dictionary)

    template_name = "client_1_0/settings.html"
    form_class=ClientDetailsForm
    success_url = reverse_lazy('client:landing')

    def get_context_data(self, **kwargs):
        context = super(SetClientView, self).get_context_data(**kwargs)
        context['title'] = 'Client Information'
        context['hideMenu'] = True
        return context

    def form_valid(self, form):

        # remove clientDict from the session if already exists
        if 'clientDict' in self.request.session.items():
            self.request.session.pop('clientDict')

        # create new client dictionary from the form data and save to the session
        clientDict={}
        clientDict=form.cleaned_data.copy()
        self.request.session['clientDict'] = clientDict

        # perform high-level validation of client data, using HHC_Loan object
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        chkResponse=loanObj.chkClientDetails()

        if chkResponse['status']=="Ok":
            #if ok, renders the success_url as normal
            return super(SetClientView, self).form_valid(form)
        else:
            #if error, renders the same page again with error message
            messages.error(self.request, chkResponse['details'])
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

    def get_initial(self):
        #Uses the details saved in the client dictionary for the form, unless this doesn't exist,
        #in which case the temporary default settings are used

        initFormData = super(SetClientView, self).get_initial()

        if 'clientDict' in self.request.session:
            initFormData.update(self.request.session["clientDict"])
        else:
            initFormData.update(DEFAULT_CLIENT)
        return initFormData.copy()





class SettingsView(LoginRequiredMixin, FormView):

    template_name = "client_1_0/settings.html"
    form_class=SettingsForm
    success_url = reverse_lazy('client:introduction1')

    def get_context_data(self, **kwargs):
        context = super(SettingsView, self).get_context_data(**kwargs)
        context['title'] = 'Economic Settings'
        context['hideMenu'] = True
        return context

    def form_valid(self, form):

        # save form details to relevant dictionary (and session)
        if 'economicDict' in self.request.session.items():
            self.request.session.pop('economicDict')

        # create new settingsDict dictionary
        economicDict={}
        economicDict=form.cleaned_data.copy()

        self.request.session['economicDict'].update(economicDict)

        return super(SettingsView, self).form_valid(form)

    def get_initial(self):
        #Uses the current settings for the form values, unless this hasn't been saved yet
        #in which case the defaults are loaded and saved

        initFormData = super(SettingsView, self).get_initial()

        if 'clientDict' in self.request.session:
            initFormData.update(self.request.session["economicDict"])
        else:
            initFormData.update(ECONOMIC)
        return initFormData.copy()



# / PDF Generation View (not rendered)

class pdfProduction(View):

    def __init__(self):
            self.a2p_client = Api2Pdf(APP_SETTINGS['Api2PdfKey'])

    def get(self,request):

        options={'preferCSSPageSize':True, 'marginBottom':0, 'marginLeft':0, 'marginRight':0,'marginTop':0,
                 'paperWidth':8.27,'paperHeight':11.69}
        api_response = self.a2p_client.HeadlessChrome.convert_from_url('https://householdcapital.app/client/pdfReport',
                                                                       inline_pdf=True, **options)
        return HttpResponseRedirect(api_response.result['pdf'])

class pdfReport(ResultsHelper,TemplateView):
    template_name = "client_1_0/summaryDocument/mainDocument.html"

    def get_context_data(self, **kwargs):
        context = super(pdfReport, self).get_context_data(**kwargs)

        # Temporary

        dir = settings.MEDIA_ROOT

        pickle_in = open(settings.MEDIA_ROOT + "/clientDict", "rb")
        clientDict = pickle.load(pickle_in)
        pickle_in.close()

        pickle_in = open(settings.MEDIA_ROOT + "/loanDict", "rb")
        loanDict = pickle.load(pickle_in)
        pickle_in.close()

        pickle_in = open(settings.MEDIA_ROOT + "/economicDict", "rb")
        economicDict = pickle.load(pickle_in)
        pickle_in.close()

        loanObj = LoanValidator(clientDict, loanDict)
        loanStatusDict = loanObj.getStatus()

        # Key Dictionaries

        context.update(loanStatusDict)
        context.update(clientDict)
        context.update(loanDict)
        context.update(economicDict)

        loanProj = LoanProjection(clientDict,
                                  loanDict,
                                  economicDict,
                                  loanStatusDict)

        #Get projection figures
        projectionFigures=loanProj.getProjections()

        # Build results dictionaries, using helper functions
        # Build results dictionaries

        # Check for no top-up Amount
        if context["topUpAmount"] == 0:
            context['topUpProjections'] = False
        else:
            context['topUpProjections'] = True
            context['resultsCumulative'] = self.createResultsList(projectionFigures, 'CumulativeSuperIncome',
                                                                  imageSize=100,
                                                                  imageMethod='exp')
            context['resultsTotalIncome'] = self.createResultsList(projectionFigures, 'TotalIncome', imageSize=150,
                                                                   imageMethod='lin')
            context['resultsSuperBalance'] = self.createResultsList(projectionFigures, 'BOPBalance', imageSize=100,
                                                                    imageMethod='exp')
            context['resultsIncomeImages'] = self.createImageList(projectionFigures, 'PensionIncomePC',
                                                                  settings.STATIC_URL + 'img/icons/income_{0}_icon.png')

        context['resultsAge'] = self.createResultsList(projectionFigures, 'BOPAge')
        context['resultsHomeEquity'] = self.createResultsList(projectionFigures, 'BOPHomeEquity')
        context['resultsHomeEquityPC'] = self.createResultsList(projectionFigures, 'BOPHomeEquityPC')
        context['resultsHomeImages'] = self.createImageList(projectionFigures, 'BOPHomeEquityPC',
                                                            settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')
        context['resultsHouseValue'] = self.createResultsList(projectionFigures, 'BOPHouseValue', imageSize=100,
                                                              imageMethod='lin')

        context['totalInterestRate'] = context['interestRate'] + context['lendingMargin']

        context['comparisonRate']=context['totalInterestRate']+context['comparisonIncrement']
        context['resultsNegAge'] = loanProj.getNegativeEquityAge()


        #Stress Results
        projectionSmallHpi = loanProj.getProjections(hpiStressLevel=APP_SETTINGS['hpiLowStressLevel'])
        projectionNoHpi = loanProj.getProjections(hpiStressLevel=APP_SETTINGS['hpiHighStressLevel'])
        projectionRateUp = loanProj.getProjections(intRateStress=APP_SETTINGS['intRateStress'])

        context['hpi1']=APP_SETTINGS['hpiLowStressLevel']
        context['intRate1']=context['totalInterestRate']

        context['hpi2']=APP_SETTINGS['hpiHighStressLevel']
        context['intRate2']=context['totalInterestRate']

        context['hpi3']=context['housePriceInflation']
        context['intRate3']=context['totalInterestRate']+APP_SETTINGS['intRateStress']

        # Stress-1
        context['resultsHomeEquity1'] = self.createResultsList(projectionSmallHpi,'BOPHomeEquity')
        context['resultsHomeEquityPC1'] = self.createResultsList(projectionSmallHpi,'BOPHomeEquityPC')
        context['resultsHomeImages1'] = self.createImageList(projectionSmallHpi,'BOPHomeEquityPC',
                                                              settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')
        context['resultsHouseValue1'] = self.createResultsList(projectionSmallHpi,'BOPHouseValue', imageSize=100, imageMethod='lin')

        # Stress-2
        context['resultsHomeEquity2'] = self.createResultsList(projectionNoHpi,'BOPHomeEquity')
        context['resultsHomeEquityPC2'] = self.createResultsList(projectionNoHpi,'BOPHomeEquityPC')
        context['resultsHomeImages2'] = self.createImageList(projectionNoHpi,'BOPHomeEquityPC',
                                                              settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')
        context['resultsHouseValue2'] = self.createResultsList(projectionNoHpi,'BOPHouseValue', imageSize=100, imageMethod='lin')

        # Stress-3
        context['resultsHomeEquity3'] = self.createResultsList(projectionRateUp, 'BOPHomeEquity')
        context['resultsHomeEquityPC3'] = self.createResultsList(projectionRateUp, 'BOPHomeEquityPC')
        context['resultsHomeImages3'] = self.createImageList(projectionRateUp, 'BOPHomeEquityPC',
                                                              settings.STATIC_URL + 'img/icons/equity_{0}_icon.png')
        context['resultsHouseValue3'] = self.createResultsList(projectionRateUp, 'BOPHouseValue', imageSize=100,
                                                                imageMethod='lin')

        return context




