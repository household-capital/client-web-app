"""
Django settings for household project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_PATH=BASE_DIR+'/templates/'

# Project Settings
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Application definition

INSTALLED_APPS = [
    # django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party apps
    'crispy_forms',
    'rest_framework',
    'django_celery_beat',
    'django_celery_results',
    'storages',
    'corsheaders',
    # my apps
    'apps.accounts',
    'apps.application',
    'apps.calculator',
    'apps.calendly',
    'apps.case',
    'apps.client_2_0',
    'apps.enquiry',
    'apps.fact_find',
    'apps.landing',
    'apps.servicing',
    'apps.referrer',
    'apps.site_tags',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_PATH],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/collected/' #'/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR + '/static/collected'
MEDIA_ROOT = BASE_DIR + '/static/media'
STATICFILES_DIRS = (BASE_DIR + '/static/uncollected',)
FILE_UPLOAD_PERMISSIONS = 0o644


WSGI_APPLICATION = 'config.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Australia/Melbourne'
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR=True
THOUSAND_SEPARATOR = ','


DATE_INPUT_FORMATS = (
    '%Y-%m-%d',     # '2013-03-21'
    '%d/%m/%Y',     # '21/03/2014'
)
TIME_INPUT_FORMATS = (
    '%I:%M %p',     # ' 5:59 PM'
    '%H:%M:%S',     # '17:59:59'
    '%H:%M',        # '17:59'
)
DATETIME_INPUT_FORMATS = (
    '%Y-%m-%d %H:%M',     # '2013-03-21 17:59'
    '%Y-%m-%d %I:%M %p',  # '2013-03-21 5:59 PM'
    '%d/%m/%Y %I:%M %p',  # '21/03/2014 5:59 PM'
    '%d/%m/%Y %H:%M',     # '21/03/2014 17:59'
)

SHORT_DATETIME_FORMAT = 'd M y, h:i A'   # 21 Mar 14, 5:59 PM


# Third-party App Settings
CRISPY_TEMPLATE_PACK = 'bootstrap4'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_BROKER_URL = 'redis://{}'.format(os.environ.get('REDIS_ENDPOINT', 'localhost:6360'))
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False

CORS_ALLOWED_ORIGINS = [
    "https://householdcapital.app",
    "https://www.householdcapital.app",
    "https://householdcapital.com.au",
    "https://www.householdcapital.com.au",
    os.getenv("SITE_URL")
]

# Default URLS
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/landing/'
