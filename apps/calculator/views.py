#Python Imports

#Django Imports
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView, CreateView

#Third-party Imports

#Local Application Imports
from apps.lib.loanValidator import LoanValidator
from apps.lib.enums import  dwellingTypesEnum, loanTypesEnum
from apps.logging import write_applog
from .models import WebCalculator, WebContact
from .forms import WebInputForm, WebOutputForm, WebContactForm



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

        loanObj = LoanValidator({}, clientDict)
        chkOpp = loanObj.chkClientDetails()

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

        obj=WebCalculator.objects.dictionary_byUID(self.caseUID)

        context["obj"]=obj
        if obj["maxLVR"]<18:
            img='transfer_15.png'
        elif obj["maxLVR"]<22:
            img = 'transfer_20.png'
        elif obj["maxLVR"] < 27:
            img = 'transfer_25.png'
        elif obj["maxLVR"] < 32:
            img = 'transfer_30.png'
        else:
            img = 'transfer_35.png'
        context["transfer_img"]=img

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
                      'https://householdcapital.com.au/retirement-planning/']

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






