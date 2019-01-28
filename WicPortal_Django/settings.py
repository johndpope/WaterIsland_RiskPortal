"""
Django settings for WicPortal_Django project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

from datetime import timedelta
import os
from celery.schedules import crontab
import environ
from sqlalchemy import create_engine

env = environ.Env()
environ.Env.read_env()  # Read the .env File

engine = create_engine("mysql://"+env('WICFUNDS_DATABASE_USER')+":"+env('WICFUNDS_DATABASE_PASSWORD')
                       + "@" + env('WICFUNDS_DATABASE_HOST')+"/"+env('WICFUNDS_DATABASE_NAME'))
con = engine.connect()

SQLALCHEMY_CONNECTION = con
WICFUNDS_TEST_DATABASE_NAME = env('WICFUNDS_TEST_DATABASE_NAME')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INTERNAL_IPS = ('127.0.0.1','10.16.1.151')

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']
AUTH_USER_MODEL = 'accounts.User'

CELERY_TIMEZONE = 'US/Eastern'

CELERY_BROKER_URL = env('CELERY_BROKER_URL')

CELERYBEAT_SCHEDULE = {
    'ESS_IDEA_DAILY_UPDATE':{
        'task':'risk.tasks.ess_idea_daily_update',
        'schedule':crontab(hour=9, minute=45, day_of_week='mon-fri') #Execute every morning at 9.40 after market opens
    },
    # 'MERGER_ARB_NAV_IMPACTS_UPDATES':{
    #     'task':'risk_reporting.tasks.update_merger_arb_nav_impacts',
    #     'schedule':crontab(minute='*/15'), #Execute every morning at 9.40 after market opens
    # },
    'ESS_IDEA_FLAGGER':{
        'task':'risk.tasks.premium_analysis_flagger',
        'schedule':crontab(hour=10, minute=38, day_of_week='mon-fri'), #Execute every morning after daily update
    }
}

BROKER_POOL_LIMIT = 0
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'accounts',
    'portal',
    'weather',
    'wic_news',
    'tweets',
    'breakfast',
    'risk',
    'statpro',
    'notes',
    'djcelery',
    'equity_fixedincome_risk_reward',
    'risk_reporting',
    'portfolio_analytics',
    'django_slack',
    'realtime_pnl_impacts',
    'securities',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = '$'+env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True

ROOT_URLCONF = 'WicPortal_Django.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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

WSGI_APPLICATION = 'WicPortal_Django.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': env('WICFUNDS_DATABASE_HOST'),
        'PORT': env('WICFUNDS_DATABASE_PORT'),
        'USER': env('WICFUNDS_DATABASE_USER'),
        'PASSWORD': env('WICFUNDS_DATABASE_PASSWORD'),
        'NAME': env('WICFUNDS_DATABASE_NAME'),
        'CONN_MAX_AGE': None,
    },
    'waterislandproduction': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': env('WICFUNDS_PRODUCTION_DATABASE_HOST'),
        'PORT': env('WICFUNDS_PRODUCTION_DATABASE_PORT'),
        'USER': env('WICFUNDS_PRODUCTION_DATABASE_USER'),
        'PASSWORD': env('WICFUNDS_PRODUCTION_DATABASE_PASSWORD'),
        'NAME': env('WICFUNDS_PRODUCTION_DATABASE_NAME'),
        'CONN_MAX_AGE': None,
    },

    'NorthPoint-PnLAppDb':{
        'ENGINE': 'sql_server.pyodbc',
        'HOST': env('NORTHPOINT_PNLAPPDB_DATABASE_HOST'),
        'USER': env('NORTHPOINT_PNLAPPDB_DATABASE_USER'),
        'PASSWORD': env('NORTHPOINT_PNLAPPDB_DATABASE_PASSWORD'),
        'NAME': env('NORTHPOINT_PNLAPPDB_DATABASE_NAME')
    },
    'NorthPoint-SecurityMaster':{
        'ENGINE': 'sql_server.pyodbc',
        'HOST': env('NORTHPOINT_PNLAPPDB_DATABASE_HOST'),
        'USER': env('NORTHPOINT_PNLAPPDB_DATABASE_USER'),
        'PASSWORD': env('NORTHPOINT_PNLAPPDB_DATABASE_PASSWORD'),
        'NAME': env('NORTHPOINT_SECURITYMASTER_DATABASE_NAME')
    },
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = False

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# LOGIN_REDIRECT_URL = 'index'
# LOGIN_URL = '/accounts/login/'

# --- MEDIA ---
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

SLACK_TOKEN = env('SLACK_TOKEN')
SLACK_CHANNEL = env('SLACK_CHANNEL')
SLACK_USERNAME = env('SLACK_USERNAME')
SLACK_BACKEND = env('SLACK_BACKEND')

TWEEPY_CONSUMER_SECRET = env('TWEEPY_CONSUMER_SECRET')
TWEEPY_CONSUMER_KEY = env('TWEEPY_CONSUMER_KEY')
TWEEPY_ACCESS_TOKEN = env('TWEEPY_ACCESS_TOKEN')
TWEEPY_ACCESS_TOKEN_SECRET = env('TWEEPY_ACCESS_TOKEN_SECRET')