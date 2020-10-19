# Python Imports
import json
import base64

# Third-party Imports
from config.celery import app

# Local Application Imports

from apps.calculator.models import WebCalculator, WebContact
from apps.enquiry.models import Enquiry
from apps.lib.api_Wordpress import apiWordpress
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError, cleanPhoneNumber
from apps.lib.site_Enums import *

# TASKS

@app.task(name="Wordpress_Data")
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

            mapList = {'age1': 'age_1',
                       'age2': 'age_2',
                       'maxDrawdown': 'maxDrawdownAmount',
                       'mortgage': 'mortgageDebt',
                       'repayment': 'mortgageRepayment'}

            popList = ['id', 'retrieved', 'retrievedDate', 'timestamp', 'uuid', 'phone']

            sourceUID = item['uuid']

            srcData = item.copy()

            srcData['phoneNumber'] = cleanPhoneNumber(srcData['phone'])
            srcData['sourceID'] = sourceUID

            # map fields
            for key, value in mapList.items():
                srcData[value] = srcData[key]
                srcData.pop(key)

            # remove redundant fields
            for item in popList:
                srcData.pop(item)

            # convert empty strings to null
            for key, value in srcData.items():
                if value == "":
                    srcData[key] = None

            srcData['name'] = srcData['name'].title() if srcData['name'] else None

            write_applog("INFO", 'API', 'Tasks-getWordpressData', "Item data: " + json.dumps(srcData))

            # Create and save new WebCalculator object
            try:
                item_saved = False
                web_obj = WebCalculator.objects.create(**srcData)
                item_saved = True
            except:
                write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not save calculator entry")
                raise raiseTaskAdminError("Could not save calculator entry", json.dumps(srcData))

            if item_saved:
                # Mark items as retrieved on Wordpress
                result = wp.markCalculatorRetrieved(sourceUID)

                if result['status'] != 'Ok':
                    write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not mark retrieved")
                    raise raiseTaskAdminError("Could not mark calculator entry retrieved", json.dumps(srcData))

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

                mapList = {'age': 'age_1'}

                popList = ['id', 'retrieved', 'retrievedDate', 'timestamp', 'uuid', 'firstname',
                           'lastname', 'origin', 'resource']

                srcData['phone'] = cleanPhoneNumber(srcData['phone'])
                srcData['name'] = srcData['firstname'].title() if srcData['firstname'] else None
                if srcData['lastname']:
                    srcData['name'] += " " + srcData['lastname'].title() if srcData['firstname'] else ""
                srcData['sourceID'] = sourceUID

                # map fields
                for key, value in mapList.items():
                    srcData[value] = srcData[key]
                    srcData.pop(key)

                # remove redundant fields
                for item in popList:
                    srcData.pop(item)

                write_applog("INFO", 'API', 'Tasks-getWordpressData', "Item data: " + json.dumps(srcData))

                # Create and save new WebContact object
                try:
                    item_saved = False
                    web_obj = WebContact.objects.create(**srcData)
                    item_saved = True
                except:
                    write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not save contact entry")
                    raise raiseTaskAdminError("Could not save calculator entry", json.dumps(srcData))

            else:
                #Map website data to Enquiry

                mapList = {'age': 'age_1',
                           'uuid': 'referrerID'}

                popList = ['id', 'retrieved', 'retrievedDate', 'timestamp', 'firstname', 'lastname',
                           'origin', 'resource', 'phone', 'message']

                srcData['referrer'] = directTypesEnum.WEB_ENQUIRY.value
                srcData['enquiryStage'] = enquiryStagesEnum.BROCHURE_SENT.value
                srcData['phoneNumber'] = cleanPhoneNumber(srcData['phone'])
                srcData['name'] = srcData['firstname'].title() if srcData['firstname'] else None
                if srcData['lastname']:
                    srcData['name'] += " " + srcData['lastname'].title() if srcData['firstname'] else ""
                srcData['enquiryNotes'] = '[# Website Enquiry #]'
                srcData['enquiryNotes'] += '\r\n' + srcData['origin']
                srcData['referrerID'] = sourceUID

                # map fields
                for key, value in mapList.items():
                    srcData[value] = srcData[key]
                    srcData.pop(key)

                # remove redundant fields
                for item in popList:
                    srcData.pop(item)

                write_applog("INFO", 'API', 'Tasks-getWordpressData', "Item data: " + json.dumps(srcData))

                # Create and save new Enquiry object
                try:
                    item_saved = False
                    web_obj = Enquiry.objects.create(**srcData)
                    item_saved = True
                except:
                    write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not save contact entry")
                    raise raiseTaskAdminError("Could not save calculator entry", json.dumps(srcData))

            if item_saved:
                # Mark items as retrieved on Wordpress
                result = wp.markContactRetrieved(sourceUID)

                if result['status'] != 'Ok':
                    write_applog("ERROR", 'Api', 'Tasks-getWordpressData', "Could not mark retrieved")
                    raise raiseTaskAdminError("Could not mark contact entry retrieved", json.dumps(srcData))

    write_applog("INFO", 'API', 'Tasks-getWordpresData', 'Finishing Retrieving Data')
    return 'Task completed successfully'
