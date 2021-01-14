#Python Imports
from datetime import datetime

# Django Imports

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView, View, UpdateView
from django.conf import settings

# Third-party Imports
from config.celery import app

# Local Application Imports
from .forms import FactFindForm
from apps.case.models import ModelSetting, Loan, Case, FactFind

from apps.lib.api_Pdf import pdfGenerator

from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import HouseholdLoginRequiredMixin, validateLoanGetContext, getProjectionResults
from urllib.parse import urljoin

# Utilities
class ContextHelper():
    # Most of the views require the same validation and context information

    def getLoanContext(self):

        caseUID = str(self.kwargs['uid'])

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

        messages.info(request, "Remember to save as you go and hit exit to generate the Case Summary document")
        return super(Main, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        self.extra_context = self.getLoanContext()

        context = super(Main, self).get_context_data(**kwargs)
        context['title'] = 'Case Summary'
        return context

    def get_object(self, queryset=None):
        caseUID = str(self.kwargs['uid'])
        case = Case.objects.queryset_byUID(caseUID).get()
        queryset = FactFind.objects.queryset_byUID(caseUID)
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

    def get_context_data(self, **kwargs):
        # Update and add dictionaries to context
        self.extra_context = self.getLoanContext()

        caseUID = str(self.kwargs['uid'])

        context = super(PdfCaseSummary, self).get_context_data(**kwargs)
        context['title'] = 'Case Summary'
        context['factObj'] = self.get_object()
        context['clientObj'] = Case.objects.queryset_byUID(caseUID).get()

        return context

    def get_object(self, queryset=None):
        queryset = FactFind.objects.queryset_byUID(str(self.kwargs['uid']))
        if queryset.count() == 0:
            #Create object
            case = Case.objects.queryset_byUID(str(self.kwargs['uid'])).get()
            obj = FactFind(case = case)
            obj.backgroundNotes = case.caseNotes
            obj.save()
        else:
            obj = queryset.get()
        return obj


class GeneratePdf(View):

    def get(self,request, *args, **kwargs):

        dateStr = datetime.now().strftime('%Y-%m-%d-%H:%M:%S%z')

        caseUID = str(self.kwargs['uid'])
        obj = Case.objects.filter(caseUID=caseUID).get()

        sourceUrl = urljoin(
            settings.SITE_URL,
            reverse('fact_find:pdfSummary', kwargs={'uid': caseUID})
        )
        targetFileName = "customerReports/CaseSummary-" + caseUID[-12:] + "-" + dateStr + ".pdf"
        pdf = pdfGenerator(caseUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'CaseSummary.pdf', targetFileName)

        if not created:
            messages.error(self.request, "Meeting Summary not generated")
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseUID}))

        try:
            # SAVE TO DATABASE

            qsCase = Case.objects.queryset_byUID(caseUID)
            qsCase.update(responsibleDocument=targetFileName)


        except:
            write_applog("ERROR", 'GeneratePdf', 'get',
                         "Failed to save Meeting Summary in Database: " + caseUID)
            messages.error(request, "Failed to save Case Summary" )
            return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseUID}))

        messages.success(self.request, "Meeting Summary generated")

        #Call Synch document task
        if obj.sfOpportunityID:
            app.send_task('SF_Doc_Synch', kwargs={'caseUID': str(obj.caseUID)})
            app.send_task('SF_Opp_Synch', kwargs={'caseUID': str(obj.caseUID)})

        return HttpResponseRedirect(reverse_lazy('case:caseDetail', kwargs={'uid': caseUID}))


