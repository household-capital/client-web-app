

# Django Imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def firstNameSplit(str):

    if " " not in str:
        return str

    firstname, surname = str.split(" ", 1)
    if len(firstname) > 0:
        return firstname
    else:
        return str


class taskError():

    def raiseAdminError(self,title,body):
        msg_title="[Django] ERROR (Celery Task): "+ title
        from_email=settings.DEFAULT_FROM_EMAIL
        to=settings.ADMINS[0][1]
        msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
        msg.send()
        return


