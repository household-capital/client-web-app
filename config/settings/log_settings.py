
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
            # 'class': 'logging.FileHandler',
            # 'filename': DEPLOYED_LOGGING+'/django.log',
        },
        'file-app': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            # 'class': 'logging.FileHandler',
            # 'filename': DEPLOYED_LOGGING + '/app.log',
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