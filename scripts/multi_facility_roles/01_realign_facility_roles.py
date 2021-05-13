from apps.case.models import Case
from apps.servicing.models import Facility, FacilityRoles
from apps.lib.api_Salesforce import apiSalesforce
from apps.servicing.tasks import sfDetailSynch

sfAPI = apiSalesforce()
statusResult = sfAPI.openAPI(True)
sfListObj = sfAPI.getLoanObjList()['data']
loan_ids = list(sfListObj['Id'])

FacilityRoles.objects.filter(
    facility__sfID__in=loan_ids
).delete()

sfDetailSynch()