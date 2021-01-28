import os 

from datetime import timedelta
from django.utils import timezone as djtimezone
from pytz import timezone
from django_celery_results.models import TaskResult

def get_task_count(task_name, now_utc, offset): 
    return TaskResult.objects.filter(
        date_done__gte=now_utc-offset,
        date_done__lt=now_utc,
        task_name=task_name
    ).count()


def get_namespace():
    env = os.environ.get('ENV', 'local')
    return 'ClientApp-{}/PeriodicTasks'.format(env)
