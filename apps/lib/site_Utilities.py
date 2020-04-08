

# Django Imports
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.urls import reverse_lazy

from apps.calculator.models import WebCalculator, WebContact
from apps.enquiry.models import Enquiry
from apps.servicing.models import FacilityEnquiry
from apps.case.models import Case


# CLASSES
class HouseholdLoginRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(HouseholdLoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

    # Ensures views will not render unless Household employee, redirects to Landing
    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.isHousehold:
            return super(HouseholdLoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))


class LoginOnlyRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginOnlyRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)


class ReferrerLoginRequiredMixin():
    # Ensures views will not render unless logged in, redirects to login page
    @classmethod
    def as_view(cls, **kwargs):
        view = super(ReferrerLoginRequiredMixin, cls).as_view(**kwargs)
        return login_required(view)

        # Ensures views will not render unless Household employee, redirects to Landing

    def dispatch(self, request, *args, **kwargs):
        if request.user.profile.referrer:
            return super(ReferrerLoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('landing:landing'))




class taskError():

    def raiseAdminError(self,title,body):
        msg_title="[Django] ERROR (Celery Task): "+ title
        from_email=settings.DEFAULT_FROM_EMAIL
        to=settings.ADMINS[0][1]
        msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
        msg.send()
        return



# FUNCTIONS

def updateNavQueue(request):
    request.session['webCalcQueue'] = WebCalculator.objects.queueCount()
    request.session['webContQueue'] = WebContact.objects.queueCount()
    request.session['enquiryQueue'] = Enquiry.objects.queueCount()
    request.session['loanEnquiryQueue'] = FacilityEnquiry.objects.queueCount()
    request.session['referrerQueue'] = Case.objects.referrerQueueCount()
    return

def firstNameSplit(str):

    if " " not in str:
        return str

    firstname, surname = str.split(" ", 1)
    if len(firstname) > 0:
        return firstname
    else:
        return str


def sendTemplateEmail(template_name, email_context, subject, from_email, to, cc= None, bcc = None ):
    text_content = "Email Message"
    html = get_template(template_name)
    html_content = html.render(email_context)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to=ensureList(to), bcc=ensureList(bcc),cc=ensureList(cc))
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
        return True
    except:
        return False

def ensureList(sourceItem):
    return [sourceItem] if type(sourceItem) is str else sourceItem


