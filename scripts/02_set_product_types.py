# current dummy script 
from apps.case.models import Case, Loan 
from apps.enquiry.models import Enquiry 

import pytz
import datetime
                             
# This migration is technically handled by 

tz = pytz.timezone('Australia/Melbourne')
now = datetime.datetime.now(tz)
second_before_first_june = datetime.datetime(day=1, month=6, year=2021).replace(tzinfo=tz) - datetime.timedelta(seconds=1)


# set all leads with un-set meeting dates as 2021 product
case_id_new_product_type = Case.objects.filter(
    meetingDate__isnull=True
).exclude(deleted_on__isnull=False).values_list('id', flat=True)

case_id_old_product_type = Case.objects.exclude(
    meetingDate__isnull=True
).values_list('id', flat=True)

Loan.objects.filter(
    case_id__in=case_id_new_product_type
).update(product_type="HHC.RM.2021")

Loan.objects.filter(
    case_id__in=case_id_old_product_type
).update(product_type="HHC.RM.2018")

Enquiry.objects.filter(
    timestamp__lte=second_before_first_june
).update(product_type="HHC.RM.2018")

Enquiry.objects.filter(
    timestamp__gt=second_before_first_june
).update(product_type="HHC.RM.2021")