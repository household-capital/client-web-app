# Python Imports
import json
import base64

# Third-party Imports
from config.celery import app

# Local Application Imports

from apps.calculator.models import WebCalculator, WebContact
from apps.enquiry.models import Enquiry
from apps.lib.api_Website import apiWebsite
from apps.lib.api_Wordpress import apiWordpress
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError, cleanPhoneNumber
from apps.lib.site_Enums import *

# TASKS

@app.task(name="Website_Data")
def getWebsiteData():
    ''' Task to retrieve calculator and contact data from Wagtail Website'''

    write_applog("INFO", 'API', 'Tasks-getWebsiteData', 'Retrieving Website Data')

    webAPI = apiWebsite()
    result = webAPI.openAPI()

    # Open API
    if result['status'] != 'Ok':
        write_applog("ERROR", 'API', 'Tasks-getWebsiteData', "Could not open API")
        return "Finished - Unsuccessfully"

    # Get calculator queue
    result = webAPI.getCalculatorQueue()
    if result['status'] != 'Ok':
        write_applog("ERROR", 'API', 'Tasks-getWebsiteData', result['responseText'])
        return "Finished - Unsuccessfully"

    if result['data'][0]['queue'] > 0:
        for item in result['data'][1]['data']:

            # remove redundant fields
            sourceUID = item['calcUID']

            srcData = item.copy()

            srcData.pop('calcUID')
            srcData.pop('retrieved')
            srcData.pop('retrievedDate')
            srcData.pop('timestamp')
            srcData.pop('updated')
            srcData['name'] = srcData['name'].title() if srcData['name'] else None

            write_applog("INFO", 'API', 'Tasks-getWebsiteData', "Item data: " + json.dumps(srcData))

            # Create and save new local calculator object
            try:
                web_obj = WebCalculator.objects.create(**srcData)
            except:
                write_applog("ERROR", 'Api', 'Tasks-getWebsiteData', "Could not save calculator entry")
                raise raiseTaskAdminError("Could not save calculator entry", json.dumps(srcData))

            result = webAPI.markCalculatorRetrieved(sourceUID)

            if result['status'] != 'Ok':
                write_applog("ERROR", 'Api', 'Tasks-getWebsiteData', "Could not mark retrieved")
                raise raiseTaskAdminError("Could not mark calculator entry retrieved", json.dumps(srcData))

    # Get contact queue
    result = webAPI.getContactQueue()
    if result['status'] != 'Ok':
        write_applog("ERROR", 'API', 'Tasks-getWebsiteData', result['responseText'])
        return "Finished - Unsuccessfully"

    if result['data'][0]['queue'] > 0:
        for item in result['data'][1]['data']:

            # remove redundant fields
            sourceUID = item['contUID']

            srcData = item.copy()

            srcData.pop('contUID')
            srcData.pop('retrieved')
            srcData.pop('retrievedDate')
            srcData.pop('timestamp')
            srcData.pop('updated')
            srcData['name'] = srcData['name'].title() if srcData['name'] else None

            # Create and save new local calculator object
            try:
                web_obj = WebContact.objects.create(**srcData)
            except:
                write_applog("ERROR", 'Api', 'Tasks-getWebsiteData', "Could not save contact entry")
                raise raiseTaskAdminError("Could not save contact entry", json.dumps(srcData))

            result = webAPI.markContactRetrieved(sourceUID)

            if result['status'] != 'Ok':
                write_applog("ERROR", 'Api', 'Tasks-getWebsiteData', "Could not mark contact retrieved")
                raise raiseTaskAdminError("Could not mark contact entry retrieved", json.dumps(srcData))

    write_applog("INFO", 'API', 'Tasks-getWebsiteData', 'Finishing Retrieving Data')
    return 'Task completed successfully'



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
                       'maxDrawdown': 'maxDrawdownAmount'}

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

            srcData['name'] = srcData['name'].title() if srcData['name'] else None
            print(srcData)

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

                web_obj = Enquiry.objects.create(**srcData)

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
