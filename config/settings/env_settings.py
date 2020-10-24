import os
import boto3

from io import StringIO
from os.path import join, dirname
from dotenv import load_dotenv
from config.utils import get_setting

import requests 

# Environment Variables are saved as strings!
def boolStr(str):
    strTrue=["1","True","true","TRUE"]
    if str == None:
        return False
    if str in strTrue:
        return True
    else:
        return False

def intNone(str):
    if str == None or str == 'XXXXXXXX':
        return 0
    else:
        return int(str)

ALLOWED_HOSTS = [os.getenv("ALLOWED_HOSTS_1"),
                 os.getenv("ALLOWED_HOSTS_2"),
                 os.getenv("ALLOWED_HOSTS_3"),
                 os.getenv("ALLOWED_HOSTS_4")]


SITE_URL = os.getenv("SITE_URL")

if os.environ.get('ENV') == 'prod': 
    ALLOWED_HOSTS += [
        '.householdcapital.app', 
        '.householdcapital.com.au'
    ]

if SITE_URL is not None: 
    ip = requests.get('http://ipinfo.io/json').json()['ip']
    ALLOWED_HOSTS += [ip]

#Email Settings
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_MAIN=os.getenv("EMAIL_MAIN")
EMAIL_PORT = intNone(os.getenv("INT_EMAIL_PORT"))
EMAIL_USE_TLS = boolStr(os.getenv("BOOL_EMAIL_USE_TLS"))
DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL")
SERVER_EMAIL=os.getenv("SERVER_EMAIL")

#Admin Settings
ADMINS=[(os.getenv("ADMIN_NAME"),os.getenv("ADMIN_EMAIL"))]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")


CORS_ALLOWED_ORIGINS = [
    "https://householdcapital.app",
    "https://www.householdcapital.app",
    "https://householdcapital.com.au",
    "https://www.householdcapital.com.au",
]

if os.getenv("SITE_URL") is not None: 
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS + [os.getenv("SITE_URL")]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
if os.environ.get('ENV') and os.getenv('STORAGE') == "AWS": 
    DEBUG = boolStr(os.getenv("BOOL_DEBUG"))


# DATABASE

if os.getenv('STORAGE') == "AWS":

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DATABASE'],
            'USER':  get_setting('Username'),
            'PASSWORD': get_setting('Password'),
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
    CELERY_RESULT_BACKEND_DB = ''.join(['postgresql+psycopg2://',
                                        get_setting('Username'),
                                        ":",
                                        get_setting('Password'),
                                        os.environ['RDS_HOSTNAME'],
                                        os.environ['RDS_DATABASE']])
else:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.getenv("DATABASE_NAME"),
            'USER': os.getenv("DATABASE_USER"),
            'PASSWORD': os.getenv("DATABASE_PASSWORD"),
            'HOST': 'localhost',
            'PORT': '',
        }
    }

    CELERY_RESULT_BACKEND_DB = ''.join(['postgresql+psycopg2://',
                                       os.getenv("DATABASE_USER"),
                                       ":",
                                       os.getenv("DATABASE_PASSWORD"),
                                       "@localhost/",
                                       os.getenv("DATABASE_NAME")])


# STORAGE
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.getenv('STORAGE') == "AWS":

    #Digital Ocean Storage Settings
    # AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    # AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    #AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')

    AWS_STORAGE_BUCKET_NAME = os.getenv('S3_BUCKET_STATIC')

    AWS_S3_REGION_NAME = 'ap-southeast-2' #os.getenv('AWS_S3_REGION_NAME')
    # AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400',}
    AWS_STATIC_LOCATION = 'static'
    AWS_MEDIA_LOCATION = 'media'
    
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3-{AWS_S3_REGION_NAME}.amazonaws.com'
    AWS_DEFAULT_ACL = None
    
    #Django Storages
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static/uncollected'),]
    STATIC_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_STATIC_LOCATION)
    MEDIA_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_MEDIA_LOCATION)
    STATICFILES_STORAGE = 'config.settings.ext_storage.StaticStorage'    # Static Root
    DEFAULT_FILE_STORAGE = 'config.settings.ext_storage.MediaStorage'   # Media Root

    FILE_UPLOAD_PERMISSIONS = 0o644

else:
    
    STATIC_URL = '/static/collected/' #'/static/'
    MEDIA_URL = '/media/'
    STATIC_ROOT = BASE_DIR + '/static/collected'
    MEDIA_ROOT = BASE_DIR + '/static/media'
    STATICFILES_DIRS = (BASE_DIR + '/static/uncollected',)
    FILE_UPLOAD_PERMISSIONS = 0o644


    # LOCAL storage
    # https://docs.djangoproject.com/en/1.11/howto/static-files/
    
    # STATIC_URL = SITE_URL + '/static/'
    # MEDIA_URL = SITE_URL + '/media/'
    # STATIC_ROOT = BASE_DIR + '/static/collected'
    # MEDIA_ROOT = BASE_DIR + '/static/media'
    # STATICFILES_DIRS = (BASE_DIR + '/static/uncollected',)
    # FILE_UPLOAD_PERMISSIONS = 0o644


# SESSION EXPIRY TIME: in seconds
SESSION_COOKIE_AGE = 172800

# HTTPS Browser Protection - only use if https access only
SECURE_HSTS_SECONDS = intNone(os.getenv('INT_SECURE_HSTS_SECONDS'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = boolStr(os.getenv('BOOL_SECURE_HSTS_INCLUDE_SUBDOMAINS'))
SECURE_CONTENT_TYPE_NOSNIFF = boolStr(os.getenv('BOOL_SECURE_CONTENT_TYPE_NOSNIFF'))
SECURE_BROWSER_XSS_FILTER=boolStr(os.getenv('BOOL_SECURE_BROWSER_XSS_FILTER'))
SECURE_SSL_REDIRECT=boolStr(os.getenv('BOOL_SECURE_SSL_REDIRECT'))
SESSION_COOKIE_SECURE=boolStr(os.getenv('BOOL_SESSION_COOKIE_SECURE'))
CSRF_COOKIE_SECURE=boolStr(os.getenv('BOOL_CSRF_COOKIE_SECURE'))
SECURE_HSTS_PRELOAD=boolStr(os.getenv('BOOL_SECURE_HSTS_PRELOAD'))












