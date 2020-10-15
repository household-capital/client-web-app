import os

from datetime import timedelta
from celery.schedules import crontab, schedule

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
            'task': 'SF_Refer_Postcode', # custom task (?)
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
            'schedule': schedule(run_every=timedelta(hours=1))
        },
        'Website Poll':{
            'task': 'Wordpress_Data', # custom task (?)
            'schedule': schedule(run_every=timedelta(minutes=15))
        },
        'EnquiryFollowupEmail':{
            'task': 'EnquiryFollowUp', # custom task (?)
            'schedule': crontab(hour=7, minute=30)
        },
        'Case SF Catchall - Nightly':{
            'task': 'Catchall_SF_Case_Lead', # custom task (?)
            'schedule': crontab(hour=2, minute=0)
        },
        'Enquiry SF Catchall - Nightly':{
            'task': 'Catchall_SF_Lead', # custom task (?)
            'schedule': crontab(hour=2, minute=0)
        },
        'Enquiry SF Catchall - Nightly':{
            'task': 'AMAL_Funded_Data', # custom task (?)
            'schedule': crontab(hour=3, minute=0)
        }
    }