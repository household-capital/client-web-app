

# Django Imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


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


class taskError():

    def raiseAdminError(self,title,body):
        msg_title="[Django] ERROR (Celery Task): "+ title
        from_email=settings.DEFAULT_FROM_EMAIL
        to=settings.ADMINS[0][1]
        msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
        msg.send()
        return