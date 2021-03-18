
import random
import logging
import datetime

from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

from apps.settings.models import GlobalSettings
from apps.lib.site_Enums import *
from apps.lib.site_Logging import write_applog
from apps.case.models import Case
from apps.case.assignment import auto_assign_leads
from apps.case.helpers import should_lead_owner_update
from .models import Enquiry

# DEPRECATE COMMENTED

# def _assign_enquiries(assignments, notify):

#     def send_summary_email(user, enquiries):
#         if not enquiries:
#             return
#         subject = "Enquiry(s) Assigned to You"
#         from_email = "noreply@householdcapital.app"
#         to = user.email
#         text_content = "Text Message"
#         email_context = {
#             'user': user,
#             'enquiries': enquiries,
#             'base_url': settings.SITE_URL,
#         }
#         html = get_template(email_template_name)
#         html_content = html.render(email_context)
#         msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
#         msg.attach_alternative(html_content, "text/html")
#         msg.send()

#     email_template_name = 'enquiry/email/email_assign.html'

#     for user_id, enquiries in assignments.items():

#         if user_id is not None:
#             user = User.objects.get(id=user_id)
#             username = user.username
#         else:
#             user = None
#             username = "Unassigned"

#         processed = []
#         try:
#             for enquiry in enquiries:
#                 write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Assigning enquiry (%s) to user %s' % (enquiry.enqUID, username))

#                 if enquiry.user:
#                     enquiry.enquiryNotes = (enquiry.enquiryNotes or '') + '\r\n[# Enquiry assigned from ' + enquiry.user.username + ' to ' + username + ' #]'
#                 elif enquiry.referrer == directTypesEnum.BROKER.value:
#                     enquiry.enquiryNotes = (enquiry.enquiryNotes or '') + '\r\n[# Enquiry assigned from ' + enquiry.referralUser.profile.referrer.companyName + ' to ' + username + ' #]'

#                 enquiry.user = user
#                 enquiry.save(should_sync=True)
#                 processed.append(enquiry)
#                 write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Succeeded')
#         except Exception as ex:
#             if notify and (user is not None):
#                 try:
#                     write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Sending summary email')
#                     send_summary_email(user, processed)
#                     write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Summary email sent')
#                 except Exception as ex:
#                     write_applog('ERROR', 'enquiry.util', 'assign_enquiries', 'Could not send email', is_exception=True)
#             raise

#         if notify and (user is not None):
#             write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Sending summary email')
#             send_summary_email(user, processed)
#             write_applog('INFO', 'enquiry.util', 'assign_enquiries', 'Summary email sent')


# def assign_enquiry(enquiry, user, notify=True):
#     return _assign_enquiries({user.id: [enquiry]}, notify)


# def _filter_calc_assignees(assignees):
#     return [
#         assignee for assignee in assignees
#         if assignee.profile.isCreditRep and assignee.profile.calendlyUrl
#     ]


# def _filter_partner_assignees(assignees):
#     return [
#         assignee for assignee in assignees
#         #if assignee.profile.isCreditRep
#     ]


# def _filter_social_assignees(assignees):
#     return [
#         assignee for assignee in assignees
#         #if assignee.profile.isCreditRep
#     ]

# _AUTO_ASSIGN_LEADSOURCE_LOOKUP = {
#     directTypesEnum.WEB_CALCULATOR.value: {
#         'settings_assignee_field': 'autoassignees_calculators',
#         'choice_filter': _filter_calc_assignees,
#     },
# }

# _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP = {
#     marketingTypesEnum.STARTS_AT_60.value: {
#         'settings_assignee_field': 'autoassignees_STARTS_AT_60',
#         'choice_filter': _filter_partner_assignees,
#     },
#     marketingTypesEnum.CARE_ABOUT.value: {
#         'settings_assignee_field': 'autoassignees_CARE_ABOUT',
#         'choice_filter': _filter_partner_assignees,
#     },
#     marketingTypesEnum.NATIONAL_SENIORS.value: {
#         'settings_assignee_field': 'autoassignees_NATIONAL_SENIORS',
#         'choice_filter': _filter_partner_assignees,
#     },
#     marketingTypesEnum.YOUR_LIFE_CHOICES.value: {
#         'settings_assignee_field': 'autoassignees_YOUR_LIFE_CHOICES',
#         'choice_filter': _filter_partner_assignees,
#     },
#     marketingTypesEnum.FACEBOOK.value: {
#         'settings_assignee_field': 'autoassignees_FACEBOOK',
#         'choice_filter': _filter_social_assignees,
#     },
#     marketingTypesEnum.LINKEDIN.value: {
#         'settings_assignee_field': 'autoassignees_LINKEDIN',
#         'choice_filter': _filter_social_assignees,
#     },
# }


# def find_auto_assignee(referrer=None, marketing_source=None, email=None, phoneNumber=None, global_settings=None):

#     def load_options():
#         options = None

#         if options is None and referrer in _AUTO_ASSIGN_LEADSOURCE_LOOKUP:
#             options = _AUTO_ASSIGN_LEADSOURCE_LOOKUP[referrer]

#         if options is None and marketing_source in _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP:
#             options = _AUTO_ASSIGN_MARKETINGSOURCE_LOOKUP[marketing_source]

#         return options or {}

#     write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'BEGIN')

#     if global_settings is None:
#         global_settings = GlobalSettings.load()

#     options = load_options()

#     # First we honour using the same owner as a existing duplicate enquiry
#     if email or phoneNumber:
#         write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Checking duplicates for (%s, %s)' % (phoneNumber, email))
#         duplicates = Enquiry.objects.find_duplicates(email, phoneNumber, order_by="-updated")
#         potential_owners = [duplicate.user for duplicate in duplicates if (duplicate.user is not None and duplicate.user.is_active)]
#         if 'choice_filter' in options:
#             potential_owners = options['choice_filter'](potential_owners)
#         if potential_owners:
#             write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Using duplicate assignee')
#             return potential_owners[0]

#     # next try to use the system settings to find an active assignee
#     if 'settings_assignee_field' in options:
#         write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Checking system settings')
#         potential_owners = [user for user in getattr(global_settings, options['settings_assignee_field']).all() if user.is_active]
#         if 'choice_filter' in options:
#             potential_owners = options['choice_filter'](potential_owners)
#         if potential_owners:
#             write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Using settings assignee')
#             return random.choice(potential_owners)

#     write_applog('INFO', 'enquiry.util', 'find_auto_assignee', 'Failed to locate potential assignee')
#     return None


# def auto_assign_enquiries(enquiries, force=False, notify=True):
#     global_settings = GlobalSettings.load()
#     assignments = {}

#     for enquiry in enquiries:
#         old_user = enquiry.user

#         # if we aren't forcing an assignment, may as well keep existing user
#         if not force and (old_user is not None) and old_user.is_active:
#             continue

#         # find a user, but if not forcing we can use the user from a duplicate enquiry
#         user = find_auto_assignee(
#             referrer=enquiry.referrer,
#             marketing_source=enquiry.marketingSource,
#             email=(enquiry.email if not force else None),
#             phoneNumber=(enquiry.phoneNumber if not force else None),
#             global_settings=global_settings
#         )

#         if user is not None:
#             if (old_user is not None) and (user.username == old_user.username):
#                 # nothing to do, same user as before
#                 continue
#         else:
#             if old_user is None:
#                 # nothing to do, same user as before
#                 continue

#         if user:
#             assignments.setdefault(user.id, []).append(enquiry)
#         elif force:
#             # if forcing and no user available, set the owner to None
#             assignments.setdefault(None, []).append(enquiry)

#     if assignments:
#         return _assign_enquiries(assignments, notify)


def assign_enquiry_leads(enquiries, force=False, notify=True):
    case_uids = set() 
    for enq in enquiries:
        case_uids |= {enq.case.caseUID}
    leads = list(Case.objects.filter(caseUID__in=case_uids))
    auto_assign_leads(leads, force=force, notify=notify)


def updateCreateEnquiry(
    email, 
    phoneNumber, 
    payload, 
    enquiryString, 
    marketingSource, 
    enquiries_to_assign, updateNonDirect=True):

    nonDirectTypes = [directTypesEnum.PARTNER.value, directTypesEnum.BROKER.value,
                      directTypesEnum.ADVISER.value]

    # Try find existing enquiry
    # No special logic needed to handle enquiry duplicates
    write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'Creating new enquiry')
    payload["enquiryNotes"] = enquiryString

    prev_sources = Enquiry.objects.find_duplicates(email, phoneNumber).values_list(
        'marketingSource', flat=True
    ) 
    if marketingSource not in prev_sources: 
        new_enq = Enquiry.objects.create(**payload)
        if should_lead_owner_update(new_enq.case):
            enquiries_to_assign.append(new_enq)
    else:
        write_applog(
            "INFO", 'Enquiry', 'EnquiryPartnerUpload',
            'Enquiry from marketing source {} already exists. Email = {}, Phone={}'.format(
                marketingSource,
                email,
                phoneNumber
            )
        )
