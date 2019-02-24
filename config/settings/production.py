

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3059be9d2454b6eeb5a690f02dad4782'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django',
        'USER': 'django',
        'PASSWORD': 'ksudfhs92834498234uyksueh',
        'HOST': 'localhost',
        'PORT': '',
    }
}

SITE_URL = 'https://www.householdcapital.app'