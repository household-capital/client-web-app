from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse_lazy, reverse
from config.celery import app

from apps.lib.site_Enums import directTypesEnum, enquiryStagesEnum
from apps.lib.api_Pdf import pdfGenerator
from apps.lib.site_Logging import write_applog
from apps.lib.site_Globals import LOAN_LIMITS, ECONOMIC

from apps.enquiry.models import Enquiry
from .models import WebCalculator
from apps.enquiry.util import auto_assign_enquiries


class ProcessingError(Exception):
    pass


def convert_calc(calculator, proposed_owner=None):

    def attempt_sync(enq_obj):
        try:
            app.send_task('Create_SF_Lead', kwargs={'enqUID': str(enq_obj.enqUID)})
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
        referrer_id = calc_dict['sourceID']

        pop_list = ['calcUID', 'actionedBy', 'id', 'sourceID', 'referrer', 'updated', 'timestamp', 'actioned', 'application']
        for item in pop_list:
            calc_dict.pop(item)

        calc_dict['name'] = calc_dict['name'][:29] if calc_dict['name'] else None
        calc_dict['streetAddress'] = calc_dict['streetAddress'][:79] if calc_dict['streetAddress'] else None
        calc_dict['suburb'] = calc_dict['suburb'][:39] if calc_dict['suburb'] else None

        enq_obj = Enquiry.objects.create(
            user=proposed_owner, referrer=directTypesEnum.WEB_CALCULATOR.value, referrerID=referrer, **calc_dict
        )
        enq_obj.save()

        if proposed_owner is None:
            auto_assign_enquiries([enq_obj])

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

        #  Strip name
        if calculator.name:
            if " " in calculator.name:
                customer_first_name, surname = calculator.name.split(" ", 1)
            else:
                customer_first_name = calculator.name
            if len(customer_first_name) < 2:
                customer_first_name = None
        else:
            customer_first_name = None

        email_context['customerFirstName'] = customer_first_name

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

        sent = pdf.emailPdf(template_name, email_context, subject, from_email, to, bcc, text_content, attach_filename)

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
        attempt_sync(enq_obj)
