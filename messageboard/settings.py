import os
from pathlib import Path
import django_heroku
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


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
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

WSGI_APPLICATION = "messageboard.wsgi.application"

PWA_APP_NAME = 'board4dng'
PWA_APP_DESCRIPTION = "A sleek and futuristic message board app."
PWA_APP_THEME_COLOR = '#ff66cc'  # Customize with your preferred color
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'portrait'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {
        'src': '/static/images/icons/icon-72x72.png',
        'sizes': '72x72'
    },
    {
        'src': '/static/images/icons/icon-96x96.png',
        'sizes': '96x96'
    },
    {
        'src': '/static/images/icons/icon-128x128.png',
        'sizes': '128x128'
    },
    {
        'src': '/static/images/icons/icon-144x144.png',
        'sizes': '144x144'
    },
    {
        'src': '/static/images/icons/icon-152x152.png',
        'sizes': '152x152'
    },
    {
        'src': '/static/images/icons/icon-192x192.png',
        'sizes': '192x192'
    },
    {
        'src': '/static/images/icons/icon-384x384.png',
        'sizes': '384x384'
    },
    {
        'src': '/static/images/icons/icon-512x512.png',
        'sizes': '512x512'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/images/icons/icon-180x180.png',
        'sizes': '180x180'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/images/icons/splash-640x1136.png',
        'media': '(device-width: 320px) and (device-height: 568px)'
    },
    {
        'src': '/static/images/icons/splash-750x1334.png',
        'media': '(device-width: 375px) and (device-height: 667px)'
    },
    {
        'src': '/static/images/icons/splash-1242x2208.png',
        'media': '(device-width: 414px) and (device-height: 736px)'
    },
    {
        'src': '/static/images/icons/splash-1125x2436.png',
        'media': '(device-width: 375px) and (device-height: 812px)'
    },
    {
        'src': '/static/images/icons/splash-828x1792.png',
        'media': '(device-width: 414px) and (device-height: 896px)'
    },
    {
        'src': '/static/images/icons/splash-1242x2688.png',
        'media': '(device-width: 414px) and (device-height: 896px)'
    },
    {
        'src': '/static/images/icons/splash-1536x2048.png',
        'media': '(device-width: 768px) and (device-height: 1024px)'
    },
    {
        'src': '/static/images/icons/splash-1668x2224.png',
        'media': '(device-width: 834px) and (device-height: 1112px)'
    },
    {
        'src': '/static/images/icons/splash-1668x2388.png',
        'media': '(device-width: 834px) and (device-height: 1194px)'
    },
    {
        'src': '/static/images/icons/splash-2048x2732.png',
        'media': '(device-width: 1024px) and (device-height: 1366px)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

SESSION_COOKIE_AGE = 1200  # 20 minutes
SESSION_SAVE_EVERY_REQUEST = True


# Load the secret key from the .env file
SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=True, cast=bool)

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
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Email settings for your hosting provider
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_SSL = True
EMAIL_HOST = 'mail.thepinkbook.com.au'
EMAIL_PORT = 465
EMAIL_HOST_USER = config(
    'EMAIL_HOST_USER', default='noreplyaccactivate@thepinkbook.com.au')
EMAIL_HOST_PASSWORD = config(
    'EMAIL_HOST_PASSWORD')  # Load from .env
DEFAULT_FROM_EMAIL = 'noreplyaccactivate@thepinkbook.com.au'
MODERATOR_EMAIL = 'moderator@thepinkbook.com.au'


# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'message_board'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django-Heroku settings (optional)
django_heroku.settings(locals())
