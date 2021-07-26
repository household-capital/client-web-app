import magic, requests, os
import datetime
import backports.datetime_fromisoformat
backports.datetime_fromisoformat.MonkeyPatch.patch_fromisoformat()
import pytz

# Django Imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import is_naive
from urllib.parse import urljoin

from apps.lib.site_Enums import appTypesEnum

# UTILITY FUNCTIONS

def raiseAdminError(title, body):
    """Error raising utility"""
    msg_title = title
    from_email = settings.DEFAULT_FROM_EMAIL
    to = settings.ADMINS[0][1]
    msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
    msg.send()
    return


def raiseTaskAdminError(title, body, to=None):
    """Error raising utility for task errors"""
    msg_title = "[Django] ERROR (Celery Task): " + title
    from_email = settings.DEFAULT_FROM_EMAIL
    if to is None:
        to = settings.ADMINS[0][1]
    msg = EmailMultiAlternatives(msg_title, body, from_email, [to])
    msg.send()
    return


def firstNameSplit(str):
    if not str:
        return ''
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

def get_default_product_now():
    tz = pytz.timezone('Australia/Melbourne')
    now = datetime.datetime.now(tz)
    second_before_first_june = datetime.datetime(day=1, month=6, year=2021).replace(tzinfo=tz) - datetime.timedelta(seconds=1)
    return "HHC.RM.2021" if now > second_before_first_june else "HHC.RM.2018"

def calc_age(dob):
    return int((datetime.date.today() - dob).days / 365.25)

def serialise_payload(payload): 
    SERIALIZABLE_TYPES = [
        int,
        float,
        str,
        bool
    ]
    payload_type = type(payload)
    if payload_type in [list, tuple]:  
        return payload_type([
            serialise_payload(val)
            for val in payload
        ])
    if payload_type in [dict]:
        return {
            x: serialise_payload(y)
            for x,y in payload.items()
        } 
    return payload if (payload_type in SERIALIZABLE_TYPES or payload is None) else str(payload)


def loan_api_response(endpoint, payload, params={}, headers={}, return_raw_res_obj=False): 
    payload['is_variation'] = payload.get('appType') == appTypesEnum.VARIATION.value
    payload = serialise_payload(payload)

    res = requests.post(
        urljoin(
            os.environ.get('HHC_LOAN_API_ENDPOINT'),
            endpoint
        ),
        headers={
            'x-api-key': os.environ.get('HHC_ENDPOINT_API_KEY'),
            **headers

        },
        json=payload,
        params=params
    )
    if return_raw_res_obj: 
        return res
    if res.status_code != 200: 
        raise Exception(res.content)
    return res.json()

def loan_lixi_response(endpoint, payload, params={}, headers={}, return_raw_res_obj=False): 
    payload = serialise_payload(payload)
    
    res = requests.post(
        urljoin(
            os.environ.get('HHC_LIXI_ENDPOINT'),
            endpoint
        ),
        headers={
            'x-api-key': os.environ.get('HHC_LIXI_KEY'),
            **headers

        },
        json=payload,
        params=params
    )
    if return_raw_res_obj:
        return res
    if res.status_code != 200: 
        raise Exception(res.content)
    return res.json()

def generate_lixi(source_dict, schema_type='ACC'):
    response = loan_lixi_response(
        "/api/lixi/v1/generate/{}".format(schema_type),
        source_dict,
        return_raw_res_obj=True
    )
    returning_dict = {
        'XMLContent': None,
        'OutputLog': "",
        "ErrorTitle": "" 
    }
    status_code = response.status_code
    res_json = response.json()
    if status_code == 200: 
        returning_dict['XMLContent'] = res_json['responseText']
        returning_dict['OutputLog'] = res_json['responseLog']
    else: 
        if res_json.get('message') is None: 
            # raised 500 [handled]
            returning_dict['ErrorTitle'] = res_json['title']
            returning_dict['OutputLog'] = res_json['description']
        else:
            returning_dict['ErrorTitle'] = 'API Internal Server Error'
            returning_dict['OutputLog'] = res_json['message']
            # generic 500 [unhandled]

    return returning_dict


def validate_loan(source_dict, product_type="HHC.RM.2021"):
    source_dict['use_refer'] = 1
    response = loan_api_response(
        "/api/calc/v1/valid/loan",
        source_dict,
        {
            "product":product_type,
            "use_refer": 1
        },
        return_raw_res_obj=True
    )
    validation_result = {
        'data': {},
        'status': "Ok",
        'responseText':''
    }
    if response.status_code == 400: 
        validation_result['responseText'] = response.json()['description']
        validation_result['status'] = 'Error'
    elif response.status_code == 200: 
        validation_result['data'] = response.json()
    else: 
        validation_result['status'] = 'Error'
        validation_result['responseText'] = 'API server error. Please retry a update to hit validator API.'
    return validation_result


def get_loan_status(source_dict, product_type="HHC.RM.2021"):
    return {
        'data': loan_api_response(
            "/api/calc/v1/valid/status",
            source_dict, 
            {
                "product": product_type,
                "use_refer": 1
            }
        ),
        'status': 'Ok'
    }
