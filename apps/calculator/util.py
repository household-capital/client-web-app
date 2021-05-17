from urllib.parse import urljoin
import time

from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.contrib.staticfiles.storage import staticfiles_storage

from config.celery import app

from apps.lib.site_Enums import directTypesEnum, enquiryStagesEnum
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC

from apps.enquiry.models import Enquiry
from .models import WebCalculator

from apps.case.assignment import auto_assign_leads, assign_lead


class ProcessingError(Exception):
    pass


def convert_calc(calculator, proposed_owner=None, pause_for_dups=True):

    def attempt_sync(enq_obj, pause_for_dups):
        try:
            if pause_for_dups and enq_obj.has_duplicate():
                # in case the dup was recently created, let's wait to give it time to finish a SF sync before
                # we start this one.
                write_applog("INFO", 'calculator.util', 'attempt_sync', "Pausing for 20 secs to allow duplicate to settle")
                time.sleep(20)
            app.send_task('Update_SF_Enquiry', kwargs={'enqUID': str(enq_obj.enqUID)})
        except Exception as ex:
            try:
                write_applog("ERROR", 'calculator.util', 'convert_calc', "Failed to sync " + str(enq_obj.enqUID), is_exception=True)
            except:
                pass
            pass

    def convert_to_enquiry(calculator, proposed_owner=None):
        if proposed_owner and not proposed_owner.profile.calendlyUrl:
            raise ProcessingError("You are not set-up to action this type of enquiry")

        calc_dict = WebCalculator.objects.dictionary_byUID(str(calculator.calcUID))

        # Create enquiry using WebCalculator Data
        # Remove certain items from the dictionary
        referrer = calc_dict['referrer']

        pop_list = ['calcUID', 'actionedBy', 'id', 'referrer', 'updated', 'timestamp', 'actioned', 'application', 'raw_name']
        for item in pop_list:
            calc_dict.pop(item)

        calc_dict['streetAddress'] = calc_dict['streetAddress'][:79] if calc_dict['streetAddress'] else None
        calc_dict['suburb'] = calc_dict['suburb'][:39] if calc_dict['suburb'] else None
        calc_dict['enquiryNotes'] = '[# Website Calculator #]'
        if calc_dict.get('submissionOrigin'):
            calc_dict['enquiryNotes'] += '\r\norigin: ' + calc_dict['submissionOrigin']

        enq_obj = Enquiry.objects.create(
            user=None, referrer=directTypesEnum.WEB_CALCULATOR.value, referrerID=referrer, **calc_dict
        )
        lead_obj = enq_obj.case

        if lead_obj.owner is None:
            if proposed_owner is None:
                auto_assign_leads([lead_obj], notify=False)
            else:
                assign_lead(lead_obj, proposed_owner, notify=False)
        
        enq_obj.refresh_from_db()
        return enq_obj

    def gen_calc_summary(enq_obj, calculator):
        # PRODUCE PDF REPORT
        source_url = urljoin(
            settings.SITE_URL,
            reverse('enquiry:enqSummaryPdf', kwargs={'uid': str(enq_obj.enqUID)})
        )
        target_file_name = "enquiryReports/Enquiry-" + str(enq_obj.enqUID)[-12:] + ".pdf"

        pdf = pdfGenerator(str(calculator.calcUID))
        created, text = pdf.createPdfFromUrl(source_url, 'CalculatorSummary.pdf', target_file_name)

        if not created:
            write_applog(
                "ERROR", 'calculator.util', 'convert_calc', "Enquiry created - but calc summary could not be generated for enquiry " + str(enq_obj.enqUID)
            )
            raise ProcessingError("Enquiry created - but calc summary could not be generated")

        try:
            # SAVE TO DATABASE (Enquiry Model)
            qs_enq = Enquiry.objects.queryset_byUID(str(enq_obj.enqUID))
            qs_enq.update(summaryDocument=target_file_name, enquiryStage=enquiryStagesEnum.SUMMARY_SENT.value)
        except Exception as ex:
            write_applog(
                "ERROR", 'calculator.util', 'convert_calc', "Failed to save Calc Summary in Database: " + str(enq_obj.enqUID), is_exception=True
            )

        return pdf

    def email_customer(pdf, enq_obj, calculator):
        template_name = 'calculator/email/email_cover_calculator.html'
        owner = enq_obj.user

        email_context = {}

        email_context['customerFirstName'] = calculator.firstname

        #  Get Rates
        email_context['loanRate'] = round(ECONOMIC['interestRate'] + ECONOMIC['lendingMargin'], 2)
        email_context['compRate'] = round(email_context['loanRate'] + ECONOMIC['comparisonRateIncrement'], 2)

        email_context['user'] = owner
        subject = "Household Capital: Your Personal Summary"
        from_email = owner.email
        to = calculator.email
        bcc = owner.email
        text_content = "Text Message"
        attach_filename = 'HHC-CalculatorSummary.pdf'

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
            raise ProcessingError("Enquiry created - but email not sent")

    enq_obj = convert_to_enquiry(calculator, proposed_owner)
    try:
        calculator.actioned = 1
        calculator.save(update_fields=['actioned'])

        if not enq_obj.status:
            raise ProcessingError("Age or Postcode Restriction - please respond to customer")

        if enq_obj.user:
            pdf = gen_calc_summary(enq_obj, calculator)
            email_customer(pdf, enq_obj, calculator)
    finally:
        attempt_sync(enq_obj, pause_for_dups)
