# Python Imports
from datetime import datetime, timedelta
import uuid

# Django Imports
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.core import signing
from django.urls import reverse_lazy, reverse
from django.utils import timezone


# Third-party Imports
from config.celery import app

# Local Application Imports
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError
from apps.lib.site_EmailUtils import sendTemplateEmail
from apps.lib.site_Enums import loanTypesEnum, appStatusEnum

from .models import Application, ApplicationDocuments
from apps.case.models import Case

from urllib.parse import urljoin

from apps.operational.decorators import email_admins_on_failure

# CASE TASKS

@app.task(name="Email_App_Link")
def emailAppLink(appUID):
    """Email application link to customer (signed url)"""

    payload = {'appUID': appUID,
               'action': 'Application'}

    signed_payload = signing.dumps(payload)
    signedURL = urljoin(
        settings.SITE_URL, 
        str(reverse_lazy('application:validateReturn', kwargs={'signed_pk': signed_payload}))
    )

    obj = Application.objects.filter(appUID=uuid.UUID(appUID)).get()
    email_template = 'application/email/email_application_link.html'
    email_context = {}
    email_context['obj'] = obj
    email_context['signedURL'] = signedURL
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
    """Email Loan Summary to customer

    The Summary is comprised of a generated document (saved as a component) and a
    static document.  A second call to API2PDF merges these
    """

    email_template = 'application/email/email_loan_summary.html'

    dateStr = datetime.now().strftime('%Y-%m-%d-%H:%M:%S%z')

    sourceUrl = urljoin(
        settings.SITE_URL,
        reverse('application:pdfLoanSummary', kwargs={'uid': appUID})
    )
    
    componentFileName = "customerReports/Component-" + appUID[-12:] + ".pdf"
    componentURL = default_storage.url(componentFileName)
    targetFileName = "customerReports/Summary-" + appUID[-12:] + "-" + dateStr + ".pdf"

    #Generate Summary File
    pdf = pdfGenerator(appUID)
    created, text = pdf.createPdfFromUrl(sourceUrl, 'HouseholdSummary.pdf', componentFileName)

    if not created:
        write_applog("ERROR", 'PdfProduction', 'get',
                     "Failed to generate loan summary: " + appUID + " - " + text)
        raiseTaskAdminError('Application Error',
                            "Failed to generate loan summary: " + appUID + " - " + text)
        return 'Task Failed'

    # Merge Additional Components
    additionalDocument = staticfiles_storage.url('img/document/LoanSummaryAdditional.pdf')
    urlList = [componentURL, additionalDocument]

    created, text = pdf.mergePdfs(urlList=urlList, pdfDescription="HHC-LoanSummary.pdf",
                                  targetFileName=targetFileName)

    if not created:
        write_applog("ERROR", 'PdfProduction', 'get',
                     "Failed to generate loan application summary: " + appUID + " - " + text)
        raiseTaskAdminError('Application Error',
                            "Failed to generate loan application summary: " + appUID + " - " + text)
        return 'Task Failed'
    else:
        try:
            # Save to Database
            qsApp = Application.objects.queryset_byUID(appUID)
            qsApp.update(summaryDocument=targetFileName)
            obj = qsApp.get()

            email_context = {}
            email_context['obj'] = obj

            result = pdf.emailPdf(
                email_template, 
                email_context, 
                'Household Capital Loan Summary',
                'noreply@householdcapital.com',
                obj.email, 
                None, 
                'Household Loan Summary', 'LoanSummary.pdf',
                other_attachments=[
                    {
                        'name': "HHC-Brochure.pdf",
                        'type': 'application/pdf',
                        'content': staticfiles_storage.open('img/document/brochure.pdf', 'rb').read()
                    }
                ]
            )

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
    """Email Application Document received from customer """

    template_name = 'application/email/email_document.html'
    appObj = Application.objects.queryset_byUID(appUID).get()
    docObj = ApplicationDocuments.objects.filter(docUID=uuid.UUID(docUID)).get()

    email_context = {}
    email_context['appObj'] = appObj
    email_context['docObj'] = docObj

    subject, from_email, to = "Application Document Provided", "noreply@householdcapital.app", \
                              'customers@householdcapital.com'
    text_content = "Application document"

    result = sendTemplateEmail(template_name, email_context, subject, from_email,
                               to, cc=None, bcc=None)
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
    """Email Next Steps Email to customer
    This email is comprised of multiple components (signedURLs and documents) and varies depending
    on whether the loan is lowLVR
    """
    template = 'application/email/email_next_steps.html'
    template_alt = 'application/email/email_next_steps_low_lvr.html'
    appObj = Application.objects.queryset_byUID(appUID).get()

    # 1. Generate signed URL for Document Upload
    payload = {'appUID': appUID,
               'action': 'Documents'}

    signed_payload = signing.dumps(payload)
    signedURL = urljoin(
        settings.SITE_URL,
        str(reverse_lazy('application:validateReturn',kwargs={'signed_pk': signed_payload}))
    )

    # 2. Generate signed URL for Bankstatements
    payload = {'appUID': appUID,
               'action': 'Bankstatements'}

    signed_payload_bs = signing.dumps(payload)
    signedURLBS = urljoin(
        settings.SITE_URL,
        str(reverse_lazy('application:validateReturn', kwargs={'signed_pk': signed_payload_bs}))
    )

    email_context = {}
    email_context['obj'] = appObj
    email_context['signedURL'] = signedURL
    email_context['signedURLBS'] = signedURLBS

    # 3. Generate Application Summary
    attachments = []
    sourceUrl = urljoin(
        settings.SITE_URL,
        reverse('application:pdfApplication', kwargs={'uid': appUID})
    ) 
    targetFileName = "customerReports/ApplicationSummary-" + appUID + ".pdf"

    pdf = pdfGenerator(appUID)
    created, text = pdf.createPdfFromUrl(sourceUrl, 'HHC-ApplicationSummary.pdf', targetFileName)

    if not created:
        raiseTaskAdminError("Application summary generation failed", "Application for " + appObj.surname_1)

    qsApp = Application.objects.queryset_byUID(appUID)
    qsApp.update(applicationDocument=targetFileName)
    appObj = qsApp.get()

    attachments.append(('ApplicationSummary.pdf', appObj.applicationDocument.name))

    # Save document to Case
    qsCase = Case.objects.get(caseUID=caseUID)
    qsCase.applicationDocument = appObj.applicationDocument.name
    qsCase.save(should_sync=True)
    
    # 4. Australia Post Attachments
    filePath = 'img/document/AustraliaPostVOI.pdf'
    if appObj.loanType == loanTypesEnum.JOINT_BORROWER.value:
        attachments.append(('AustraliaPostVOI-1.pdf', filePath, True))
        attachments.append(('AustraliaPostVOI-2.pdf', filePath, True))
    else:
        attachments.append(('AustraliaPostVOI-1.pdf', filePath, True))

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


@app.task(name="ApplicationFollowUp")
@email_admins_on_failure(task_name='ApplicationFollowUp')
def appFollowUp():
    """Send in-progress application customers a reminder email"""
    write_applog("INFO", 'Application', 'FollowUpEmail', "Starting")

    delta = timedelta(days=21)
    windowDate = timezone.now() - delta

    qs = Application.objects.filter(followUpEmail__isnull=True,
                                    timestamp__lte=windowDate,
                                    appStatus=appStatusEnum.IN_PROGRESS.value)[:75]
    # should not be more then 75 in a day - ensure no time out

    for app in qs:
        result = FollowUpEmail(str(app.appUID))
        if result['status'] == "Ok":
            write_applog("INFO", 'Application', 'FollowUpEmail', "Sent -" + app.surname_1)
        else:
            write_applog("ERROR", 'Enquiry', 'FollowUpEmail', "Failed -" + app.surname_1)

    write_applog("INFO", 'Application', 'FollowUpEmail', "Finished")
    return "Finished - Successfully"


# Follow Up Email
def FollowUpEmail(appUID):
    """Individual follow-up email"""

    template_name = 'application/email/email_followup.html'

    appObj = Application.objects.queryset_byUID(appUID).get()

    # Build context
    email_context = {}
    email_context['obj'] = appObj
    email_context['calendlyUrl'] = 'https://calendly.com/household-capital/15-minute-discovery-call'

    subject, from_email, to = "Household Capital: Application Follow-up", "info@householdcapital.com", appObj.email

    sentEmail = sendTemplateEmail(template_name, email_context, subject, from_email, to)

    if sentEmail:
        appObj.followUpEmail = timezone.now()
        appObj.save()

        write_applog("INFO", 'Application', 'Tasks-FollowUpEmail', "Follow-up Email Sent: "+appObj.surname_1)
        return {"status": "Ok", 'responseText': "Follow-up Email Sent"}
    else:
        write_applog("ERROR", 'Application', 'Tasks-FollowUpEmail',
                     "Failed to email follow-up:" + appObj.surname_1)
        return {"status": "ERROR", 'responseText': "Failed to email follow-up:" + appObj.surname_1}