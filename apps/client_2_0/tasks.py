import traceback
# Python Imports
from datetime import datetime

# Django Imports
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.urls import reverse

# Third-party Imports
from config.celery import app

from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError
from apps.calculator.util import ProcessingError

from apps.case.models import Case
from urllib.parse import urljoin

from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC

# TASKS
@app.task(name="Create_Loan_Summary")
def createLoanSummary(caseUID):

    qsCase = Case.objects.get(caseUID=caseUID)
    qsCase.summaryDocument = None
    qsCase.save()

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
    staticFileURL = staticfiles_storage.url('img/document/LoanSummaryAdditional.pdf')

    urlList = [componentURL, staticFileURL]

    created, text = pdf.mergePdfs(urlList=urlList, pdfDescription="HHC-LoanSummary.pdf",
                                  targetFileName=targetFileName)

    if not created:
        write_applog('ERROR', 'client2:tasks', 'createLoanSummary', "Merged PDF not generated")
        return 'Task Failed'

    try:
        # SAVE TO DATABASE

        qsCase.summaryDocument = targetFileName
        qsCase.save(should_sync=True)
        return "Loan Summary generated"

    except:
        write_applog("ERROR", 'PdfProduction', 'get',
                     "Failed to save Summary Report in Database: " + caseUID)
        return 'Task Failed'

@app.task(name="Webcalc_gen_and_email_pre_ql")
def generate_and_email_pre_ql(caseUID):
    try:
        case_obj = Case.objects.get(caseUID=caseUID)
        pdf = gen_preql_summary(case_obj)
        email_preql(pdf, case_obj)
    except Exception as e:
        tb = traceback.format_exc()
        raiseTaskAdminError(
            "Failed preql gen/email - {}".format(str(caseUID)),
            tb
        )
        raise e

def gen_preql_summary(case_obj):
    source_url = urljoin(
        settings.SITE_URL,
        reverse('client2:pdfPreQualSummary', kwargs={'uid': case_obj.caseUID})
    )
    target_file_name = "enquiryReports/PreQL-" + str(case_obj.caseUID)[-12:] + ".pdf"
    pdf = pdfGenerator(str(case_obj.caseUID))
    created, text = pdf.createPdfFromUrl(source_url, 'PreQualSummary.pdf', target_file_name)
    if not created:
        write_applog(
            "ERROR", 'client_2_0.tasks', 'gen_preql_summary', "Preql summary could not be generated for enquiry " + str(case_obj.caseUID)
        )
        raise ProcessingError("Preql summary could not be generated")
    else:
        case_obj.preQualDocument = target_file_name
        case_obj.save()

    return pdf

def email_preql(pdf, caseObj):
    template_name = 'calculator/email/email_cover_preql.html'
    owner = caseObj.owner

    email_context = {}

    email_context['customerFirstName'] = caseObj.firstname_1
    name = "{} {}".format(
        caseObj.firstname_1 or '',
        caseObj.surname_1 or ''
    )
    paramStr = "?name=" + (name or '') + "&email=" + (caseObj.email_1 or '')
    #  Get Rates
    email_context['loanRate'] = round(ECONOMIC['interestRate'] + ECONOMIC['lendingMargin'], 2)
    email_context['compRate'] = round(email_context['loanRate'] + ECONOMIC['comparisonRateIncrement'], 2)
    email_context['calendlyUrl'] = owner.profile.calendlyUrl + paramStr
    email_context['user'] = owner
    subject = "Household Capital: Your Personal Pre Qualification Summary"
    from_email = owner.email
    to = caseObj.email_1
    bcc = owner.email
    text_content = "Text Message"
    attach_filename = 'HHC-PreQualSummary.pdf'

    sent = pdf.emailPdf(
        template_name, 
        email_context, 
        subject, 
        from_email, 
        to, 
        bcc, 
        text_content, 
        attach_filename,
        other_attachments=[
            {
                'name': "HHC-Brochure.pdf",
                'type': 'application/pdf',
                'content': staticfiles_storage.open('img/document/brochure.pdf', 'rb').read()
            }
        ]
    )

    if not sent:
        raise ProcessingError("Pre ql email not sent")