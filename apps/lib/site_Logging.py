import csv
import logging
from datetime import datetime

from django.conf import settings

logger = logging.getLogger('myApps')


def write_applog(log_level, log_module, log_function, log_message):
    log_entry = str(datetime.now()) + "|" + log_level + "|" + log_module + "|" + log_function + "|" + log_message

    if log_level=="INFO":
        logger.info(log_entry)
    elif log_level=="ERROR":
        logger.info(log_entry)

