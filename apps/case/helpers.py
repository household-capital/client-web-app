from apps.case.models import Case
from apps.lib.site_Enums import caseStagesEnum

def should_lead_owner_update(lead): 
    if lead.owner: 
        if lead.caseStage in [
            caseStagesEnum.SALES_ACTIVE.value,
            caseStagesEnum.MEETING_HELD.value,
            caseStagesEnum.APPLICATION.value,
            caseStagesEnum.DOCUMENTATION.value,
            caseStagesEnum.APPLICATION.value,
            caseStagesEnum.FUNDED.value,
            caseStagesEnum.CLOSED.value,
        ]:
            return False
        latest_enq = lead.enquiries.latest('timestamp')
        if lead.channelDetail == latest_enq.marketingSource: 
            return False
    return True
