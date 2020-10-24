
# Logging Set-up

from .base_settings import BASE_DIR
LOG_ROOT = BASE_DIR + '/logs'
DEPLOYED_LOGGING =  LOG_ROOT #"/opt/python/log"
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file-django': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'file-app': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },

        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file-django','mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'myApps': {
            'handlers': ['file-app'],
            'level': 'INFO',
            'propagate': True,
        },

    },
}

if os.getenv('ENV'): 
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file-django': {
                'class': 'logging.FileHandler',
                'filename': "/opt/python/log/django.log",
            },
            'file-app': {
                'class': 'logging.FileHandler',
                'filename': '/opt/python/log/app.log',
            },

            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
                'include_html': True,
            }
        },
        'loggers': {
            'django': {
                'handlers': ['file-django','mail_admins'],
                'level': 'INFO',
                'propagate': True,
            },
            'myApps': {
                'handlers': ['file-app'],
                'level': 'INFO',
                'propagate': True,
            },

        },
    }