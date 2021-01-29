
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


def _assign_enquiries(assignments):

    def send_summary_email(user, enquiries):
        subject, from_email, to = "Enquiry(s) Assigned to You", "noreply@householdcapital.app", user.email
        text_content = "Text Message"
        email_context = {
            'user': user,
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

        if user_id is not None:
            user = User.objects.get(id=user_id)
            username = user.username
        else:
            user = None
            username = "Unassigned"

        processed = []
        try:
            for enquiry in enquiries:
                write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Assigning enquiry (%s) to user %s' % (enquiry.enqUID, username))

                if enquiry.user:
                    enquiry.enquiryNotes += '\r\n[# Enquiry assigned from ' + enquiry.user.username + ' to ' + username + ' #]'
                elif enquiry.referrer == directTypesEnum.BROKER.value:
                    enquiry.enquiryNotes += '\r\n[# Enquiry assigned from ' + enquiry.referralUser.profile.referrer.companyName + ' to ' + username + ' #]'

                enquiry.user = user
                enquiry.save()
                processed.append(enquiry)
                write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Succeeded')
        except Exception as ex:
            if user is not None:
                try:
                    write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Sending summary email')
                    send_summary_email(user, processed)
                    write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Summary email sent')
                except Exception as ex:
                    write_applog('ERROR', 'enquiry.util', 'assign_enquiries', 'Could not send email', is_exception=True)
            raise

        if user is not None:
            write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Sending summary email')
            send_summary_email(user, processed)
            write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Summary email sent')


def assign_enquiry(enquiry, user):
    return _assign_enquiries({user.id: [enquiry]})


def _filter_calc_assignees(assignees):
    return [
        assignee for assignee in assignees
        if assignee.is_active and assignee.profile.isCreditRep and assignee.profile.calendlyUrl
    ]


def _filter_partner_assignees(assignees):
    return [
        assignee for assignee in assignees
        if assignee.is_active #and assignee.profile.isCreditRep
    ]


def _filter_social_assignees(assignees):
    return [
        assignee for assignee in assignees
        if assignee.is_active #and assignee.profile.isCreditRep
    ]

_AUTO_ASSIGN_LEADSOURCE_LOOKUP = {
    directTypesEnum.WEB_CALCULATOR.value: ('autoassignees_calculators',  _filter_calc_assignees),
}

_AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP = {
    marketingTypesEnum.STARTS_AT_60.value: ('autoassignees_STARTS_AT_60',  _filter_partner_assignees),
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
        write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Checking duplicates for (%s, %s)' % (phoneNumber, email))
        duplicates = Enquiry.objects.find_duplicates(email, phoneNumber, order_by="-updated")
        dup_owners = [duplicate.user for duplicate in duplicates if duplicate.user is not None]
        dup_owners = [owner for owner in dup_owners if owner.is_active]
        if choice_filter:
            dup_owners = choice_filter(dup_owners)
        if dup_owners:
            write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Using duplicate assignee')
            return dup_owners[0]

    # next try to use the system settings to find an active assignee
    if settings_assignee_field:
        write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Checking system settings')
        users = choice_filter(getattr(global_settings, settings_assignee_field).all())
        users = [user for user in users if user.is_active]
        if users:
            write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Using settings assignee')
            return random.choice(users)

    write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Failed to locate potential assignee')
    return None


def auto_assign_enquiries(enquiries, force=False):
    global_settings = GlobalSettings.load()
    assignments = {}

    for enquiry in enquiries:
        old_user = enquiry.user

        # if we aren't forcing an assignment, may as well keep existing user
        if not force and (old_user is not None) and old_user.is_active:
            continue

        # find a user, but if not forcing we can use the user from a duplicate enquiry
        user = find_auto_assignee(
            referrer=enquiry.referrer,
            marketing_source=enquiry.marketingSource,
            email=(enquiry.email if not force else None),
            phoneNumber=(enquiry.phoneNumber if not force else None),
            global_settings=global_settings
        )

        if user is not None:
            if (old_user is not None) and (user.username == old_user.username):
                # nothing to do, same user as before
                continue
        else:
            if old_user is None:
                # nothing to do, same user as before
                continue

        if user:
            assignments.setdefault(user.id, []).append(enquiry)
        elif force:
            # if forcing and no user available, set the owner to None
            assignments.setdefault(None, []).append(enquiry)

    if assignments:
        return _assign_enquiries(assignments)

