from urllib.parse import urljoin

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

    enq_obj = convert_to_enquiry(calculator, proposed_owner)
    if enq_obj.user is None: 
        lead = enq_obj.case
        lead_owner = lead.owner
        if lead_owner is not None: 
            enq_obj.user = lead_owner 
            enq_obj.save(should_sync=False)
    try:
        calculator.actioned = 1
        calculator.save(update_fields=['actioned'])

        if not enq_obj.status:
            raise ProcessingError("Age or Postcode Restriction - please respond to customer")

        if enq_obj.user:
            app.send_task(
                'Webcalc_gen_and_email', 
                kwargs={
                    'enqUID': str(enq_obj.enqUID),
                    'calcUID': str(calculator.calcUID)
                }
            )
            #generate_and_email.delay(enq_obj.enqUID, calculator.calcUID)
            # pdf = gen_calc_summary(enq_obj, calculator)
            # email_customer(pdf, enq_obj, calculator)
    finally:
        attempt_sync(enq_obj, pause_for_dups)
