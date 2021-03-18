import magic
import datetime
import pytz

# Django Imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import is_naive

# UTILITY FUNCTIONS

def raiseAdminError(title, body):
    """Error raising utility"""
    msg_title = title
    from_email = settings.DEFAULT_FROM_EMAIL
    to = settings.ADMINS[0][1]
    msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
    msg.send()
    return


def raiseTaskAdminError(title, body):
    """Error raising utility for task errors"""
    msg_title = "[Django] ERROR (Celery Task): " + title
    from_email = settings.DEFAULT_FROM_EMAIL
    to = settings.ADMINS[0][1]
    msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
    msg.send()
    return


def firstNameSplit(str):
    if " " not in str:
        return str

    firstname, surname = str.split(" ", 1)
    if len(firstname) > 0:
        return firstname
    else:
        return str


def getFileFieldMimeType(fieldObj):

    if hasattr(fieldObj, 'temporary_file_path'):
        # file is temporary on the disk, so we can get full path of it
        mime_type = magic.from_file(fieldObj.temporary_file_path(), mime=True)
    else:
        # file is in memory
        mime_type = magic.from_buffer(fieldObj.read(), mime=True)

    return mime_type


def ensureList(sourceItem):
    return [sourceItem] if type(sourceItem) is str else sourceItem


def cleanPhoneNumber(phone):
    phone = str(phone) if phone is not None else None 
    if phone:
        number = phone.replace(" ", "").replace("(", "").replace(")", "").replace("+61", "0").replace("-", "")
        number = remove_prefix(number,"61")
        if number[0:1] != "0":
            return "0"+number
        else:
            return number


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        text = text.replace(prefix, "", 1)
    return text


def checkMobileNumber(number):
    result = cleanPhoneNumber(number)
    if len(result) != 10:
        return False
    if result[0:2] == "04":
        return True
    else:
        result = False


def chkNone(arg):
    return arg if arg else ''


def cleanValuation(valuation):
    if type(valuation) == str:
        val = valuation.replace("$", "").replace(",", "").replace("Million", "M"). \
            replace("m", "M").replace("k", "K").replace("M", "000000").replace("K", "000")
    else:
        val = valuation
    try:
        val = int(val)
        if val > 5000000:
            return None
        elif val < 1000:
            return val * 1000
        else:
            return val
    except:
        return None


def calcAge(DOBString, date_format='%m/%d/%Y'):
    if DOBString is None: 
        return 
    age = int((datetime.date.today() - datetime.datetime.strptime(DOBString, date_format).date()).days / 365.25)
    if age > 50 and age < 100:

        return age


def parse_api_datetime(dtstring):
    dt = datetime.datetime.fromisoformat(dtstring)
    if is_naive(dt):
        dt = pytz.utc.localize(dt)
    return dt


def split_name(name):
    firstname = ''
    surname = ''
    if name:
        if ' ' in name:
            firstname, surname = name.split(' ', 1)
        else:
            firstname = ''
            surname = name
    return firstname, surname


def parse_api_names(firstname, lastname):
    if firstname and lastname:
        name = "{} {}".format(firstname, lastname)
    else:
        # reduces to None if neither are present
        name = firstname or lastname

    name = name[:255] if name else None
    firstname = firstname[:40] if firstname else None
    lastname = lastname[:80] if lastname else None

    return firstname, lastname, name


def parse_api_name(name):
    firstname, lastname = split_name(name)
    return parse_api_names(firstname, lastname)


def join_name(firstname=None, middlename=None, lastname=None):
    return (firstname or '') + ((' ' + middlename) if middlename else '') + ((' ' + lastname) if lastname else '')
