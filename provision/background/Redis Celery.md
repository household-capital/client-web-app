This document details the initial set-up of a production instance of Redis and Celery. 

Redis is an in-memory key-value store (broker) known for its flexibility, performance, and wide language support.

Celery is a task queue that is built on an asynchronous message passing system. It can be used as a bucket where programming tasks can be dumped. The program that passed the task can continue to execute and function responsively, and then later on, it can poll celery to see if the computation is complete and retrieve the data.

### SECTION 1 - REDIS Install

```
sudo apt update
sudo apt install redis-server
```

Update configuration file to enable init to manage as a service 

```
sudo nano /etc/redis/redis.conf
```

Change the following:
```
supervised systemd
```

Test redis is working:
```
redis-cli
ping
```
This should produce PONG as output.

Check the port binding using:
```
sudo netstat -lnp | grep redis
```


### SECTION 2 - Celery Install (with extensions)
https://docs.celeryproject.org/en/latest/index.html

Install via pip:

```
pip install "celery[redis]"
pip install redis
pip install django-celery-beat
pip install django-celery-results
```

Update Django settings.py:

```
INSTALLED_APPS = [
    # third-party apps
    'django_celery_beat',
    'django_celery_results',
]

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
```

Note: CELERY_RESULT settings are because we are using django_celery_results
http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#django-celery-results-using-the-django-orm-cache-as-a-result-backend

Note: Full path was required to get task to wirte to the database
```
CELERY_RESULT_BACKEND_DB = 'postgresql+psycopg2://'+os.getenv("DATABASE_USER")+":"+os.getenv("DATABASE_PASSWORD")+"@localhost/"+os.getenv("DATABASE_NAME")
```

Create celery.py in the project root:

```
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'red.settings')

app = Celery('proj')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
```

Update project __init__ to make sure imported

```
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app  # noqa
```

Run migrations:

```
python manage.py makemigrations
python manage.py migrate
```

### SECTION 3 - Daemonise Celery

Create a new user named celery. 
Add to ww-data group to ensure file permissions (in particular, so .env can be called when running Django)

```
sudo useradd celery -d /home/celery -b /bin/bash
sudo adduser celery www-data
```

Create the log folders and set the right permissions. 
```
sudo mkdir /var/log/celery
sudo chown -R celery:django /var/log/celery
sudo chmod -R 755 /var/log/celery

```

Create the /etc/celery/celery.conf

```
# Name of nodes to start
# here we have a single node
CELERYD_NODES="worker1"
# or we could have three nodes:
#CELERYD_NODES="w1 w2 w3"

# Absolute or relative path to the 'celery' command:
#CELERY_BIN="/usr/local/bin/celery"
CELERY_BIN="/home/django/.virtualenvs/env/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="config"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# How to call manage.py
CELERYD_MULTI="multi"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=8"

# - %n will be replaced with the first part of the nodename.
# - %I will be replaced with the current child process index
#   and is important when using the prefork pool to avoid race conditions.
CELERYD_PID_DIR="/var/run/celery"
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_LOG_LEVEL="INFO"

# you may wish to add these options for Celery Beat
CELERYBEAT_PID_FILE="/var/run/celery/beat.pid"
CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"
```


Create /etc/systemd/system/celery.service
```
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=celery
Group=celery
EnvironmentFile=/etc/celery/celery.conf
# Run ExecStartPre with root-permissions
PermissionsStartOnly=true
ExecStartPre=-/bin/mkdir ${CELERYD_PID_DIR}
ExecStartPre=/bin/chown -R celery:celery ${CELERYD_PID_FILE}

#Run ExecStart with User=celery / Group=celery
WorkingDirectory=/home/django/django_project
ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PID_FILE}'
ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
TimeoutStopSec=2

[Install]
WantedBy=multi-user.target
```

Create /etc/systemd/system/celerybeat.service
```

[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=celery
Group=celery
EnvironmentFile=/etc/celery/celery.conf
# Run ExecStartPre with root-permissions
PermissionsStartOnly=true
ExecStartPre=-/bin/mkdir ${CELERYD_PID_DIR}
ExecStartPre=-/bin/chown -R celery:celery ${CELERYD_PID_DIR}

#Run ExecStart with User=celery / Group=celery
WorkingDirectory=/home/django/django_project
ExecStart=/bin/sh -c '${CELERY_BIN} beat  \
  -A ${CELERY_APP} \
  -l debug \
  --pidfile=${CELERYBEAT_PID_FILE} \
  --logfile=${CELERYBEAT_LOG_FILE} \
  --loglevel=${CELERYD_LOG_LEVEL}\
  --scheduler django_celery_beat.schedulers:DatabaseScheduler'
ExecStop=/bin/kill -s TERM $MAINPID
TimeoutStopSec=2

[Install]
WantedBy=multi-user.target

```
The default scheduler is the celery.beat.PersistentScheduler, that simply keeps track of the last run times in a local shelve database file.
There’s also the django-celery-beat extension that stores the schedule in the Django database, and presents a convenient admin interface to manage periodic tasks at runtime.
This app uses django-celery-beat hence the --scheduler inclusion above
http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#using-custom-scheduler-classes


Run systemctl daemon-reload in order that Systemd acknowledges that file. You should also run that command each time you modify it.
```
sudo systemctl daemon-reload
```

Enable the services to start on boot
```
systemctl enable celery.service
systemctl enable celerybeat.service
```