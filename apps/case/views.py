#Python Imports
import datetime

#Django Imports
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.generic import ListView, UpdateView, CreateView

#Third-party Imports

#Local Application Imports
from .models import Case
from .forms import CaseDetailsForm
from apps.lib.loanValidator import LoanValidator

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
        context['hideMenu']=True
        context['isUpdate']=True

        clientDict={}
        clientDict=self.get_queryset().values()[0]

        loanObj = LoanValidator([],clientDict)
        context['status']=loanObj.chkClientDetails()

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Update age if birthdate present
        if obj.birthdate_1 != None:
            obj.age_1 = datetime.date.today().year-obj.birthdate_1.year

        if obj.birthdate_2 != None:
            obj.age_2 = datetime.date.today().year - obj.birthdate_2.year

        obj.user=self.request.user

        obj.save()
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
        return super(CaseCreateView,self).form_valid(form)
