#Python Imports
import datetime
import os
import uuid

#Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, DeleteView, View

#Third-party Imports

#Local Application Imports
from .models import Case
from .forms import CaseDetailsForm
from apps.lib.loanValidator import LoanValidator
from apps.lib.enums import caseTypesEnum, clientSexEnum, clientTypesEnum, dwellingTypesEnum ,pensionTypesEnum, loanTypesEnum


# MIXINS

class LoginRequiredMixin(object):
    #Ensures views will not render undless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

# CLASS BASED VIEWS

# Client List View
class CaseListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    template_name = 'case/caseList.html'
    context_object_name = 'object_list'
    model=Case

    def get_queryset(self,**kwargs):
        queryset= super(CaseListView, self).get_queryset()

        # Search modifications
        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(caseDescription__icontains=search) |
                Q(adviser__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(caseNotes__icontains=search)|
                Q(street__icontains=search)|
                Q(surname_1__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(CaseListView,self).get_context_data(**kwargs)
        context['title'] = 'Cases'
        context['hideMenu']=True

        return context

class CaseDetailView(LoginRequiredMixin, UpdateView):

    template_name ='case/caseDetail.html'
    model=Case
    form_class=CaseDetailsForm
    context_object_name = 'obj'

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView,self).get_context_data(**kwargs)
        context['title'] = 'Case Detail'
        context['isUpdate']=True
        context['caseTypesEnum']=caseTypesEnum

        clientDict={}
        clientDict=self.get_queryset().filter(caseID=self.object.caseID).values()[0]


        loanObj = LoanValidator([],clientDict)
        context['status']=loanObj.chkClientDetails()

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Update age if birthdate present and user
        if obj.birthdate_1 != None:
            obj.age_1 = datetime.date.today().year-obj.birthdate_1.year
        if obj.birthdate_2 != None:
            obj.age_2 = datetime.date.today().year - obj.birthdate_2.year
        obj.save()

        import pathlib

        if obj.propertyImage:
            path,filename=obj.propertyImage.name.split("/")
            ext=pathlib.Path(obj.propertyImage.name).suffix



            newFilename=settings.MEDIA_ROOT+"/"+path+"/"+str(obj.caseUID)+"."+ext
            os.rename(settings.MEDIA_ROOT+"/"+obj.propertyImage.name,
                      newFilename)
            obj.propertyImage = path+"/"+str(obj.caseUID)+"."+ext
            obj.save(update_fields=['propertyImage'])

        return super(CaseDetailView, self).form_valid(form)

class CaseCreateView(LoginRequiredMixin, CreateView):

    template_name ='case/caseDetail.html'
    model=Case
    form_class=CaseDetailsForm

    def get_context_data(self, **kwargs):
        context = super(CaseCreateView,self).get_context_data(**kwargs)
        context['title'] = 'New Case'
        context['hideMenu']=True

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        #Update age if birthdate present
        if obj.birthdate_1 != None:
            obj.age_1 = datetime.date.today().year-obj.birthdate_1.year

        if obj.birthdate_2 != None:
            obj.age_2 = datetime.date.today().year - obj.birthdate_2.year

        #Set fields manually
        obj.caseType = 0
        obj.user=self.request.user

        obj.save()
        messages.success(self.request,"Lead Created")
        return super(CaseCreateView,self).form_valid(form)


class CaseDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        if "uid" in kwargs:
            Case.objects.filter(caseUID=kwargs['uid']).delete()
            messages.success(self.request, "Lead deleted")

        return HttpResponseRedirect(reverse_lazy('case:caseList'))