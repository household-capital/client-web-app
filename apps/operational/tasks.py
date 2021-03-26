import os

from datetime import timedelta
from django.utils import timezone as djtimezone
from django.core.files.storage import default_storage

from pytz import timezone
from apps.lib.site_Logging import write_applog
from apps.lib.api_Salesforce import apiSalesforce
from apps.lib.api_CloudWatch import CloudWatchWrapper
from config.celery import app

from apps.operational.utils import get_task_count, get_namespace
from apps.operational.decorators import email_admins_on_failure


def generic_stat_poll(task_name, delta):
    now_utc = djtimezone.now()
    # delta = timedelta(minutes=15)
    log_message = lambda message:  write_applog(
        "INFO", 
        'Operational', 'Tasks-CW_{}_stats'.format(task_name),  
        message
    )
    hour_ago = now_utc - delta
    log_message("Getting poll count from {} to {} [UTC]".format(hour_ago,now_utc))
    task_count =  get_task_count(task_name, now_utc, delta)
    log_message( "poll count {}".format(task_count))
    metric_namespace = get_namespace()
    log_message("poll namespace {}".format(metric_namespace))
    metric_name = task_name
    now_melb = now_utc.astimezone(timezone('Australia/Melbourne'))
    cw_wrapper = CloudWatchWrapper()
    log_message("Putting data to cloudwatch")
    cw_wrapper.put_metric_data(
        metric_namespace, 
        metric_name, 
        now_melb, 
        task_count,
        'Count'
    )

@app.task(name="CW_Wordpress_Data_stats")
@email_admins_on_failure(task_name="CW_Wordpress_Data_stats")
def cloud_watch_wordpress_poll_stats():
    # CW wordpress poll stats <- poll every 15minutes  
    # Run task every 15minutes
    generic_stat_poll(
        'Wordpress_Data',
        timedelta(minutes=15)
    )


@app.task(name="CW_Catchall_SF_Lead_stats")
@email_admins_on_failure(task_name="CW_Catchall_SF_Lead_stats")
def cloud_watch_sf_enquiry_sync():
    # CW Catchall_SF_Lead stats <- poll everyday at 4 AM
    # Run task always at 4 AM 
    generic_stat_poll(
        'Catchall_SF_Lead',
        timedelta(hours=2)
    )


@app.task(name="CW_Catchall_SF_Case_Lead_stats")
@email_admins_on_failure(task_name="CW_Catchall_SF_Case_Lead_stats")
def cloud_watch_sf_case_sync():
    # CW Catchall_SF_Lead stats <- poll everyday at 4 AM
    # Run task always at 4 AM 
    generic_stat_poll(
        'Catchall_SF_Case_Lead',
        timedelta(hours=2)
    )

def generic_file_uploader(doc_list, record_id): 
    """
        doc_list = {
            "Doc Title" : FileField
        }
    """
    sfAPI = apiSalesforce()
    result = sfAPI.openAPI(True)
    if result['status'] != "Ok":
        write_applog("ERROR", 'operational', 'Tasks-Generic File-upload', result['responseText'])
        return "Error - could not open Salesforce"
    for file_name, file_obj in doc_list.items():
        write_applog("ERROR", 'operational', 'Tasks-Generic File-upload', 'Attempting to sync {} on {}'.format(file_name, record_id))
        try:
            with default_storage.open(file_obj.name, "rb") as f:
                body = f.read()
            result = sfAPI.genericUploader(record_id, body, file_name)
            if result['status'] != 'Ok':
                write_applog("ERROR", 'operational', 'Tasks-Generic File-upload', result['responseText'])
                return "Error - Failed to upload docs"
        except FileNotFoundError:
            write_applog("ERROR", 'operational', 'Tasks-Generic File-upload', "Document Synch - " + file_name + "- file does not exist")
    return "Success"
