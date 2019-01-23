
# Logging Set-up

from .base_settings import *
LOG_ROOT = BASE_DIR + '/logs'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file-django': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_ROOT+'/django.log',
        },
        'file-app': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_ROOT + '/app.log',
        },
        'file-lib': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_ROOT + '/lib.log',
        }


    },
    'loggers': {
        'django': {
            'handlers': ['file-django'],
            'level': 'INFO',
            'propagate': True,
        },
        'myApps': {
            'handlers': ['file-app'],
            'level': 'INFO',
            'propagate': True,
        },
        'lib': {
            'handlers': ['file-lib'],
            'level': 'INFO',
            'propagate': True,
        }
    },
}