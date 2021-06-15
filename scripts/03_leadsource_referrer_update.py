from django.db.models import OuterRef, Subquery, Count, F
from apps.enquiry.models import Enquiry 
from apps.case.models import Case


referrers = Enquiry.objects.filter(
    case__caseUID=OuterRef('caseUID')
).order_by('timestamp').values_list('referrer', flat=True)
Case.objects.annotate(
    enq_count=Count('enquiries'),
    fenq_referrer=Subquery(referrers[:1])
).filter(
    enq_count__gte=2
).update(
    referrer=F('fenq_referrer')
)