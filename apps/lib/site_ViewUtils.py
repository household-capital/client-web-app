
from apps.calculator.models import WebCalculator, WebContact
from apps.case.models import Case
from apps.enquiry.models import Enquiry

from apps.servicing.models import FacilityEnquiry, Facility


def updateNavQueue(request):
    """Update queue badges in the menu bar"""
    request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
    request.session['webContQueue'] = WebContact.objects.queueCount()
    request.session['enquiryQueue'] = Enquiry.objects.queueCount()
    request.session['loanEnquiryQueue'] = FacilityEnquiry.objects.queueCount()
    request.session['referrerQueue'] = Case.objects.queueCount()

    # Servicing
    recItems = Facility.objects.filter(amalReconciliation=False, settlementDate__isnull=False).count()
    breachItems = Facility.objects.filter(amalBreach=True, settlementDate__isnull=False).count()
    enquiryItems = FacilityEnquiry.objects.filter(actioned=False).count()

    request.session['servicingQueue'] = max(recItems,enquiryItems, breachItems)

    return
