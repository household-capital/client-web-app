# Python Imports
from datetime import datetime
import json
import base64
import uuid

# Django Imports
from django.core.files import File
from django.conf import settings

# Third-party Imports
from config.celery import app

# Local Application Imports

from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError, sendTemplateEmail

from .models import Application


# CASE TASKS

@app.task(name="Email_App_Link")
def emailAppLink(appUID, signedURL):
    obj = Application.objects.filter(appUID=uuid.UUID(appUID)).get()
    email_template = 'application/email/email_application_link.html'
    email_context = {}
    email_context['obj'] = obj
    email_context['signedURL'] = signedURL
    email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
    subject, from_email, to = "Application Link", \
                              'noreply@householdcapital.com', \
                              [obj.email]

    emailSent = sendTemplateEmail(email_template, email_context, subject, from_email, to)

    if not emailSent:
        write_applog("ERROR", 'application', 'emailAppLink', "Application email link not sent")
        raiseTaskAdminError("Application email could not be sent", "Application | emailAppLink |" + str(obj.appUID))

    # Record document sent
    obj.loanSummarySent = True
    obj.loanSummaryAmount = obj.totalPlanAmount
    obj.save()

    return "Loan Summary Sent!"


@app.task(name="Email_App_Summary")
def EmailLoanSummaryTask(appUID):
    email_template = 'application/email/email_loan_summary.html'

    dateStr = datetime.now().strftime('%Y-%m-%d-%H:%M:%S%z')

    sourceUrl = 'https://householdcapital.app/application/pdfLoanSummary/' + appUID
    componentFileName = settings.MEDIA_ROOT + "/customerReports/Component-" + appUID[-12:] + ".pdf"
    componentURL = 'https://householdcapital.app/media/' + "/customerReports/Component-" + appUID[-12:] + ".pdf"
    targetFileName = settings.MEDIA_ROOT + "/customerReports/Summary-" + appUID[-12:] + "-" + dateStr + ".pdf"

    pdf = pdfGenerator(appUID)
    created, text = pdf.createPdfFromUrl(sourceUrl, 'HouseholdSummary.pdf', componentFileName)

    if not created:
        write_applog("ERROR", 'PdfProduction', 'get',
                     "Failed to generate loan application summary: " + appUID + " - " + text)
        raiseTaskAdminError('Application Error',
                            "Failed to generate loan application summary: " + appUID + " - " + text)
        return 'Task Failed'

    # Merge Additional Components
    urlList = [componentURL,
               'https://householdcapital.app/static/img/document/LoanSummaryAdditional.pdf']

    created, text = pdf.mergePdfs(urlList=urlList, pdfDescription="HHC-LoanSummary.pdf",
                                  targetFileName=targetFileName)

    if not created:
        write_applog("ERROR", 'PdfProduction', 'get',
                     "Failed to generate loan application summary: " + appUID +  " - " + text)
        raiseTaskAdminError('Application Error',
                            "Failed to generate loan application summary: " + appUID +  " - " + text)
        return 'Task Failed'
    else:
        try:
            # SAVE TO DATABASE
            localfile = open(targetFileName, 'rb')

            qsApp = Application.objects.queryset_byUID(appUID)
            qsApp.update(summaryDocument=File(localfile))
            obj = qsApp.get()

            email_context = {}
            email_context['obj'] = obj
            email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
            email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

            result = pdf.emailPdf(email_template, email_context, 'Household Capital Loan Summary',
                                  'info@householdcapital.com',
                                  obj.email, None, 'Household Loan Summary', 'LoanSummary.pdf')

            if result == False:
                write_applog("ERROR", 'EmailLoanSummary', 'get',
                             "Failed to email loan application: " + appUID)
                raiseTaskAdminError('Application Error', "Failed to email loan application summary: " + appUID)

                return 'Task Failed'

        except:
            write_applog("ERROR", 'PdfProduction', 'get',
                         "Failed to save loan application summary: " + appUID)
            raiseTaskAdminError('Application Error', "Failed to save loan application summary: " + appUID)

            return "Task Failed"

    return 'Task Success!'
