# current dummy script 
from apps.case.models import Case, Loan 
from apps.enquiry.models import Enquiry 

import pytz
import datetime
                             
# This migration is technically handled by 

tz = pytz.timezone('Australia/Melbourne')
now = datetime.datetime.now(tz)
second_before_first_june = datetime.datetime(day=1, month=6, year=2021).replace(tzinfo=tz) - datetime.timedelta(seconds=1)


#Case.objects.filter(
#).exclude(deleted_on__isnull=False)
Loan.objects.update(product_type="HHC.RM.2018")

