#Python Imports
import datetime
import json
from math import log

#Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.files import File
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView, View, UpdateView


#Local Application Imports
from apps.case.models import ModelSetting, Loan, Case
from apps.lib.enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,pensionTypesEnum, loanTypesEnum
from apps.lib.globals import ECONOMIC, APP_SETTINGS
from apps.lib.loanValidator import LoanValidator
from apps.lib.loanProjection import LoanProjection
from apps.logging import write_applog
from .forms import ClientDetailsForm, SettingsForm, IntroChkBoxForm,topUpForm, debtRepayForm
from .forms import giveAmountForm, renovateAmountForm, travelAmountForm, careAmountForm, DetailedChkBoxForm
from apps.lib.utilities import pdfGenerator


# MIXINS

class LoginRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

    # Ensures views will not render unless Household employee, redirects to Landing
    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))

class SessionRequiredMixin(object):
    #Ensures any attempt to acces without UID set is redirct to list view
    def dispatch(self, request, *args, **kwargs):
        if 'caseUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('case:caseList'))
        return super(SessionRequiredMixin, self).dispatch(request, *args, **kwargs)


# UTILITIES

class ResultsHelper():
    # Used to render Loan Projection results for the GUI and Summary Document

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
        if val <= 0:
            return 0
        return log(val)

    def createImageList(self, projFigures, keyName, imageURL):
        figuresList = [int(round(projFigures[i][keyName] / 10, 0)) for i in [0, 5, 10, 15]]
        imageList = [imageURL.replace('{0}', str(figuresList[i])) for i in range(4)]

        return imageList

class ContextHelper():
    # Most of the views require the same validation and context information

    def validate_and_get_context(self):
        #get dictionaries from model
        clientDict=Case.objects.dictionary_byUID(self.request.session['caseUID'])
        loanDict=Loan.objects.dictionary_byUID(self.request.session['caseUID'])
        modelDict=ModelSetting.objects.dictionary_byUID(self.request.session['caseUID'])

        #validate loan
        loanObj = LoanValidator(clientDict, loanDict)
        loanStatus=loanObj.getStatus()

        #update loan
        loanQS = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        loanQS.update(maxLVR=loanStatus['maxLVR'],
                      totalLoanAmount=loanStatus['totalLoanAmount'],
                      establishmentFee=loanStatus['establishmentFee'],
                      actualLVR=loanStatus['actualLVR'])

        #create context
        context = {}
        context.update(clientDict)
        context.update(loanDict)
        context.update(modelDict)
        context.update(loanStatus)

        context['caseTypesEnum']=caseTypesEnum
        context['clientSexEnum'] = clientSexEnum
        context['clientTypesEnum'] = clientTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum
        context['pensionTypesEnum'] = pensionTypesEnum
        context['loanTypesEnum'] = loanTypesEnum

        return context


# CLASS BASED VIEWS

# Landing View
class LandingView(LoginRequiredMixin, ContextHelper ,TemplateView):

    template_name = "client_1_0/interface/landing.html"

    def get_context_data(self, **kwargs):

        self.extra_context = self.validate_and_get_context()

        #Add's client information to the context (if it exists) for navigation purposes
        context = super(LandingView,self).get_context_data(**kwargs)

        #Set Initial Parameters - Potentially Undefined/None
        # Pension Income
        loanObj= Loan.objects.queryset_byUID(self.request.session['caseUID'])
        caseObj= Case.objects.queryset_byUID(self.request.session['caseUID'])

        if self.extra_context['pensionAmount']!=None:
            loanObj.update(annualPensionIncome=self.extra_context['pensionAmount']*26)
        else:
            loanObj.update(annualPensionIncome=0)

        # mortgageDebt
        if self.extra_context['mortgageDebt']==None:
            caseObj.update(mortgageDebt=0)

        # mortgageDebt
        if self.extra_context['superAmount'] == None:
            caseObj.update(superAmount=0)

        # Check and set consents/meeting date
        if context['consentPrivacy']==True and context['consentElectronic']==True:
            context['post_id']=2
        else:
            if 'post_id' in kwargs:
                context['post_id'] = kwargs['post_id']
                if kwargs['post_id']==1:
                    loanObj.update(consentPrivacy=True)
                if kwargs['post_id']==2:
                    loanObj.update(consentElectronic=True)
                    caseObj.update(meetingDate = datetime.datetime.now())


        return context

    def get(self, request, *args, **kwargs):

        if 'uid' in kwargs:
            #Main entry view - save the UID into a session variable
            #Use this to retrieve queryset for each page

            caseUID=str(kwargs['uid'])
            request.session['caseUID']=caseUID
            write_applog("INFO", 'LandingView', 'get', "Meeting commenced by "+str(request.user)+" for -"+ caseUID )

            obj=ModelSetting.objects.queryset_byUID(caseUID)
            obj.update(**ECONOMIC)

        if 'caseUID' not in request.session:
            return HttpResponseRedirect(reverse_lazy('case:caseList'))

        return super(LandingView,self).get(self, request, *args, **kwargs)


# Settings Views
class SetClientView(LoginRequiredMixin, SessionRequiredMixin, ContextHelper, UpdateView):
    # Sets the initial client data (in associated dictionary)

    template_name = "client_1_0/interface/settings.html"
    form_class = ClientDetailsForm
    model = Case
    success_url = reverse_lazy('client:meetingStart')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(SetClientView, self).get_context_data(**kwargs)
        context['title'] = 'Client Information'
        context['hideMenu'] = True

        return context

    def get_object(self, queryset=None):
        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj

    def form_valid(self, form):

        self.object = form.save()

        if form.cleaned_data['resetConsents']:

            loanQs = Loan.objects.queryset_byUID(self.request.session['caseUID'])
            loanRecord = loanQs.get()
            caseQS=Case.objects.queryset_byUID(self.request.session['caseUID'])
            caseRecord = caseQS.get()

            loanRecord.choiceFuture=False
            loanRecord.choiceCenterlink =False
            loanRecord.choiceVariable =False
            loanRecord.consentPrivacy =False
            loanRecord.consentElectronic =False
            loanRecord.choiceRetireAtHome = False
            loanRecord.choiceAvoidDownsizing = False
            loanRecord.choiceAccessFunds = False
            caseQS.meetingDate=None


            loanRecord.save(update_fields=['choiceFuture','choiceCenterlink','choiceVariable','consentPrivacy',
                                           'consentElectronic','choiceRetireAtHome','choiceAvoidDownsizing',
                                           'choiceAccessFunds'])

            caseRecord.save(update_fields=['meetingDate'])

        # perform high-level validation of client data
        clientDict = {}
        clientDict = self.get_queryset().values()[0]

        loanObj = LoanValidator([], clientDict)
        chkResponse = loanObj.chkClientDetails()

        if chkResponse['status'] == "Ok":
            # if ok, renders the success_url as normal
            return super(SetClientView, self).form_valid(form)
        else:
            # if error, renders the same page again with error message
            messages.error(self.request, chkResponse['details'])
            context = self.get_context_data(form=form)
            return self.render_to_response(context)


class SettingsView(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, UpdateView):
    template_name = "client_1_0/interface/settings.html"
    form_class = SettingsForm
    model = ModelSetting
    success_url = reverse_lazy('client:meetingStart')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(SettingsView, self).get_context_data(**kwargs)
        context['title'] = 'Model Settings'
        context['hideMenu'] = True

        return context

    def get_object(self, queryset=None):
        queryset = ModelSetting.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()
        return obj


# Introduction Views
class IntroductionView1(LoginRequiredMixin,SessionRequiredMixin, ContextHelper, TemplateView):

    template_name = "client_1_0/interface/introduction1.html"

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView1,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:meetingStart')
        context['nextUrl']=reverse_lazy('client:introduction2')

        return context

class IntroductionView2(LoginRequiredMixin, SessionRequiredMixin,ContextHelper,UpdateView):

    template_name = "client_1_0/interface/introduction2.html"
    form_class=IntroChkBoxForm
    model=Loan
    success_url = reverse_lazy('client:introduction3')

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView2,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction1')
        context['nextIsButton']=True

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj= queryset.get()
        return obj

class IntroductionView3(LoginRequiredMixin, SessionRequiredMixin, ContextHelper,TemplateView):

    template_name = "client_1_0/interface/introduction3.html"

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView3,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction2')
        context['nextUrl']=reverse_lazy('client:introduction4')

        return context

class IntroductionView4(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, TemplateView):

    template_name = "client_1_0/interface/introduction4.html"

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.validate_and_get_context()

        context = super(IntroductionView4,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction3')
        context['nextUrl']=reverse_lazy('client:topUp1')

        #Page uses post_id (slug) to expose images using same view
        context['post_id']=kwargs.get("post_id")
        context['imgPath'] = settings.STATIC_URL + 'img/'

        #use object to retrieve image
        queryset = Case.objects.queryset_byUID(self.request.session['caseUID'])
        obj = queryset.get()

        context['obj']=obj
        return context


# Top Up Views
class TopUp1(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, TemplateView):
        template_name = "client_1_0/interface/topUp1.html"

        def get_context_data(self, **kwargs):
            # Update and add dictionaries to context
            self.extra_context = self.validate_and_get_context()

            context = super(TopUp1, self).get_context_data(**kwargs)
            context['title'] = 'Top Up'
            context['previousUrl'] = reverse_lazy('client:introduction4')+"/4"
            context['nextUrl'] = reverse_lazy('client:topUp2')

            # Page uses post_id (slug) to expose images using same view
            context['post_id'] = kwargs.get("post_id")

            #Loan Projections
            loanProj = LoanProjection(context)

            projectionAge=loanProj.getProjectionAge()
            currentIncomeProj = loanProj.getInitialIncome()
            boostedIncomeProj = loanProj.getMaxEnhancedIncome()
            context['currentIncomeProj']=int(currentIncomeProj)
            context['boostedIncomeProj']=int(boostedIncomeProj)
            context['projectionAge']=projectionAge

            return context

class TopUp2(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, FormView):
    template_name = "client_1_0/interface/topUp2.html"
    form_class=topUpForm
    success_url = reverse_lazy('client:topUp3')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(TopUp2, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['previousUrl'] = reverse_lazy('client:topUp1') + "/1"
        context['nextIsButton']=True

        # Loan Projections
        loanProj = LoanProjection(self.extra_context)

        sliderData = loanProj.getEnhancedIncomeArray()
        currentIncomeProj = loanProj.getInitialIncome()
        boostedIncomeProj = loanProj.getMaxEnhancedIncome()

        context['currentIncomeProj'] = int(currentIncomeProj)
        context['boostedIncomeProj'] = int(boostedIncomeProj)
        context['sliderData']=json.dumps(sliderData)
        context['sliderPoints']=APP_SETTINGS['incomeIntervals']
        context['imgPath']=settings.STATIC_URL+'img/icons/equity_10_icon.png'

        return context

    def form_valid(self, form):

        #Save data manually
        loanDict=Loan.objects.dictionary_byUID(self.request.session['caseUID'])
        loanQS=Loan.objects.queryset_byUID(self.request.session['caseUID'])

        loanQS.update(topUpAmount=int(form.cleaned_data['topUpAmount']),
                      topUpIncome=int(form.cleaned_data['topUpIncome']),
                      incomeObjective=form.cleaned_data['topUpIncome']+loanDict['annualPensionIncome'])

        return super(TopUp2, self).form_valid(form)


class TopUp3(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, UpdateView):
    template_name = "client_1_0/interface/topUp3.html"
    form_class=debtRepayForm
    model=Loan
    success_url = reverse_lazy('client:live1')

    def get_context_data(self, **kwargs):

        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(TopUp3, self).get_context_data(**kwargs)
        context['title'] = 'Top Up'
        context['previousUrl'] = reverse_lazy('client:topUp2')
        context['nextIsButton']=True

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj= queryset.get()
        return obj

    def get_initial(self):
         # Pre-populate with existing debt
        initFormData= super(TopUp3, self).get_initial()
        clientDict = Case.objects.dictionary_byUID(self.request.session['caseUID'])
        if 'refinanceAmount' not in clientDict:
            initFormData["refinanceAmount"] = clientDict['mortgageDebt']
        return initFormData


# Live Views
class Live1(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, UpdateView):
    template_name = "client_1_0/interface/live1.html"
    form_class=renovateAmountForm
    model=Loan
    success_url = reverse_lazy('client:live2')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Live1, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['previousUrl'] = reverse_lazy('client:topUp3')
        context['nextIsButton']=True

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj= queryset.get()
        return obj


class Live2(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, UpdateView):
    template_name = "client_1_0/interface/live2.html"
    form_class=travelAmountForm
    model=Loan
    success_url = reverse_lazy('client:give')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Live2, self).get_context_data(**kwargs)
        context['title'] = 'Live'
        context['previousUrl'] = reverse_lazy('client:live1')
        context['nextIsButton']=True

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj= queryset.get()
        return obj

# Give Views
class Give(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, UpdateView):
    template_name = "client_1_0/interface/give.html"
    form_class=giveAmountForm
    model = Loan
    success_url = reverse_lazy('client:care')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Give, self).get_context_data(**kwargs)
        context['title'] = 'Give'
        context['previousUrl'] = reverse_lazy('client:live1')
        context['nextIsButton']=True

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj= queryset.get()
        return obj


# Care Views
class Care(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, UpdateView):
    template_name = "client_1_0/interface/care.html"
    form_class=careAmountForm
    model = Loan
    success_url = reverse_lazy('client:results1')

    def get_context_data(self, **kwargs):

        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Care, self).get_context_data(**kwargs)
        context['title'] = 'Care'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextIsButton']=True
        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj= queryset.get()
        return obj


# Results Views

class Results1(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, TemplateView):
    template_name = "client_1_0/interface/results1.html"

    def get(self, request, *args, **kwargs):
        aggDict = self.validate_and_get_context()

        #Check initial check boxes
        if  aggDict['choiceRetireAtHome']==False or aggDict['choiceAvoidDownsizing']==False or aggDict['choiceAccessFunds']==False:
            flagError=True
        else:
            flagError=False

        if aggDict['errors']==False and flagError==False:
            return HttpResponseRedirect(reverse_lazy('client:results2'))
        return super(Results1, self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Results1, self).get_context_data(**kwargs)
        context['title'] = 'Results'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextUrl']=reverse_lazy('client:results1')

        #Check initial check boxes
        if  context['choiceRetireAtHome']==False or context['choiceAvoidDownsizing']==False or context['choiceAccessFunds']==False:
            context['flagErrors']=True

        return context


class Results2(LoginRequiredMixin, SessionRequiredMixin,ContextHelper, UpdateView):
    template_name = "client_1_0/interface/results2.html"
    form_class=DetailedChkBoxForm
    model=Loan
    success_url = reverse_lazy('client:results3')

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Results2, self).get_context_data(**kwargs)
        context['title'] = 'Results'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextIsButton']=True

        return context

    def get_object(self, queryset=None):
        queryset = Loan.objects.queryset_byUID(self.request.session['caseUID'])
        obj= queryset.get()
        return obj

    def get_initial(self):
        # Uses the details saved in the client dictionary for the form
        self.initFormData= super(Results2, self).get_initial()
        loanDict=Loan.objects.dictionary_byUID(self.request.session['caseUID'])

        self.setInitialValues('choiceTopUp',[loanDict['topUpAmount']])
        self.setInitialValues('choiceRefinance',[loanDict['refinanceAmount']])
        self.setInitialValues('choiceGive',[loanDict['giveAmount']])
        self.setInitialValues('choiceReserve',[loanDict['protectedEquity']])
        self.setInitialValues('choiceLive', [loanDict['renovateAmount'],
                                             loanDict['travelAmount']])
        self.setInitialValues('choiceCare',[loanDict['careAmount']])

        return self.initFormData

    def setInitialValues(self,fieldName, dictName):

        initial=False
        for field in dictName:
            if field!=0:
               initial=True

        self.initFormData[fieldName]=initial


class Results3(ResultsHelper, LoginRequiredMixin, SessionRequiredMixin,ContextHelper, TemplateView):
    template_name = "client_1_0/interface/results3.html"

    def get_context_data(self, **kwargs):
        # Update and add to context
        self.extra_context = self.validate_and_get_context()

        context = super(Results3, self).get_context_data(**kwargs)

        context['title'] = 'Results'
        context['previousUrl'] = reverse_lazy('client:give')
        context['nextUrl'] = reverse_lazy('client:results4')
        context['nextIsButton'] = False


        # Loan Projections
        loanProj = LoanProjection(context)
        projectionFigures=loanProj.getProjections()

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

        return context


class Results4(ResultsHelper, LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_1_0/interface/results4.html"

    def get_context_data(self, **kwargs):

        context = super(Results4, self).get_context_data(**kwargs)

        context['title'] = 'Thank you'
        context['previousUrl'] = reverse_lazy('client:results1')
        context['nextUrl'] = reverse_lazy('client:final')
        context['nextIsButton'] = False

        return context

# Final Views

class FinalView(ResultsHelper, LoginRequiredMixin, SessionRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_1_0/interface/final.html"

    def get_context_data(self, **kwargs):

        context = super(ResultsHelper, self).get_context_data(**kwargs)

        context['pdfURL'] = self.request.build_absolute_uri(reverse('client:finalPdf'))

        return context


class FinalErrorView(ResultsHelper, LoginRequiredMixin, ContextHelper, TemplateView):
    template_name = "client_1_0/interface/final_error.html"


class FinalPDFView(LoginRequiredMixin, SessionRequiredMixin, View):
    #This view is called via javascript from the final page to generate the report pdf
    #It uses a utility to render the report and then save and serves the pdf

    def get(self,request):

        sourceUrl = 'https://householdcapital.app/client/pdfLoanSummary/' + self.request.session['caseUID']
        targetFileName = settings.MEDIA_ROOT + "/customerReports/Summary-" + self.request.session['caseUID'][
                                                                             -12:] + ".pdf"

        pdf=pdfGenerator(self.request.session['caseUID'])
        created,text = pdf.createPdfFromUrl(sourceUrl,'HouseholdSummary.pdf',targetFileName)

        if not created:
            return HttpResponseRedirect(reverse_lazy('client:finalError'))

        try:
            # SAVE TO DATABASE
            localfile = open(targetFileName, 'rb')

            qsCase = Case.objects.queryset_byUID(self.request.session['caseUID'])
            qsCase.update(summaryDocument=File(localfile), )

            pdf_contents = localfile.read()
        except:
            write_applog("ERROR", 'PdfProduction', 'get',
                         "Failed to save Summary Report in Database: " + self.request.session['caseUID'])

        ## RENDER FILE TO HTTP RESPONSE
        response = HttpResponse(pdf.getContent(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="HHC-LoanSummary.pdf"'
        localfile.close()

        # log user out
        write_applog("INFO", 'PdfProduction', 'get',
                     "Meeting ended for:" + self.request.session['caseUID'])
        logout(self.request)
        return response


# REPORT VIEWS

class PdfLoanSummary(ResultsHelper, TemplateView):
    #This page is not designed to be viewed - it is to be called by the pdf generator
    #It requires a UID to be passed to it

    template_name = "client_1_0/documents/loanSummary.html"

    def get_context_data(self, **kwargs):

        context = super(PdfLoanSummary, self).get_context_data(**kwargs)

        if 'uid' in kwargs:

            caseUID=str(kwargs['uid'])

            # get dictionaries from model
            clientDict = Case.objects.dictionary_byUID(caseUID)
            loanDict = Loan.objects.dictionary_byUID(caseUID)
            modelDict = ModelSetting.objects.dictionary_byUID(caseUID)

            # validate loan
            loanObj = LoanValidator(clientDict, loanDict)
            loanStatus = loanObj.getStatus()

            # create context
            context.update(clientDict)
            context.update(loanDict)
            context.update(modelDict)
            context.update(loanStatus)
            context['caseTypesEnum'] = caseTypesEnum
            context['clientSexEnum'] = clientSexEnum
            context['clientTypesEnum'] = clientTypesEnum
            context['dwellingTypesEnum'] = dwellingTypesEnum
            context['pensionTypesEnum'] = pensionTypesEnum
            context['loanTypesEnum'] = loanTypesEnum

            # Loan Projections
            loanProj = LoanProjection(context)
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

            context['comparisonRate']=context['totalInterestRate']+context['comparisonRateIncrement']
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

            # use object to retrieve image
            queryset = Case.objects.queryset_byUID(caseUID)
            obj = queryset.get()

            context['obj'] = obj
            context['caseUID'] = caseUID

        return context


class PdfRespLending(TemplateView):
    #This page is not designed to be viewed - it is to be called by the pdf generator
    #It requires a UID to be passed to it

    template_name = "client_1_0/documents/respLending.html"

    def get_context_data(self, **kwargs):

        context = super(PdfRespLending, self).get_context_data(**kwargs)

        if 'uid' in kwargs:

            caseUID=str(kwargs['uid'])

            # get dictionaries from model
            clientDict = Case.objects.dictionary_byUID(caseUID)
            loanDict = Loan.objects.dictionary_byUID(caseUID)

            context.update(clientDict)
            context.update(loanDict)
            context['caseUID'] = caseUID

        return context


class PdfPrivacy(TemplateView):
    #This page is not designed to be viewed - it is to be called by the pdf generator
    #It requires a UID to be passed to it

    template_name = "client_1_0/documents/privacy.html"

    def get_context_data(self, **kwargs):

        context = super(PdfPrivacy, self).get_context_data(**kwargs)

        if 'uid' in kwargs:

            caseUID=str(kwargs['uid'])

            # get dictionaries from model
            clientDict = Case.objects.dictionary_byUID(caseUID)
            loanDict = Loan.objects.dictionary_byUID(caseUID)

            context.update(clientDict)
            context.update(loanDict)
            context['caseUID'] = caseUID

        return context


class PdfElectronic(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_1_0/documents/electronic.html"

    def get_context_data(self, **kwargs):
        context = super(PdfElectronic, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            clientDict = Case.objects.dictionary_byUID(caseUID)
            loanDict = Loan.objects.dictionary_byUID(caseUID)

            context.update(clientDict)
            context.update(loanDict)
            context['caseUID'] = caseUID

        return context

class PdfClientData(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_1_0/documents/clientData.html"

    def get_context_data(self, **kwargs):
        context = super(PdfClientData, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            qsClient = Case.objects.queryset_byUID(caseUID)
            qsLoan = Loan.objects.queryset_byUID(caseUID)

            context['client']=qsClient.get()
            context['loan']=qsLoan.get()
            context['loanTypesEnum'] = loanTypesEnum
            context['caseUID']=caseUID

        return context


class PdfInstruction(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_1_0/documents/clientInstruction.html"

    def get_context_data(self, **kwargs):
        context = super(PdfInstruction, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            qsClient = Case.objects.queryset_byUID(caseUID)
            qsLoan = Loan.objects.queryset_byUID(caseUID)

            context['client'] = qsClient.get()
            context['loan'] = qsLoan.get()
            context['loanTypesEnum'] = loanTypesEnum
            context['caseUID'] = caseUID

        return context

class PdfValInstruction(TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "client_1_0/documents/clientValInstruction.html"

    def get_context_data(self, **kwargs):
        context = super(PdfValInstruction, self).get_context_data(**kwargs)

        if 'uid' in kwargs:
            caseUID = str(kwargs['uid'])

            # get dictionaries from model
            qsClient = Case.objects.queryset_byUID(caseUID)
            qsLoan = Loan.objects.queryset_byUID(caseUID)

            context['client'] = qsClient.get()
            context['loan'] = qsLoan.get()
            context['loanTypesEnum'] = loanTypesEnum
            context['caseUID'] = caseUID

        return context