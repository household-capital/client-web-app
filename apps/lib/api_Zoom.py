# Python Imports
import os
import json
import jwt
import requests
from datetime import datetime, timedelta


# Application Imports

class apiZoom():
    """Zoom API Wrapper"""

    api_key = os.getenv("ZOOM_KEY")
    api_secret = os.getenv("ZOOM_SECRET")

    api_url_base = 'https://api.zoom.us'
    api_url_user_list = '/v2/users/'
    api_url_rec_list = '/v2/users/{0}/recordings'
    api_url_create = '/v2/users/{0}/meetings'
    api_url_delete = '/v2/meetings/{0}'

    user_list = []
    token = ""
    headers = {}

    def __init__(self):

        key_expiry = datetime.utcnow() + timedelta(minutes=90)
        key_payload = {
            "aud": None,
            "iss": self.api_key,
            "exp": key_expiry,
            "iat": datetime.utcnow()
        }

        self.token = jwt.encode(key_payload, self.api_secret, algorithm='HS256').decode("UTF-8")

        self.headers = {
            'authorization': "Bearer " + self.token
            , 'content-type': "application/json"}

    def get_users(self):
        self.user_list.clear()

        response = requests.get(self.api_url_base + self.api_url_user_list, headers=self.headers)

        if response.status_code == 200:
            response_dict = json.loads(response.text)
            user_data = response_dict["users"]
            for user in user_data:
                self.user_list.append(
                    {"user": user["last_name"],
                     "id": user["id"]}
                )

            return {"status": "Ok", "data": self.user_list}

        else:
            return {"status": "Error"}

    def get_recording_list(self, userID):
        meeting_list = []

        user_url = self.api_url_rec_list.format(userID)

        response = requests.get(self.api_url_base + user_url, headers=self.headers)

        if response.status_code == 200:
            response_dict = json.loads(response.text)
            meeting_data = response_dict["meetings"]

            for meeting in meeting_data:
                meeting_list.append(
                    {"meeting_date": meeting["start_time"],
                     "audio": meeting["recording_files"][0]['download_url'],
                     "video": meeting["recording_files"][1]['download_url']})

            return {"status": "Ok", "data": meeting_list}

        else:
            return {"status": "Error"}


    def create_meeting(self, userID, meetingName, description, startTime, timeZone, trackingFields, use_pmi=True):

        create_url = self.api_url_create.format(userID)

        data = {
            "topic": meetingName + " - " + description,
            "type": 2,
            "start_time": startTime,
            "duration": 75,
            "timezone": timeZone,
            "settings": {
                "use_pmi": use_pmi,
            },
            "tracking_fields": trackingFields
            ,
        }

        response = requests.post(self.api_url_base + create_url, headers=self.headers,
                                 data=json.dumps(data))

        if response.status_code == 201:
            return {"status": "Ok", "responseText": response.text}
        else:
            return {"status": "Error", "responseText": response.text}


    def delete_meeting(self, meetingID):

        delete_url = self.api_url_delete.format(meetingID)

        response = requests.delete(self.api_url_base + delete_url, headers=self.headers)

        if response.status_code == 204:
            return {"status": "Ok", "responseText":response.text}

        else:
            return {"status": "Error", "responseText":response.text}

