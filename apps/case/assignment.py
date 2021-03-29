
import random
import logging

from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives

from apps.settings.models import GlobalSettings
from apps.lib.site_Enums import *
from apps.lib.site_Logging import write_applog

from apps.case.models import Case
from apps.case.note_utils import add_case_note


def _assign_leads(assignments, notify): 
    def send_summary_email(user, cases):
        if not cases:
            return
        subject = "Lead(s) Assigned to You"
        from_email = "noreply@householdcapital.app"
        to = user.email
        text_content = "Text Message"
        email_context = {
            'user': user,
            'leads': cases,
            'base_url': settings.SITE_URL,
        }
        html = get_template(email_template_name)
        html_content = html.render(email_context)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    
    email_template_name = 'case/email/email_assign.html'
    for user_id, leads in assignments.items():

        if user_id is not None:
            user = User.objects.get(id=user_id)
            username = user.username
        else:
            user = None
            username = "Unassigned"

        processed = []
        try:
            for lead in leads:
                write_applog('INFO', 'case.assignments', 'assign_leads', 'Assigning lead (%s) to user %s' % (lead.caseUID, username))
                if lead.owner:
                    add_case_note(lead, '[# Lead assigned from ' + lead.owner.username + ' to ' + username + ' #]', user=None)
                lead.owner = user
                lead.save(should_sync=True)
                processed.append(lead)
                write_applog('INFO', 'case.assignments', 'assign_leads', 'Succeeded')
        except Exception as ex:
            if notify and (user is not None):
                try:
                    write_applog('INFO', 'case.assignments', 'assign_leads', 'Sending summary email')
                    send_summary_email(user, processed)
                    write_applog('INFO', 'case.assignments', 'assign_leads', 'Summary email sent')
                except Exception as ex:
                    write_applog('ERROR', 'case.assignments', 'assign_leads', 'Could not send email', is_exception=True)
            raise

        if notify and (user is not None):
            write_applog('INFO', 'case.assignments', 'assign_leads', 'Sending summary email')
            send_summary_email(user, processed)
            write_applog('INFO', 'case.assignments', 'assign_leads', 'Summary email sent')


def assign_lead(lead, user, notify=True):
    return _assign_leads({user.id: [lead]}, notify)

def _filter_calc_assignees(assignees):
    return [
        assignee for assignee in assignees
        if assignee.profile.isCreditRep and assignee.profile.calendlyUrl
    ]


def _filter_partner_assignees(assignees):
    return [
        assignee for assignee in assignees
        #if assignee.profile.isCreditRep
    ]


def _filter_social_assignees(assignees):
    return [
        assignee for assignee in assignees
        #if assignee.profile.isCreditRep
    ]

_AUTO_ASSIGN_LEADSOURCE_LOOKUP = {
    directTypesEnum.WEB_CALCULATOR.value: {
        'settings_assignee_field': 'autoassignees_calculators',
        'choice_filter': _filter_calc_assignees,
    },
}

_AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP = {
    marketingTypesEnum.STARTS_AT_60.value: {
        'settings_assignee_field': 'autoassignees_STARTS_AT_60',
        'choice_filter': _filter_partner_assignees,
    },
    marketingTypesEnum.CARE_ABOUT.value: {
        'settings_assignee_field': 'autoassignees_CARE_ABOUT',
        'choice_filter': _filter_partner_assignees,
    },
    marketingTypesEnum.NATIONAL_SENIORS.value: {
        'settings_assignee_field': 'autoassignees_NATIONAL_SENIORS',
        'choice_filter': _filter_partner_assignees,
    },
    marketingTypesEnum.YOUR_LIFE_CHOICES.value: {
        'settings_assignee_field': 'autoassignees_YOUR_LIFE_CHOICES',
        'choice_filter': _filter_partner_assignees,
    },
    marketingTypesEnum.FACEBOOK.value: {
        'settings_assignee_field': 'autoassignees_FACEBOOK',
        'choice_filter': _filter_social_assignees,
    },
    marketingTypesEnum.LINKEDIN.value: {
        'settings_assignee_field': 'autoassignees_LINKEDIN',
        'choice_filter': _filter_social_assignees,
    },
}

def find_auto_assignee(referrer=None, marketing_source=None, email=None, phoneNumber=None, global_settings=None):

    def load_options():
        options = None

        if options is None and referrer in _AUTO_ASSIGN_LEADSOURCE_LOOKUP:
            options = _AUTO_ASSIGN_LEADSOURCE_LOOKUP[referrer]

        if options is None and marketing_source in _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP:
            options = _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP[marketing_source]

        return options or {}

    write_applog('INFO', 'case.assignment', 'find_auto_assignee', 'BEGIN')

    if global_settings is None:
        global_settings = GlobalSettings.load()

    options = load_options()

    # First we honour using the same owner as a existing duplicate lead
    if email or phoneNumber:
        write_applog('INFO', 'case.assignment', 'find_auto_assignee', 'Checking duplicates for (%s, %s)' % (phoneNumber, email))
        duplicates = Case.objects.find_duplicates(email, phoneNumber, order_by="-updated")
        potential_owners = [duplicate.owner for duplicate in duplicates if (duplicate.owner is not None and duplicate.owner.is_active)]
        if 'choice_filter' in options:
            potential_owners = options['choice_filter'](potential_owners)
        if potential_owners:
            write_applog('INFO', 'case.assignment', 'find_auto_assignee', 'Using duplicate assignee')
            return potential_owners[0]

    # next try to use the system settings to find an active assignee
    if 'settings_assignee_field' in options:
        write_applog('INFO', 'case.assignment', 'find_auto_assignee', 'Checking system settings')
        potential_owners = [user for user in getattr(global_settings, options['settings_assignee_field']).all() if user.is_active]
        if 'choice_filter' in options:
            potential_owners = options['choice_filter'](potential_owners)
        if potential_owners:
            write_applog('INFO', 'case.assignment', 'find_auto_assignee', 'Using settings assignee')
            return random.choice(potential_owners)

    write_applog('INFO', 'case.assignment', 'find_auto_assignee', 'Failed to locate potential assignee')
    return None


def auto_assign_leads(leads, force=False, notify=True):
    global_settings = GlobalSettings.load()
    assignments = {}

    for lead in leads:
        old_user = lead.owner

        # if we aren't forcing an assignment, may as well keep existing user
        if not force and (old_user is not None) and old_user.is_active:
            continue
        
        # find a user, but if not forcing we can use the user from a duplicate lead
        user = find_auto_assignee(
            referrer=lead.referrer,
            marketing_source=lead.channelDetail,
            email=(lead.email if not force else None),
            phoneNumber=(lead.phoneNumber if not force else None),
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
            assignments.setdefault(user.id, []).append(lead)
        elif force:
            # if forcing and no user available, set the owner to None
            assignments.setdefault(None, []).append(lead)

    if assignments:
        return _assign_leads(assignments, notify)

