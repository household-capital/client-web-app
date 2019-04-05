import os

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
    if str == None:
        return 0
    else:
        return int(str)

ALLOWED_HOSTS = [os.getenv("ALLOWED_HOSTS_1"),os.getenv("ALLOWED_HOSTS_2"),os.getenv("ALLOWED_HOSTS_3")]

SITE_URL = os.getenv("SITE_URL")

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

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = boolStr(os.getenv("BOOL_DEBUG"))

# Database

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

# HTTPS Browser Protection - only use if https access only
SECURE_HSTS_SECONDS = intNone(os.getenv('INT_SECURE_HSTS_SECONDS'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = boolStr(os.getenv('BOOL_SECURE_HSTS_INCLUDE_SUBDOMAINS'))
SECURE_CONTENT_TYPE_NOSNIFF = boolStr(os.getenv('BOOL_SECURE_CONTENT_TYPE_NOSNIFF'))
SECURE_BROWSER_XSS_FILTER=boolStr(os.getenv('BOOL_SECURE_BROWSER_XSS_FILTER'))
SECURE_SSL_REDIRECT=boolStr(os.getenv('BOOL_SECURE_SSL_REDIRECT'))
SESSION_COOKIE_SECURE=boolStr(os.getenv('BOOL_SESSION_COOKIE_SECURE'))
CSRF_COOKIE_SECURE=boolStr(os.getenv('BOOL_CSRF_COOKIE_SECURE'))
SECURE_HSTS_PRELOAD=boolStr(os.getenv('BOOL_SECURE_HSTS_PRELOAD'))













