
import random
import logging

from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives

from apps.settings.models import GlobalSettings
from apps.lib.site_Enums import *
from apps.lib.site_Logging import write_applog
from .models import Enquiry


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


def _filter_partner_assignees(assignees):
    return [
        assignee for assignee in assignees if assignee.profile.isCreditRep
    ]


def _filter_social_assignees(assignees):
    return [
        assignee for assignee in assignees if assignee.profile.isCreditRep
    ]

_AUTO_ASSIGN_LEADSOURCE_LOOKUP = {
    directTypesEnum.WEB_CALCULATOR.value: ('autoassignees_calculators',  _filter_calc_assignees),
}

_AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP = {
    marketingTypesEnum.STARTS_AT_60.value: ('autoassignees_STARTS_AT_60',  _filter_calc_assignees),
    marketingTypesEnum.CARE_ABOUT.value: ('autoassignees_CARE_ABOUT',  _filter_partner_assignees),
    marketingTypesEnum.NATIONAL_SENIORS.value: ('autoassignees_NATIONAL_SENIORS',  _filter_partner_assignees),
    marketingTypesEnum.YOUR_LIFE_CHOICES.value: ('autoassignees_YOUR_LIFE_CHOICES',  _filter_partner_assignees),
    marketingTypesEnum.FACEBOOK.value: ('autoassignees_FACEBOOK',  _filter_social_assignees),
    marketingTypesEnum.LINKEDIN.value: ('autoassignees_LINKEDIN',  _filter_social_assignees),
}


def find_auto_assignee(referrer=None, marketing_source=None, email=None, phoneNumber=None, global_settings=None):

    write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'BEGIN')

    if global_settings is None:
        global_settings = GlobalSettings.load()

    settings_assignee_field = None
    choice_filter = None

    if referrer in _AUTO_ASSIGN_LEADSOURCE_LOOKUP:
        settings_assignee_field, choice_filter = _AUTO_ASSIGN_LEADSOURCE_LOOKUP[referrer]
    elif marketing_source in _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP:
        settings_assignee_field, choice_filter = _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP[marketing_source]

    # First we honour using the same owner as a existing duplicate enquiry
    if email or phoneNumber:
        write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Checking duplicates')
        duplicates = Enquiry.objects.find_duplicates(email, phoneNumber, order_by="-updated")
        dup_owners = [duplicate.user for duplicate in duplicates if duplicate.user is not None]
        if choice_filter:
            dup_owners = choice_filter(dup_owners)
        if dup_owners:
            write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Using duplicate assignee')
            return dup_owners[0]

    # next try to use the system settings to find an active assignee
    if settings_assignee_field:
        write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Checking system settings')
        users = choice_filter(getattr(global_settings, settings_assignee_field).all())
        if users:
            write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Using settings assignee')
            return random.choice(users)

    write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Failed to locate potential assignee')
    return None


def auto_assign_enquiries(enquiries):
    global_settings = GlobalSettings.load()
    assignments = {}

    for enquiry in enquiries:
        user = find_auto_assignee(
            enquiry.referrer, enquiry.marketingSource, enquiry.email, enquiry.phoneNumber, global_settings
        )
        if user:
            assignments.setdefault(user.id, []).append(enquiry)

    if assignments:
        return assign_enquiries(assignments)

