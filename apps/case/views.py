# Python Imports
import datetime
import os
import pathlib

# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, View


# Third-party Imports

# Local Application Imports
from apps.calculator.models import WebCalculator
from apps.lib.loanValidator import LoanValidator
from apps.lib.enums import caseTypesEnum
from apps.lib.utilities import pdfGenerator
from .forms import CaseDetailsForm, LossDetailsForm
from .models import Case, LossData



# //MIXINS

class LoginRequiredMixin(object):
    # Ensures views will not render undless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)


# //CLASS BASED VIEWS

# Case List View
class CaseListView(LoginRequiredMixin, ListView):
    paginate_by = 6
    template_name = 'case/caseList.html'
    context_object_name = 'object_list'
    model = Case

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search paramater
        queryset = super(CaseListView, self).get_queryset()

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(caseDescription__icontains=search) |
                Q(adviser__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(caseNotes__icontains=search) |
                Q(street__icontains=search) |
                Q(surname_1__icontains=search)
            )

        # ...and for open or closed cases
        if self.request.GET.get('showClosed') == "True":
            queryset = queryset.filter(caseType=caseTypesEnum.CLOSED.value)
        else:
            queryset = queryset.exclude(caseType=caseTypesEnum.CLOSED.value)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(CaseListView, self).get_context_data(**kwargs)
        context['title'] = 'Cases'

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        if self.request.GET.get('showClosed'):
            context['showClosed'] = self.request.GET.get('showClosed')
        else:
            context['showClosed'] = False
        return context


# Case Detail View (UpdateView)
class CaseDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'case/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm
    context_object_name = 'obj'

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Case Detail'
        context['isUpdate'] = True
        context['caseTypesEnum'] = caseTypesEnum

        clientDict = {}
        clientDict = self.get_queryset().filter(caseID=self.object.caseID).values()[0]

        loanObj = LoanValidator([], clientDict)
        context['status'] = loanObj.chkClientDetails()

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Update age if birthdate present and user
        if obj.birthdate_1 != None:
            obj.age_1 = int((datetime.date.today() - obj.birthdate_1).days / 365.25)
        if obj.birthdate_2 != None:
            obj.age_2 = int((datetime.date.today() - obj.birthdate_2).days / 365.25)
        obj.save()

        # Renames and moves the image file if present
        if obj.propertyImage:
            path, filename = obj.propertyImage.name.split("/")
            ext = pathlib.Path(obj.propertyImage.name).suffix

            newFilename = settings.MEDIA_ROOT + "/" + path + "/" + str(obj.caseUID) + "." + ext
            os.rename(settings.MEDIA_ROOT + "/" + obj.propertyImage.name,
                      newFilename)
            obj.propertyImage = path + "/" + str(obj.caseUID) + "." + ext
            obj.save(update_fields=['propertyImage'])

        # Checks for a closed case and redirects to Case Close View
        if obj.caseType == caseTypesEnum.CLOSED.value:
            return HttpResponseRedirect(reverse_lazy('case:caseClose', kwargs={'uid': str(obj.caseUID)}))

        # Generates documents when "Meeting Held" set or updated (move to another trigger?)
        if obj.caseType == caseTypesEnum.MEETING_HELD.value:

            docList = (('pdfPrivacy/', "Privacy-"),
                       ('pdfElectronic/', "Electronic-"),
                       ('pdfRespLending/', "Responsible-"),
                       ('pdfClientData/', "ClientData-"))

            sourcePath = 'https://householdcapital.app/client/'
            targetPath = settings.MEDIA_ROOT + "/customerReports/"
            clientUID = obj.caseUID

            for doc in docList:
                pdf = pdfGenerator(str(clientUID))
                pdf.createPdfFromUrl(sourcePath + doc[0] + str(clientUID), "",
                                     targetPath + doc[1] + str(clientUID)[-12:] + ".pdf")

            obj.privacyDocument = targetPath + docList[0][1] + str(clientUID)[-12:] + ".pdf"
            obj.electronicDocument = targetPath + docList[1][1] + str(clientUID)[-12:] + ".pdf"
            obj.responsibleDocument = targetPath + docList[2][1] + str(clientUID)[-12:] + ".pdf"
            obj.dataDocument = targetPath + docList[3][1] + str(clientUID)[-12:] + ".pdf"

            obj.save(update_fields=['privacyDocument', 'electronicDocument', 'responsibleDocument', 'dataDocument'])

        return super(CaseDetailView, self).form_valid(form)


# Case Create View (Create View)
class CaseCreateView(LoginRequiredMixin, CreateView):
    template_name = 'case/caseDetail.html'
    model = Case
    form_class = CaseDetailsForm

    def get_context_data(self, **kwargs):
        context = super(CaseCreateView, self).get_context_data(**kwargs)
        context['title'] = 'New Case'

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Update age if birthdate present
        if obj.birthdate_1 != None:
            obj.age_1 = datetime.date.today().year - obj.birthdate_1.year

        if obj.birthdate_2 != None:
            obj.age_2 = datetime.date.today().year - obj.birthdate_2.year

        # Set fields manually
        obj.caseType = caseTypesEnum.LEAD.value
        obj.user = self.request.user

        obj.save()
        messages.success(self.request, "Lead Created")
        return super(CaseCreateView, self).form_valid(form)


# Case Delete View (Delete View)
class CaseDeleteView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            Case.objects.filter(caseUID=kwargs['uid']).delete()
            messages.success(self.request, "Lead deleted")

        return HttpResponseRedirect(reverse_lazy('case:caseList'))


# Case Close View (Update View)
class CaseCloseView(LoginRequiredMixin, UpdateView):
    model = LossData
    template_name = 'case/caseLoss.html'
    form_class = LossDetailsForm
    context_object_name = 'obj'
    success_url = reverse_lazy('case:caseList')

    def get(self, request, *args, **kwargs):
        if "uid" in kwargs:
            caseUID = str(kwargs['uid'])
            request.session['caseUID'] = caseUID
        return super(CaseCloseView, self).get(self, request, *args, **kwargs)

    def get_object(self, queryset=None):
        queryset = LossData.objects.queryset_byUID(str(self.request.session['caseUID']))
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super(CaseCloseView, self).get_context_data(**kwargs)
        context['title'] = 'Close Case'
        return context

    def get_initial(self):
        initial = super(CaseCloseView, self).get_initial()
        initial['lossDate'] = datetime.datetime.today().strftime("%d/%m/%Y")
        return initial


# Case Summary View (List View) - work in progress
class CaseSummaryView(LoginRequiredMixin, ListView):
    template_name = 'case/caseSummary.html'
    context_object_name = 'object_list'
    model = Case

    def get_queryset(self, **kwargs):
        queryset = Case.objects.all().select_related('loan', 'lossdata').order_by('-timestamp')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(CaseSummaryView, self).get_context_data(**kwargs)
        context['title'] = 'Case Summary'
        return context


class CaseAnalysisView(LoginRequiredMixin, TemplateView):
    context_object_name = 'object_list'
    model = WebCalculator
    template_name = 'case/caseAnalysis.html'

    def get_context_data(self, **kwargs):
        context = super(CaseAnalysisView, self).get_context_data(**kwargs)
        context['title'] = 'Loan Analysis'
        return context


# Case Email
class CaseEmailEligibility(LoginRequiredMixin, TemplateView):
    template_name = 'case/caseEmail.html'
    model = Case

    def get(self, request, *args, **kwargs):
        email_context={}
        caseUID = str(kwargs['uid'])

        queryset = Case.objects.queryset_byUID(str(caseUID))
        obj = queryset.get()

        clientDict = queryset.values()[0]
        loanObj = LoanValidator([], clientDict)
        email_context['enquiry'] = loanObj.chkClientDetails()
        email_context['obj']=obj

        subject, from_email, to = "Eligibility Summary", settings.DEFAULT_FROM_EMAIL, self.request.user.email
        text_content = "Text Message"

        html = get_template(self.template_name)
        html_content = html.render(email_context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        messages.success(self.request, "A draft email has been sent to you")
        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'pk':obj.pk}))


