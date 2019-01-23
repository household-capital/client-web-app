import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template,render_to_string
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View

from weasyprint import HTML, CSS

from .forms import ClientDetailsForm, SettingsForm,IntroChkBoxForm,topUpForm
from .utilities.globals import DEFAULT_CLIENT, ECONOMIC, LOAN, APP_SETTINGS
from .utilities.loanValidator import LoanValidator
from .utilities.loanProjection import LoanProjection


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

# VIEWS

# Landing View
class LandingView(LoginRequiredMixin, TemplateView):

    template_name = "client/landing.html"

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

    template_name = "client/introduction1.html"

    def get_context_data(self, **kwargs):
        context = super(IntroductionView1,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:landing')
        context['nextUrl']=reverse_lazy('client:introduction2')
        return context

class IntroductionView2(LoginRequiredMixin, ClientDataMixin, FormView):

    template_name = "client/introduction2.html"
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
            clientDict=self.request.session['clientDict']
            clientDict['clientChoices']=form.cleaned_data['clientChoices']
            self.request.session['clientDict']=clientDict

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

    template_name = "client/introduction3.html"

    def get_context_data(self, **kwargs):
        context = super(IntroductionView3,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction2')
        context['nextUrl']=reverse_lazy('client:introduction4')+"/1"

        # Loan Validation
        loanObj = LoanValidator(self.request.session['clientDict'], self.request.session['loanDict'])
        loanStatus=loanObj.getStatus()
        context.update(loanStatus)

        return context

class IntroductionView4(LoginRequiredMixin, ClientDataMixin, TemplateView):

    template_name = "client/introduction4.html"

    def get_context_data(self, **kwargs):
        context = super(IntroductionView4,self).get_context_data(**kwargs)
        context['title'] = 'Introduction'
        context['previousUrl']=reverse_lazy('client:introduction3')
        context['nextUrl']=reverse_lazy('client:topUp1')
        context['clientPensionAnnual']=context['clientPension']*26

        #Page uses post_id (slug) to expose images using same view
        context['post_id']=kwargs.get("post_id")

        return context

# Top Up Views
class TopUp1(LoginRequiredMixin, ClientDataMixin, TemplateView):
        template_name = "client/topUp1.html"

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

            loanProj = LoanProjection(self.request.session['clientDict'],
                                      self.request.session['loanDict'],
                                      self.request.session['economicDict'],
                                      loanStatusDict)

            currentIncomeProj = loanProj.getInitialIncome()
            boostedIncomeProj = loanProj.getMaxEnhancedIncome()
            context['currentIncomeProj']=int(currentIncomeProj)
            context['boostedIncomeProj']=int(boostedIncomeProj)

            return context


class TopUp2(LoginRequiredMixin, ClientDataMixin, FormView):
    template_name = "client/topUp2.html"
    form_class=topUpForm
    success_url = reverse_lazy('client:introduction4')

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
        print(self.request.session.items())

        return context

    def form_valid(self, form):
        # All three check boxes to be checked

        loanDict = self.request.session['loanDict']
        loanDict['topUpAmount'] = form.cleaned_data['topUpAmount']
        self.request.session['loanDict'] = loanDict
        print(self.request.session.items())


        return super(TopUp2, self).form_valid(form)




# Set Client View
class SetClientView(LoginRequiredMixin, FormView):

    #Sets the initial client data (in associated dictionary)

    template_name = "client/setttings.html"
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



# Settings View
class SettingsView(LoginRequiredMixin, FormView):

    template_name = "client/setttings.html"
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

class pdfView(View):

    def get(self, request, *args, **kwargs):
        html_template = get_template('../templates/client/pdfResults.html')
        pdf_file = HTML(string=html_template.render(), base_url=request.build_absolute_uri()).write_pdf (
                        stylesheets=[CSS(settings.STATIC_ROOT +  '/css/client.css')])
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="report.pdf"'
        return response
