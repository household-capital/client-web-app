
import random
import logging

from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives

from apps.settings.models import GlobalSettings
from apps.lib.site_Enums import *
from apps.lib.site_Logging import write_applog


def assign_enquiries(assignments):

    def send_summary_email(user, enquiries):
        subject, from_email, to = "Enquiry(s) Assigned to You", "noreply@householdcapital.app", user.email
        text_content = "Text Message"
        email_context = {
            'enquiries': enquiries,
            'base_url': settings.SITE_URL,
        }
        html = get_template(email_template_name)
        html_content = html.render(email_context)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    email_template_name = 'enquiry/email/email_assign.html'

    for user_id, enquiries in assignments.items():
        user = User.objects.get(id=user_id)
        processed = []

        try:
            for enquiry in enquiries:

                if enquiry.user:
                    enquiry.enquiryNotes += '\r\n[# Enquiry assigned from ' + enquiry.user.username + ' #]'
                elif enquiry.referrer == directTypesEnum.BROKER.value:
                    enquiry.enquiryNotes += '\r\n[# Enquiry assigned from ' + enquiry.referralUser.profile.referrer.companyName + ' #]'

                enquiry.user = user
                enquiry.save()
                processed.append(enquiry)
        except:
            try:
                send_summary_email(user, processed)
            except Exception as ex:
                write_applog('ERROR', 'enquiry.util', 'assign_enquiries', 'Could not send email', is_exception=True)
            raise

        send_summary_email(user, processed)


def assign_enquiry(enquiry, user_id):
    return assign_enquiries({user_id: [enquiry]})


_AUTO_ASSIGN_LEADSOURCE_LOOKUP = {
    directTypesEnum.WEB_CALCULATOR.value: 'autoassignees_calculators'
}

_AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP = {

}

def auto_assign_enquiries(enquiries):
    global_settings = GlobalSettings.load()
    assignments = {}

    for enquiry in enquiries:

        user_field = None
        if enquiry.referrer in ASSIGN_LEADSOURCE_LOOKUP:
            user_field = ASSIGN_LEADSOURCE_LOOKUP[enquiry.referrer]
        elif enquiry.marketingSource in ASSIGN_MARKETINGSOURCE_LOOKUP:
            user_field = ASSIGN_MARKETINGSOURCE_LOOKUP[enquiry.marketingSource]

        if not user_field:
            continue

        users = global_settings[user_field]
        if not users:
            continue

        user = random.choice(users)
        assignments.setdefault(user.id, []).append(enquiry)

    if assignments:
        return assign_enquiries(assignments)
