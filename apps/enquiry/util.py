from apps.lib.site_Enums import *
from apps.lib.site_Logging import write_applog
from apps.case.models import Case
from apps.case.assignment import auto_assign_leads
from .models import Enquiry
from apps.lib.site_Enums import caseStagesEnum


def assign_enquiry_leads(enquiries, force=False, notify=True):
    case_uids = set() 
    for enq in enquiries:
        case_uids |= {enq.case.caseUID}
    leads = list(Case.objects.filter(deleted_on__isnull=True, caseUID__in=case_uids))
    auto_assign_leads(leads, force=force, notify=notify)


def updateCreatePartnerEnquiry(payload, enquiries_to_assign):

    def should_lead_update(lead, new_enq):

        nonDirectTypes = [directTypesEnum.PARTNER.value, directTypesEnum.BROKER.value, directTypesEnum.ADVISER.value]

        if lead.caseStage in [
            caseStagesEnum.SALES_ACTIVE.value,
            caseStagesEnum.MEETING_HELD.value,
            caseStagesEnum.APPLICATION.value,
            caseStagesEnum.DOCUMENTATION.value,
            caseStagesEnum.APPLICATION.value,
            caseStagesEnum.FUNDED.value,
            caseStagesEnum.CLOSED.value,
        ]:
            write_applog(
                "INFO", 'Enquiry', 'EnquiryPartnerUpload',
                'Lead stage too late to allow a Lead update. Email = {}, Phone={}'.format(
                    new_enq.email,
                    new_enq.phoneNumber
                )
            )
            return False

        if lead.channelDetail == new_enq.marketingSource:
            write_applog(
                "INFO", 'Enquiry', 'EnquiryPartnerUpload',
                'Lead already set to desired marketing source ({}), so we will not update the lead. Email = {}, Phone={}'.format(
                    new_enq.marketingSource,
                    new_enq.email,
                    new_enq.phoneNumber
                )
            )
            return False

        if lead.referrer not in nonDirectTypes:
            write_applog(
                "INFO", 'Enquiry', 'EnquiryPartnerUpload',
                'Lead set to a direct lead source, so we will not update the lead. Email = {}, Phone={}'.format(
                    new_enq.email,
                    new_enq.phoneNumber
                )
            )
            return False

        return True


    write_applog("INFO", 'Enquiry', 'EnquiryPartnerUpload', 'Creating new enquiry')
    new_enq = Enquiry.objects.create(**payload)
    lead = new_enq.case

    if should_lead_update(lead, new_enq):
        # reset source info
        lead.referrer = new_enq.referrer
        lead.channelDetail = new_enq.marketingSource
        lead.marketing_campaign = new_enq.marketing_campaign

        # assign new owner
        enquiries_to_assign.append(new_enq)
