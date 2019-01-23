

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z3p=1h8)he#f3uitbl*rtmg@=cdr&y-yw$d*n06mm$5yjx-yf2'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hhc',
        'USER': 'hhcadminuser',
        'PASSWORD': 'Burlington3166',
        'HOST': 'localhost',
        'PORT': '',
    }
}
