import magic

# Django Imports
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from apps.lib.site_Utilities import ensureList


def sendTemplateEmail(template_name, email_context, subject, from_email, to, cc=None, bcc=None, attachments=None):
    text_content = "Email Message"
    html = get_template(template_name)
    html_content = html.render(email_context)
    bcc = ensureList(bcc) # retain legacy parsing to be safe.
         
    sunset_logging_email = "tech_alert+capp_email@householdcapital.com"

    bcc_list = []
    # bcc variable is only ever set in CAPP to 
    # be either 'None', or a single string of the owner's email.
    # acceptable values are: None, [], or ['email1', 'email2', ...]
    # ref: https://docs.djangoproject.com/en/4.0/_modules/django/core/mail/message/
    
    if bcc is None:
        bcc_list = ["tech_alert+capp_email@householdcapital.com"]

    if isinstance(bcc, str):
        bcc_list = [bcc, sunset_logging_email]

    if isinstance(bcc, list):
        bcc_list = bcc + [sunset_logging_email]

    msg = EmailMultiAlternatives(subject, text_content, from_email, to=ensureList(to), bcc=bcc_list,
                                 cc=ensureList(cc))
    msg.attach_alternative(html_content, "text/html")

    #Attached files (if present) - list of tuples (filename, file location)
    if attachments:
        for attachment in attachments:
            if len(attachment) == 3:
                msg = attachFile(msg, attachment[0], attachment[1], attachment[2])
            else:
                msg = attachFile(msg,attachment[0],attachment[1])
    try:
        msg.send()
        return True
    except:
        return False


def attachFile(msg, filename, fileLocation, isStatic=False):

    if isStatic:
        # is a static file
        localfile = staticfiles_storage.open(fileLocation, 'rb')
    else:
        #is a media file
        localfile = default_storage.open(fileLocation, 'rb')

    fileContents = localfile.read()
    mimeType = magic.from_buffer(fileContents,mime=True)
    msg.attach(filename, fileContents, mimeType)

    return msg
