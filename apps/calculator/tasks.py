# Python Imports
import json
import base64

# Third-party Imports
from config.celery import app
from django.core.serializers.json import DjangoJSONEncoder

# Local Application Imports

from apps.calculator.models import WebCalculator, WebContact
from apps.enquiry.models import Enquiry
from apps.lib.api_Wordpress import apiWordpress
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError, cleanPhoneNumber, parse_api_datetime, parse_api_names
from apps.lib.site_Enums import *
from .util import convert_calc, ProcessingError
from apps.case.assignment import find_auto_assignee

from apps.operational.decorators import email_admins_on_failure

# TASKS

@app.task(name="Wordpress_Data")
@email_admins_on_failure(task_name='Wordpress_Data')
def getWordpressData():
    ''' Task to retrieve calculator and contact data from Wordpress Website'''

    write_applog("INFO", 'API', 'Tasks-getWordpressData', 'Retrieving Wordpress Data')

    # Retrieve calculator data
    wp = apiWordpress()
    wp.openCalculatorAPI()
    result = wp.getCalculatorQueue()

    if result['status'] == "Ok":

        for item in result['data']['response']:
            #Map website data to WebCalculator

            sourceUID = item['uuid']

            mapList = {
                'age1': 'age_1',
                'age2': 'age_2',
                'maxDrawdown': 'maxDrawdownAmount',
                'mortgage': 'mortgageDebt',
                'repayment': 'mortgageRepayment',
                'origin': 'submissionOrigin',
                'uuid': 'origin_id',
            }

            popList = ['id', 'retrieved', 'retrievedDate', 'phone', 'contactDetails', 'isEnquiry', 'timestamp']

            srcData = item.copy()

            srcData['phoneNumber'] = cleanPhoneNumber(srcData['phone'])
            if srcData['timestamp']:
                srcData['origin_timestamp'] = parse_api_datetime(srcData['timestamp'])

            srcData['raw_name'] = srcData['firstname'] + ' ' + srcData['lastname']
            srcData['firstname'], srcData['lastname'], _ignore = parse_api_names(srcData['firstname'], srcData['lastname'])

            # map fields
            for key, value in mapList.items():
                if key in srcData:
                    srcData[value] = srcData[key]
                    srcData.pop(key)

            # remove redundant fields
            for item in popList:
                if item in srcData:
                    srcData.pop(item)

            # convert empty strings to null
            for key, value in srcData.items():
                if value == "":
                    srcData[key] = None

            if srcData.get('requestedCallback') is None:
                srcData['requestedCallback'] = False

            write_applog("INFO", 'API', 'Tasks-getWordpressData', "Item data: " + json.dumps(srcData, cls=DjangoJSONEncoder))

            # Create and save new WebCalculator object
            try:
                web_obj = WebCalculator.objects.create(**srcData)
            except BaseException as e:
                write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not save calculator entry")
                raiseTaskAdminError("Could not save calculator entry", json.dumps(srcData, cls=DjangoJSONEncoder))
                raise e

            # Mark items as retrieved on Wordpress
            # FIX ME - big here, because multiple calc entries use same source ID these days,
            # this can mark retrieved too soon. The ID needs to be changed to row specific!!
            result = wp.markCalculatorRetrieved(sourceUID)

            if result['status'] != 'Ok':
                write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not mark retrieved")
                raiseTaskAdminError("Could not mark calculator entry retrieved", json.dumps(srcData, cls=DjangoJSONEncoder))
                raise Exception('Could not mark calculator entry retrieved')

            proposed_owner = find_auto_assignee(
                referrer=directTypesEnum.WEB_CALCULATOR.value, email=web_obj.email, phoneNumber=web_obj.phoneNumber
            )
            if proposed_owner:
                try:
                    convert_calc(web_obj, proposed_owner)
                except ProcessingError as ex:
                    # try next lead
                    # get Jainish to help with a tech alert!
                    pass

    # Retrieve contact data
    wp = apiWordpress()
    wp.openContactAPI()
    result = wp.getContactQueue()

    if result['status'] == "Ok":
        for item in result['data']['response']:

            sourceUID = item['uuid']
            srcData = item.copy()

            if not srcData['origin']:
                srcData['origin'] = ''

            if 'Contact Us' in srcData['origin']:
                #Map website data to WebContact
                mapList = {
                    'age': 'age_1',
                    'origin': 'submissionOrigin',
                    'uuid': 'origin_id',
                }

                popList = ['id', 'retrieved', 'retrievedDate', 'timestamp', 'resource', 'description']

                srcData['phone'] = cleanPhoneNumber(srcData['phone'])
                if srcData['timestamp']:
                    srcData['origin_timestamp'] = parse_api_datetime(srcData['timestamp'])

                srcData['raw_name'] = srcData['firstname'] + ' ' + srcData['lastname']
                srcData['firstname'], srcData['lastname'], _ignore = parse_api_names(srcData['firstname'], srcData['lastname'])

                # map fields
                for key, value in mapList.items():
                    srcData[value] = srcData[key]
                    srcData.pop(key)

                # remove redundant fields
                for item in popList:
                    srcData.pop(item)

                write_applog("INFO", 'API', 'Tasks-getWordpressData', "Item data: " + json.dumps(srcData, cls=DjangoJSONEncoder))

                # Create and save new WebContact object
                try:
                    web_obj = WebContact.objects.create(**srcData)
                except:
                    write_applog("ERROR", 'Api', 'Tasks-getWordpressData', 'Could not save "contact us" entry')
                    raise raiseTaskAdminError('Could not save "contact us" entry', json.dumps(srcData, cls=DjangoJSONEncoder))

            else:
                #Map website data to Enquiry

                mapList = {
                    'age': 'age_1',
                    'origin': 'submissionOrigin',
                    'uuid': 'origin_id',
                }

                popList = ['id', 'retrieved', 'retrievedDate', 'timestamp',
                           'resource', 'phone', 'message', 'description']

                srcData['referrer'] = directTypesEnum.WEB_ENQUIRY.value
                srcData['enquiryStage'] = enquiryStagesEnum.BROCHURE_SENT.value
                srcData['phoneNumber'] = cleanPhoneNumber(srcData['phone'])
                if srcData['timestamp']:
                    srcData['origin_timestamp'] = parse_api_datetime(srcData['timestamp'])
                srcData['firstname'], srcData['lastname'], _ignore = parse_api_names(srcData['firstname'], srcData['lastname'])
                srcData['enquiryNotes'] = '[# Website Enquiry #]'
                srcData['enquiryNotes'] += '\r\n' + srcData['origin']
                if srcData.get('description') is not None:
                    srcData['enquiryNotes'] += '\r\n' + 'Description: {}'.format(srcData['description'])

                # map fields
                for key, value in mapList.items():
                    srcData[value] = srcData[key]
                    srcData.pop(key)

                # remove redundant fields
                for item in popList:
                    srcData.pop(item)

                write_applog("INFO", 'API', 'Tasks-getWordpressData', "Item data: " + json.dumps(srcData, cls=DjangoJSONEncoder))

                # Create and save new Enquiry object
                try:
                    web_obj = Enquiry.objects.create(**srcData)
                except:
                    write_applog("ERROR", 'Api', 'Tasks-getWordpressData', 'Could not save "web enquiry" entry')
                    raise raiseTaskAdminError('Could not save "web enquiry" entry', json.dumps(srcData, cls=DjangoJSONEncoder))

            # Mark items as retrieved on Wordpress
            result = wp.markContactRetrieved(sourceUID)

            if result['status'] != 'Ok':
                write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not mark retrieved")
                raise raiseTaskAdminError("Could not mark contact entry retrieved", json.dumps(srcData, cls=DjangoJSONEncoder))

    write_applog("INFO", 'API', 'Tasks-getWordpresData', 'Finishing Retrieving Data')
    return 'Task completed successfully'
