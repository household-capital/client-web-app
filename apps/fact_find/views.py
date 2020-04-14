# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.files import File
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView, View, UpdateView

# Third-party Imports
from config.celery import app

# Local Application Imports
from .forms import FactFindForm
from apps.case.models import ModelSetting, Loan, Case, FactFind
from apps.lib.site_Enums import loanTypesEnum
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Globals import ECONOMIC, APP_SETTINGS, LOAN_LIMITS
from apps.lib.hhc_LoanValidator import LoanValidator
from apps.lib.hhc_LoanProjection import LoanProjection
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import HouseholdLoginRequiredMixin, validateLoanGetContext, getProjectionResults
from apps.lib.site_DataMapping import serialisePurposes



# Utilities
class ContextHelper():
    # Most of the views require the same validation and context information

    def getLoanContext(self):

        caseUID = self.request.session['caseUID']

        # Validate the loan and generate combined context
        context = validateLoanGetContext(caseUID)

        # Get projection results (site utility using Loan Projection)
        projectionContext = getProjectionResults(context, ['baseScenario', 'intPayScenario',
                                                           'stressScenario'])
        context.update(projectionContext)

        return context


# CLASS BASED VIEWS

class Main(HouseholdLoginRequiredMixin, ContextHelper,  UpdateView):
    template_name = "fact_find/main.html"
    form_class = FactFindForm
    model = FactFind

    def get(self,request, *args, **kwargs):

        if request.user.profile.isCreditRep != True and request.user.is_superuser != True:
            messages.error(self.request, "Must be a Credit Rep to access summary")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail',kwargs={'uid': str(kwargs['uid'])}))

        # Main entry view - save the UID into a session variable
        # Use this to retrieve queryset for each page
        caseUID = str(kwargs['uid'])
        request.session['caseUID'] = caseUID
        return super(Main, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.getLoanContext()

        context = super(Main, self).get_context_data(**kwargs)
        context['title'] = 'Case Summary'

        return context

    def get_object(self, queryset=None):
        case = Case.objects.queryset_byUID(self.request.session['caseUID']).get()
        queryset = FactFind.objects.queryset_byUID(self.request.session['caseUID'])
        if queryset.count() == 0:
            #Create object
            obj = FactFind(case=case)
        else:
            obj = queryset.get()

        #Check if empty
        if not obj.backgroundNotes:
            obj.backgroundNotes = case.caseNotes
        obj.save(update_fields=['backgroundNotes'])

        return obj

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.save()

        self.success_url=self.request.path_info

        return super(Main, self).form_valid(form)


class PdfCaseSummary(ContextHelper,  TemplateView):
    # This page is not designed to be viewed - it is to be called by the pdf generator
    # It requires a UID to be passed to it

    template_name = "fact_find/pdfCaseSummary.html"
    model = FactFind

    def get(self,request, *args, **kwargs):
        # Main entry view - save the UID into a session variable
        # Use this to retrieve queryset for each page
        caseUID = str(kwargs['uid'])
        request.session['caseUID'] = caseUID
        return super(PdfCaseSummary, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.getLoanContext()

        context = super(PdfCaseSummary, self).get_context_data(**kwargs)
        context['title'] = 'Case Summary'
        return context

    def get_object(self, queryset=None):
        queryset = FactFind.objects.queryset_byUID(self.request.session['caseUID'])
        if queryset.count() == 0:
            #Create object
            case = Case.objects.queryset_byUID(self.request.session['caseUID']).get()
            obj = FactFind(case = case)
            obj.backgroundNotes = case.caseNotes
            obj.save()
        else:
            obj = queryset.get()
        return obj


class GeneratePdf(View):

    def get(self,request, *args, **kwargs):

        caseUID = str(kwargs['uid'])
        obj = Case.objects.filter(caseUID=self.kwargs.get('uid')).get()

        sourceUrl = 'https://householdcapital.app/factfind/pdfCaseSummary/' + self.request.session['caseUID']
        targetFileName = settings.MEDIA_ROOT + "/customerReports/CaseSummary-" + self.request.session['caseUID'][
                                                                             -12:] + ".pdf"
        pdf = pdfGenerator(caseUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'CaseSummary.pdf', targetFileName)

        if not created:
            messages.error(self.request, "Meeting Summary not generated")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': self.request.session['caseUID']}))

        try:
            # SAVE TO DATABASE
            localfile = open(targetFileName, 'rb')

            qsCase = Case.objects.queryset_byUID(self.request.session['caseUID'])
            qsCase.update(responsibleDocument=File(localfile), )

            pdf_contents = localfile.read()
            localfile.close()

        except:
            write_applog("ERROR", 'GeneratePdf', 'get',
                         "Failed to save Meeting Summary in Database: " + self.request.session['caseUID'])
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': self.request.session['caseUID']}))

        messages.success(self.request, "Meeting Summary generated")

        #Call Synch document task
        if obj.sfOpportunityID:
            app.send_task('SF_Doc_Synch', kwargs={'caseUID': str(obj.caseUID)})

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': self.request.session['caseUID']}))
