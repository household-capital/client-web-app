# Python Imports
import json
import base64

# Third-party Imports
from config.celery import app

# Local Application Imports

from apps.calculator.models import WebCalculator, WebContact
from apps.lib.api_Website import apiWebsite
from apps.lib.site_Logging import write_applog
from apps.lib.site_Utilities import raiseTaskAdminError


# TASKS

@app.task(name="Website_Data")
def getWebsiteData():
    ''' Task to retrieve calculator and contact data from Website'''

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

            write_applog("INFO", 'API', 'Tasks-getWebsiteData', "Item data: "+json.dumps(srcData))

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
