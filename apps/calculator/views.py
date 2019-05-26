# Python Imports

#Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView, CreateView,ListView, TemplateView, View
from django.urls import reverse_lazy


#Third-party Imports

#Local Application Imports
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.site_Enums import caseTypesEnum, loanTypesEnum, dwellingTypesEnum, directTypesEnum
from apps.lib.site_Utilities import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.enquiry.models import Enquiry

from .models import WebCalculator, WebContact
from .forms import WebInputForm, WebOutputForm, WebContactForm, WebContactDetail


# VIEWS
@method_decorator(csrf_exempt, name='dispatch')
class InputView(CreateView):

    template_name ='calculator/input.html'
    model=WebCalculator
    form_class = WebInputForm

    @xframe_options_exempt
    def get(self,request,*args,**kwargs):
        clientId=str(request.GET.get('clientId'))


        return super(InputView,self).get(self,request,*args,**kwargs)

    @xframe_options_exempt
    def post(self,request,*args,**kwargs):
            return super(InputView, self).post(self,request,*args,**kwargs)

    def get_context_data(self, **kwargs):
        context= super(InputView, self).get_context_data(**kwargs)
        context['loanTypesEnum']=loanTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum

        return context

    def get_object(self, queryset=None):
        uid=self.kwargs['uid']
        queryset = WebCalculator.objects.queryset_byUID(str(uid))
        obj= queryset.get()
        return obj

    def form_invalid(self, form):

        messages.error(self.request, "Input error - please check input fields")
        print(form.errors)
        return super(InputView,self).form_invalid(form)


    def form_valid(self, form):
        clientDict=form.cleaned_data
        obj = form.save(commit=False)

        loanObj = LoanValidator(clientDict)
        chkOpp = loanObj.validateLoan()

        obj.valuation=int(form.cleaned_data['valuation'])

        if chkOpp['status'] == "Error":
            obj.status=0
            obj.errorText=chkOpp['details']
            obj.save()

            messages.error(self.request, self.clientText(chkOpp['details']))

            return self.render_to_response(self.get_context_data(form=form))

        else:
            obj.status = 1
            obj.maxLoanAmount=chkOpp['restrictions']['maxLoan']
            obj.maxLVR = chkOpp['restrictions']['maxLVR']
            obj.save()

            clientId=str(self.request.GET.get('clientId'))

            success = reverse_lazy('calculator:calcOutput', kwargs={'uid': str(obj.calcUID)})+"?clientId="+clientId
            return HttpResponseRedirect(success)

    def clientText(self, inputString):

        responseText={
            'Invalid Postcode': 'Unfortunately, we do not operate in this postcode',
            'Youngest borrower must be 60' : 'This product is designed for borrowers older than 60',
            'Youngest joint borrower must be 65' : 'For couples, the youngest borrower must be at least 65',
            'Minimum Loan Size cannot be met' : 'Unfortunately, our minimum loan size would not be met',
            }

        if inputString in responseText:
            return responseText[inputString]
        else:
            return "Calculation cannot be performed at this time."

@method_decorator(csrf_exempt, name='dispatch')
class OutputView(UpdateView):
    template_name = 'calculator/output.html'
    model=WebCalculator
    caseUID=""
    form_class = WebOutputForm

    @xframe_options_exempt
    def get(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID=str(kwargs['uid'])
            return super(OutputView,self).get(self, request, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy("calculator:input"))

    @xframe_options_exempt
    def post(self,request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID=str(kwargs['uid'])
        return super(OutputView, self).post(self, request, **kwargs)

    def get_object(self, queryset=None):
        queryset = WebCalculator.objects.queryset_byUID(self.caseUID)
        obj= queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context=super(OutputView,self).get_context_data(**kwargs)

        obj=self.get_object()

        context["obj"]=obj
        if obj.maxLVR <18:
            img='transfer_15.png'
        elif obj.maxLVR <22:
            img = 'transfer_20.png'
        elif obj.maxLVR < 27:
            img = 'transfer_25.png'
        elif obj.maxLVR < 32:
            img = 'transfer_30.png'
        else:
            img = 'transfer_35.png'
        context["transfer_img"]=img

        if obj.referrer:
            if 'https://householdcapital.com.au/refinance-existing-mortgage' in obj.referrer:
                context['isRefi']=True
            if 'https://householdcapital.com.au/aged-care-financing/' in obj.referrer:
                context['isCare'] = True
            if 'https://householdcapital.com.au/superannuation-and-retirement/'  in obj.referrer:
                context['isTopUp']=True

        return context

    def form_valid(self, form):
        obj = form.save(commit=True)
        obj.save(update_fields=['email', 'isRefi','isTopUp', 'isLive', 'isGive','isCare'])
        context=self.get_context_data(form=form)
        context['success']=True

        obj=self.get_object()

        campaignURLs=['https://householdcapital.com.au/equity-mortgage-release/',
                      'https://householdcapital.com.au/centrelink-pension-information/',
                      'https://householdcapital.com.au/aged-care-financing/',
                      'https://householdcapital.com.au/reverse-mortgages/',
                      'https://householdcapital.com.au/superannuation-and-retirement/',
                      'https://householdcapital.com.au/retirement-planning/',
                      'https://householdcapital.com.au/refinance-existing-mortgage/']

        context['redirect'] = False

        if obj.referrer:
            for url in campaignURLs:
                if url in obj.referrer:
                    context['redirect'] = True
                    context['redirectURL'] = obj.referrer.replace(url, url[:-1] + "-thank-you")

        if context['redirect'] == False:
            messages.success(self.request, "Thank you - we will email you shortly")

        return self.render_to_response(context)



@method_decorator(csrf_exempt, name='dispatch')
class ContactView(CreateView):

    template_name ='calculator/contact.html'
    model=WebContact
    form_class = WebContactForm

    @xframe_options_exempt
    def get(self,request,*args,**kwargs):
        return super(ContactView,self).get(self,request,*args,**kwargs)

    @xframe_options_exempt
    def post(self,request,*args,**kwargs):
            return super(ContactView, self).post(self,request,*args,**kwargs)


    def form_valid(self, form):
        clientDict=form.cleaned_data
        obj = form.save(commit=True)

        context={}
        context['submitted']=True

        return self.render_to_response(context)




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


# Calculator Queue
class CalcListView(LoginRequiredMixin, ListView):
    paginate_by = 6
    template_name = 'calculator/calculatorList.html'
    context_object_name = 'object_list'
    model = WebCalculator

    def get_queryset(self, **kwargs):
        queryset = super(CalcListView, self).get_queryset()

        queryset = queryset.filter(email__isnull=False, actioned=0).order_by('-timestamp')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(CalcListView, self).get_context_data(**kwargs)
        context['title'] = 'Web Calculator Queue'


        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context


class CalcMarkSpam(LoginRequiredMixin, UpdateView):
    # This view does not render it updates the calculator and redirects to the ListView
    context_object_name = 'object_list'
    model = WebCalculator

    def get(self, request, *args, **kwargs):
        calcUID = str(kwargs['uid'])
        queryset = WebCalculator.objects.queryset_byUID(str(calcUID))
        obj = queryset.get()
        obj.actioned = -1
        obj.save(update_fields=['actioned'])
        return HttpResponseRedirect(reverse_lazy("calculator:calcList"))


class CalcSendDetails(LoginRequiredMixin, UpdateView):
    # This view does not render it creates and enquiry, sends an email, updates the calculator
    # and redirects to the Enquiry ListView
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'calculator/email/email_cover_calculator.html'
    template_name_alt='calculator/email/email_cover_calculator_calendar.html'

    def get(self, request, *args, **kwargs):
        calcUID = str(kwargs['uid'])
        queryset = WebCalculator.objects.queryset_byUID(str(calcUID))
        obj = queryset.get()

        calcDict = WebCalculator.objects.dictionary_byUID(str(calcUID))

        # Create enquiry using WebCalculator Data
        # Remove certain items from the dictionary
        referrer = calcDict['referrer']
        calcDict.pop('calcUID')
        calcDict.pop('actionedBy')
        calcDict.pop('id')
        calcDict.pop('referrer')
        calcDict.pop('updated')
        calcDict.pop('timestamp')
        calcDict.pop('actioned')
        user = self.request.user

        enq_obj = Enquiry.objects.create(user=user, referrer=directTypesEnum.WEB_CALCULATOR.value, referrerID=referrer,
                                         **calcDict)
        enq_obj.save()

        # PRODUCE PDF REPORT
        sourceUrl = 'https://householdcapital.app/calculator/calcSummaryPdf/' + str(enq_obj.enqUID)
        targetFileName = settings.MEDIA_ROOT + "/enquiryReports/Enquiry-" + str(enq_obj.enqUID)[
                                                                            -12:] + ".pdf"

        pdf = pdfGenerator(calcUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'CalculatorSummary.pdf', targetFileName)

        if not created:
            messages.error(self.request, "Enquiry created - but email not sent")

            obj.actioned = 1  # Actioned=1, Spam=-1
            obj.save(update_fields=['actioned'])

            return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))

        try:
            # SAVE TO DATABASE (Enquiry Model)
            localfile = open(targetFileName, 'rb')

            qsCase = Enquiry.objects.queryset_byUID(str(enq_obj.enqUID))
            qsCase.update(summaryDocument=File(localfile), )

            pdf_contents = localfile.read()
        except:
            write_applog("ERROR", 'CalcSendDetails', 'get',
                         "Failed to save Calc Summary in Database: " + str(enq_obj.enqUID))

        email_context = {}
        email_context['user'] = request.user
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

        subject, from_email, to, bcc = "Household Loan Enquiry", \
                                       self.request.user.email, \
                                       obj.email, \
                                       self.request.user.email
        text_content = "Text Message"
        attachFilename = 'HHC-CalculatorSummary'

        if request.user.username in ['Moutzikis']:
            sent = pdf.emailPdf(self.template_name_alt, email_context, subject, from_email, to, bcc, text_content,
                                attachFilename)
        else:
            sent = pdf.emailPdf(self.template_name, email_context, subject, from_email, to, bcc, text_content,
                            attachFilename)

        if sent:
            messages.success(self.request, "Client has been emailed and enquiry created")
        else:
            messages.error(self.request, "Enquiry created - but email not sent")

        obj.actioned = 1  # Actioned=1, Spam=-1
        obj.save(update_fields=['actioned'])

        return HttpResponseRedirect(reverse_lazy("enquiry:enquiryList"))


class CalcSummaryPdfView(TemplateView):
    # Produce Summary Report View (called by Api2Pdf)
    template_name = 'calculator/document/calculator_summary.html'

    def get_context_data(self, **kwargs):
        context = super(CalcSummaryPdfView, self).get_context_data(**kwargs)

        enqUID = str(kwargs['uid'])

        obj = Enquiry.objects.dictionary_byUID(enqUID)

        context["obj"] = obj
        if obj["maxLVR"] < 18:
            img = 'transfer_15.png'
        elif obj["maxLVR"] < 22:
            img = 'transfer_20.png'
        elif obj["maxLVR"] < 27:
            img = 'transfer_25.png'
        elif obj["maxLVR"] < 32:
            img = 'transfer_30.png'
        else:
            img = 'transfer_35.png'
        context["transfer_img"] = img

        context['caseTypesEnum'] = caseTypesEnum
        context['loanTypesEnum'] = loanTypesEnum
        context['dwellingTypesEnum'] = dwellingTypesEnum
        context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        return context

# Contact Queue
class ContactListView(LoginRequiredMixin, ListView):
    paginate_by = 6
    template_name = 'calculator/contactList.html'
    context_object_name = 'object_list'
    model = WebContact

    def get_queryset(self, **kwargs):
        queryset = super(ContactListView, self).get_queryset()

        queryset = queryset.order_by('-timestamp')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContactListView, self).get_context_data(**kwargs)
        context['title'] = 'Web Contact Queue'

        self.request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
        self.request.session['webContQueue'] = WebContact.objects.queueCount()
        self.request.session['enquiryQueue'] = Enquiry.objects.queueCount()

        return context

# Contact Detail View
class ContactDetailView(LoginRequiredMixin, UpdateView):
    template_name = "calculator/contactDetail.html"
    form_class = WebContactDetail
    model = WebContact

    def get_object(self, queryset=None):
        if "uid" in self.kwargs:
            queryset = WebContact.objects.queryset_byUID(str(self.kwargs['uid']))
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(ContactDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Web Contact Detail'
        context['obj'] = self.get_object()
        return context

    def form_valid(self, form):

        obj = form.save(commit=False)

        obj.save()

        messages.success(self.request, "Contact Updated")

        return HttpResponseRedirect(reverse_lazy('calculator:contactDetail', kwargs={'uid': str(obj.contUID)}))


class ContactActionView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            queryset = WebContact.objects.queryset_byUID(str(kwargs['uid']))
            obj = queryset.get()
            obj.actioned=1
            obj.actionedBy=request.user
            obj.actionDate=timezone.now()
            obj.save(update_fields=['actioned','actionedBy','actionDate'])
            messages.success(self.request, "Contact marked as actioned")

        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))

# Enquiry Delete View (Delete View)
class ContactDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            WebContact.objects.filter(contUID=kwargs['uid']).delete()
            messages.success(self.request, "Contact deleted")

        return HttpResponseRedirect(reverse_lazy('calculator:contactList'))