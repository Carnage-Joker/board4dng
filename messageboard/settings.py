import json
import base64
import os

import django_heroku
import firebase_admin
from decouple import config
from firebase_admin import credentials

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "board",
    "whitenoise.runserver_nostatic",
    "pwa",
    'widget_tweaks',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Place whitenoise middleware correctly
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "messageboard.urls"
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # If you have custom templates, define the path here
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

FIREBASE_PRIVATE_KEY = config('FIREBASE_PRIVATE_KEY', default='')

if FIREBASE_PRIVATE_KEY:
    # Decode Firebase private key (base64 or direct JSON)
    try:
        cred_data = base64.b64decode(FIREBASE_PRIVATE_KEY).decode('utf-8')
        cred = credentials.Certificate(json.loads(cred_data))
    except:
        # In case the key is already in JSON format (not base64-encoded)
        cred = credentials.Certificate(json.loads(FIREBASE_PRIVATE_KEY))

    firebase_admin.initialize_app(cred)

# FCM Server Key (also stored in the environment)
FCM_SERVER_KEY = config('FCM_SERVER_KEY', default='')

WSGI_APPLICATION = "messageboard.wsgi.application"

# Firebase configuration settings
FIREBASE_CONFIG = {
    'apiKey': config('FIREBASE_API_KEY'),
    'authDomain': config('FIREBASE_AUTH_DOMAIN'),
    'projectId': config('FIREBASE_PROJECT_ID'),
    'storageBucket': config('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': config('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': config('FIREBASE_APP_ID'),
    'measurementId': config('FIREBASE_MEASUREMENT_ID'),
}

# PWA Settings
PWA_APP_NAME = 'board4dng'
PWA_APP_DESCRIPTION = "A sleek and futuristic message board app."
PWA_APP_THEME_COLOR = '#ff66cc'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'portrait'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {'src': '/static/images/icons/icon-72x72.png', 'sizes': '72x72'},
    # Add other icon sizes here...
]
PWA_APP_ICONS_APPLE = [
    {'src': '/static/images/icons/icon-180x180.png', 'sizes': '180x180'}]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/images/splash_screens/4_iPhone_SE_iPod_touch_5th_generation.png',
        'media': '(device-width: 320px) and (device-height: 568px)'
    },
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

# Sessions
SESSION_COOKIE_AGE = 1200  # 20 minutes
SESSION_SAVE_EVERY_REQUEST = True

# Load secret key from environment variables
SECRET_KEY = config('SECRET_KEY')
DEBUG = True  # config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['board4dng.herokuapp.com', 'localhost', '127.0.0.1']

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Static files configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_SSL = True
EMAIL_HOST = 'mail.thepinkbook.com.au'
EMAIL_PORT = 465
EMAIL_HOST_USER = config(
    'EMAIL_HOST_USER', default='noreplyaccactivate@thepinkbook.com.au')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'noreplyaccactivate@thepinkbook.com.au'
MODERATOR_EMAIL = 'moderator@thepinkbook.com.au'

# Authentication settings
LOGIN_URL = 'board:login'
LOGIN_REDIRECT_URL = 'board:message_board'
AUTH_USER_MODEL = 'board.User'
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django-Heroku settings
django_heroku.settings(locals())

# Add security settings if DEBUG is False
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
