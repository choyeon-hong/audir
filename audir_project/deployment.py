import os 
from .settings import *
from .settings import BASE_DIR

SECRET_KEY = os.environ['SECRET']
WEBSITE_HOSTNAME = os.environ.get('WEBSITE_HOSTNAME', '')
DEBUG = False

ALLOWED_HOSTS = [WEBSITE_HOSTNAME] if WEBSITE_HOSTNAME else ['*']
CSRF_TRUSTED_ORIGINS = ['https://' + WEBSITE_HOSTNAME] if WEBSITE_HOSTNAME else []

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

conn_str = os.environ['AZURE_POSTGRESQL_CONNECTIONSTRING']
conn_str_dict = {}
for pair in conn_str.strip().split(' '):
    if '=' in pair:
        key, value = pair.split('=', 1)
        conn_str_dict[key] = value

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': conn_str_dict.get('dbname'),
        'HOST': conn_str_dict.get('host'),
        'USER': conn_str_dict.get('user'),
        'PASSWORD': conn_str_dict.get('password'),
        'PORT': conn_str_dict.get('port', '5432'),  
        'OPTIONS': {
            'sslmode': conn_str_dict.get('sslmode', 'require')
        }
    }
}