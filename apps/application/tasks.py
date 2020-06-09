# Python Imports
from datetime import datetime
import json
import base64
import uuid

# Django Imports
from django.core.files import File
from django.conf import settings
from django.core import signing
from django.urls import reverse_lazy


# Third-party Imports
from config.celery import app

# Local Application Imports

from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError, sendTemplateEmail
from apps.lib.site_Enums import loanTypesEnum

from .models import Application, ApplicationDocuments
from apps.case.models import Case


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

    return "App Link Sent!"


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
                     "Failed to generate loan summary: " + appUID + " - " + text)
        raiseTaskAdminError('Application Error',
                            "Failed to generate loan summary: " + appUID + " - " + text)
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
                                  'noreply@householdcapital.com',
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


@app.task(name="Email_Document")
def email_document(appUID, docUID):

    template_name = 'application/email/email_document.html'
    appObj = Application.objects.queryset_byUID(appUID).get()
    docObj = ApplicationDocuments.objects.filter(docUID=uuid.UUID(docUID)).get()

    email_context = {}
    email_context['appObj'] = appObj
    email_context['docObj'] = docObj
    email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
    email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL

    attachment = (docObj.enumDocumentType + ".pdf", docObj.document.path)

    subject, from_email, to = "Application Document Provided", "noreply@householdcapital.app", \
                              'paul.murray@householdcapital.com' #Change to customers
    text_content = "Application document"

    result = sendTemplateEmail(template_name, email_context, subject, from_email,
                               to, cc=None, bcc=None, attachments=[attachment])
    if result == False:
        write_applog("ERROR", 'Application-Task', 'Email_Document',
                     "Failed to email customer document:" + appObj.surname_1)
        raiseTaskAdminError("Application Document Error",
                        "Failed to email customer document:" + appObj.surname_1)
        return "Task Failed"

    else:
        return 'Task Success!'


@app.task(name="Email_Next_Steps")
def next_steps_email(appUID, caseUID):
        template = 'application/email/email_next_steps.html'
        template_alt = 'application/email/email_next_steps_low_lvr.html'
        appObj = Application.objects.queryset_byUID(appUID).get()

        #1. Generate signed URL for Document Upload
        payload = {'appUID': appUID,
                   'action': 'Documents'}

        signed_payload = signing.dumps(payload)
        signedURL = settings.SITE_URL + str(reverse_lazy('application:validateReturn',
                                                         kwargs={'signed_pk': signed_payload}))

        #2. Generate signed URL for Bankstatements
        payload = {'appUID': appUID,
                   'action': 'Bankstatements'}

        signed_payload_bs = signing.dumps(payload)
        signedURLBS = settings.SITE_URL + str(reverse_lazy('application:validateReturn',
                                                         kwargs={'signed_pk': signed_payload_bs}))

        email_context = {}
        email_context['obj'] = appObj
        email_context['absolute_url'] = settings.SITE_URL + settings.STATIC_URL
        email_context['absolute_media_url'] = settings.SITE_URL + settings.MEDIA_URL
        email_context['signedURL'] = signedURL
        email_context['signedURLBS'] = signedURLBS

        #3. Generate Application Summary
        attachments=[]
        sourceUrl = 'https://householdcapital.app/application/pdfApplication/' + appUID
        targetFileName = settings.MEDIA_ROOT + "/customerReports/ApplicationSummary-" + appUID + ".pdf"

        pdf = pdfGenerator(appUID)
        created, text = pdf.createPdfFromUrl(sourceUrl, 'HHC-ApplicationSummary.pdf', targetFileName)

        if not created:
            raiseTaskAdminError("Application summary generation failed", "Application for "+appObj.surname_1 )

        localfile = open(targetFileName, 'rb')

        qsApp = Application.objects.queryset_byUID(appUID)
        qsApp.update(applicationDocument=File(localfile))
        appObj = qsApp.get()

        attachments.append(('ApplicationSummary.pdf', appObj.applicationDocument.path))

        #Save document to Case
        qsCase = Case.objects.queryset_byUID(caseUID)
        qsCase.update(applicationDocument=appObj.applicationDocument.path)

        #4. Australia Post Attachments
        filePath = settings.STATICFILES_DIRS[0] + '/img/document/AustraliaPostVOI.pdf'
        if appObj.loanType == loanTypesEnum.JOINT_BORROWER.value:
            attachments.append(('AustraliaPostVOI-1.pdf',filePath))
            attachments.append(('AustraliaPostVOI-2.pdf', filePath))
        else:
            attachments.append(('AustraliaPostVOI-1.pdf',filePath))

        subject, from_email, to = "Application Received - Next Steps", "customers@householdcapital.com", \
                                  appObj.email
        text_content = "Next steps"

        if appObj.isLowLVR:
            template_name = template_alt
        else:
            template_name = template

        result = sendTemplateEmail(template_name, email_context, subject, from_email,
                                   to, cc=None, bcc=None, attachments=attachments)

        if result == False:
            write_applog("ERROR", 'Application-Task', 'Email_Next_Steps',
                         "Failed to email next steps:" + appObj.surname_1)
            raiseTaskAdminError("Application Next Steps Email Error",
                                "Failed to email next steps:" + appObj.surname_1)
            return "Task Failed"

        else:
            return 'Task Success!'

