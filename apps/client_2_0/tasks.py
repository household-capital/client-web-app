# Python Imports
from datetime import datetime

# Django Imports
from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse

# Third-party Imports
from config.celery import app

from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog

from apps.case.models import Case
from urllib.parse import urljoin

# TASKS
@app.task(name="Create_Loan_Summary")
def createLoanSummary(caseUID):

    qsCase = Case.objects.queryset_byUID(caseUID)
    qsCase.update(summaryDocument=None)

    dateStr = datetime.now().strftime('%Y-%m-%d-%H:%M:%S%z')

    sourceUrl = urljoin(
        settings.SITE_URL,
        reverse('client2:pdfLoanSummary', kwargs={'uid': caseUID})
    )
    componentFileName = "customerReports/Component-" + caseUID[-12:] + ".pdf"
    componentURL = default_storage.url(componentFileName)
    targetFileName = "customerReports/Summary-" + caseUID[-12:] + "-" + dateStr + ".pdf"

    pdf = pdfGenerator(caseUID)
    created, text = pdf.createPdfFromUrl(sourceUrl, 'HouseholdSummary.pdf', componentFileName)

    if not created:
        write_applog('ERROR', 'client2:tasks' ,'createLoanSummary', "Base PDF not generated")
        return 'Task Failed'

    # Merge Additional Components
    urlList = [
        componentURL,
        '{}static/img/document/LoanSummaryAdditional.pdf'.format(settings.SITE_URL)
    ]

    created, text = pdf.mergePdfs(urlList=urlList, pdfDescription="HHC-LoanSummary.pdf",
                                  targetFileName=targetFileName)

    if not created:
        write_applog('ERROR', 'client2:tasks', 'createLoanSummary', "Merged PDF not generated")
        return 'Task Failed'

    try:
        # SAVE TO DATABASE

        qsCase.update(summaryDocument=targetFileName)

        return "Loan Summary generated"

    except:
        write_applog("ERROR", 'PdfProduction', 'get',
                     "Failed to save Summary Report in Database: " + caseUID)
        return 'Task Failed'

