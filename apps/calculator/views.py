import json
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import ListView, UpdateView, CreateView, TemplateView
from django.urls import reverse_lazy, reverse


from apps.lib.loanValidator import LoanValidator
from apps.lib.enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,pensionTypesEnum, loanTypesEnum

from .models import WebCalculator
from .forms import WebInputForm, WebOutputForm


# VIEWS
class InputView(CreateView):

    template_name ='calculator/input.html'
    model=WebCalculator
    form_class = WebInputForm

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

            success = reverse_lazy('calculator:calcOutput', kwargs={'uid': str(obj.calcUID)})
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


class OutputView(UpdateView):
    template_name = 'calculator/output.html'
    model=WebCalculator
    caseUID=""
    form_class = WebOutputForm

    def get(self, request, **kwargs):
        if 'uid' in kwargs:
            self.caseUID=str(kwargs['uid'])
            return super(OutputView,self).get(self, request, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy("calulator:input"))

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
        obj = form.save(commit=False)
        obj.save(update_fields=['email', 'isRefi','isTopUp', 'isLive', 'isGive','isCare'])
        messages.success(self.request,"Thank you - we will email you shortly")
        context=self.get_context_data(form=form)
        context['success']=True
        return self.render_to_response(context)
