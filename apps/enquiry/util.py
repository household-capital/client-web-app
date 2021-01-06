
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
            'user' : user,
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
                write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Assigning enquiry (%s) to user %s' % (enquiry.enqUID, user.username))

                if enquiry.user:
                    enquiry.enquiryNotes += '\r\n[# Enquiry assigned from ' + enquiry.user.username + ' #]'
                elif enquiry.referrer == directTypesEnum.BROKER.value:
                    enquiry.enquiryNotes += '\r\n[# Enquiry assigned from ' + enquiry.referralUser.profile.referrer.companyName + ' #]'

                enquiry.user = user
                enquiry.save()
                processed.append(enquiry)
                write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Succeeded')
        except Exception as ex:
            try:
                send_summary_email(user, processed)
            except Exception as ex:
                write_applog('ERROR', 'enquiry.util', 'assign_enquiries', 'Could not send email', is_exception=True)
            raise

        write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Sending summary email')
        send_summary_email(user, processed)
        write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Summary email sent')


def assign_enquiry(enquiry, user_id):
    return assign_enquiries({user_id: [enquiry]})


def _filter_calc_assignees(assignees):
    return [
        assignee for assignee in assignees
        if assignee.profile.isCreditRep and assignee.profile.calendlyUrl
    ]


_AUTO_ASSIGN_LEADSOURCE_LOOKUP = {
    directTypesEnum.WEB_CALCULATOR.value: ('autoassignees_calculators',  _filter_calc_assignees)
}

_AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP = {
}


def find_auto_assignee(referrer, marketing_source, global_settings=None):
    if global_settings is None:
        global_settings = GlobalSettings.load()

    user_field = None
    if referrer in _AUTO_ASSIGN_LEADSOURCE_LOOKUP:
        user_field, choice_filter = _AUTO_ASSIGN_LEADSOURCE_LOOKUP[referrer]
    elif marketing_source in _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP:
        user_field, choice_filter = _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP[marketing_source]

    if not user_field:
        return None

    users = choice_filter(getattr(global_settings, user_field).all())
    if not users:
        return None

    return random.choice(users)


def auto_assign_enquiries(enquiries):
    global_settings = GlobalSettings.load()
    assignments = {}

    for enquiry in enquiries:
        user = find_auto_assignee(enquiry.referrer, enquiry.marketingSource, global_settings)
        assignments.setdefault(user.id, []).append(enquiry)

    if assignments:
        return assign_enquiries(assignments)
