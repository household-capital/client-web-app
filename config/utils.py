import os
import boto3
import base64
import json

from datetime import timedelta
from celery.schedules import crontab, schedule

from botocore.exceptions import ClientError

def get_celery_beat_config():
    env = os.environ.get('ENV')
    if env is None: 
        return {}
    return {
        'SF Annual Review Notification Nightly': {
            'task': 'Annual_Review_Notification',
            'schedule': crontab(hour=7, minute=30)
        },
        'Calendly Synch': {
            'task': 'Synch_Calendly_Discovery', # custom task (?)
            'schedule': crontab(hour=1)
        },
        'Application Follow Up - Nightly': {
            'task': 'ApplicationFollowUp', # custom task (?)
            'schedule': crontab(hour=7, minute=30)
        },
        'SF Refer Postcode': {
            'task': 'SF_Refer_Postcode_Lead', # custom task (?)
            'schedule': crontab(hour=1)
        },
        'Clear_Session': {
            'task': 'Clear_Session_Data', # custom task (?)
            'schedule': crontab(hour=5, minute=0)
        },
        'SF_AMAL_SYNCH': {
            'task': 'SF_AMAL_Synch', # custom task (?)
            'schedule': crontab(hour=6, minute=0)
        },
        'SF Detailed Synch': {
            'task': 'Servicing_Detail_Synch', # custom task (?)
            'schedule': crontab(hour=4, minute=0)
        },
        # 'Funded Data (Balances Only)': {                        # NOT ENABLED (?)
        #     'task': 'AMAL_Funded_Data', # custom task (?)
        #     'schedule': schedule(run_every=timedelta(days=14))
        # },
        'Servicing Synch - Hourly': {
            'task': 'Servicing_Synch', # custom task (?)
            'schedule': schedule(run_every=timedelta(hours=1))
        },
        'SF Integrity - Nightly':{
            'task': 'SF_Integrity_Check', # custom task (?)
            'schedule': crontab(hour=2, minute=30)
        },
        'SF Stage - Hourly':{
            'task': 'SF_Stage_Synch', # custom task (?)
            'schedule': crontab(minute=0, hour='*/2,7-19')
        },
        'Website Poll':{
            'task': 'Wordpress_Data', # custom task (?)
            'schedule': schedule(run_every=timedelta(minutes=5))
        },
        'LeadFollowUpEmail':{
            'task': 'LeadFollowUp', # custom task (?)
            'schedule': crontab(hour=7, minute=30)
        },
        'Case SF Catchall - Nightly':{
            'task': 'Catchall_SF_Case_Lead', # custom task (?)
            'schedule': crontab(hour=2, minute=0)
        },
        'AMAL_FUNDED_DATA - Nightly':{
            'task': 'AMAL_Funded_Data', # custom task (?)
            'schedule': crontab(hour=3, minute=0)
        },
        # The following tasks are cloudwatch tasks 
        'CloudWatch_Task_Poll_Wordpress_Data': {
            'task': 'CW_Wordpress_Data_stats',
            'schedule': schedule(run_every=timedelta(minutes=5))
        },
        'CloudWatch_Task_Poll_Catchall_SF_Case_Lead': {
            'task': 'CW_Catchall_SF_Case_Lead_stats',
            'schedule': crontab(hour=4, minute=0)
        },

        'Hard_delete_enquiries': {
            'task': 'Hard_delete_enquiries',
            'schedule': crontab(hour=0, minute=0)
        },
        'Hard_delete_leads': {
            'task': 'Hard_delete_leads',
            'schedule': crontab(hour=0, minute=15)
        },

    }

def secrets_manager_client(region_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    return client

def get_secret(secret_name):
    region_name = "ap-southeast-2"
    client = secrets_manager_client(region_name)

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])

        return secret

def get_settings(secret_type='db-cred'):
    secret_json = get_secret('{env}/clientapp/{secret_type}'.format(
            env=os.environ.get('ENV', 'local'),
            secret_type=secret_type
        )
    )
    return json.loads(secret_json)


def get_setting(setting, secret_type='db-cred'): 
    return get_settings(secret_type)[setting]

def set_settings(key, value, secret_type='db-cred'): 
    secret_name = '{env}/clientapp/{secret_type}'.format(env=os.environ.get('ENV', 'local'), secret_type=secret_type)
    region_name = "ap-southeast-2"
    secret_value = get_settings(secret_type)
    secret_value[key] = value
    
    client = secrets_manager_client(region_name)
    client.update_secret(
        SecretId=secret_name, 
        SecretString=json.dumps(secret_value)
    )

