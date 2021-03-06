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

engine = create_engine("mysql://" + env('WICFUNDS_DATABASE_USER') + ":" + env('WICFUNDS_DATABASE_PASSWORD')
                       + "@" + env('WICFUNDS_DATABASE_HOST') + "/" + env('WICFUNDS_DATABASE_NAME')
                       )


WICFUNDS_DATABASE_USER = env('WICFUNDS_DATABASE_USER')
WICFUNDS_DATABASE_PASSWORD = env('WICFUNDS_DATABASE_PASSWORD')
WICFUNDS_DATABASE_HOST = env('WICFUNDS_DATABASE_HOST')
WICFUNDS_DATABASE_NAME = env('WICFUNDS_DATABASE_NAME')

con = engine.connect()

SQLALCHEMY_CONNECTION = con
WICFUNDS_TEST_DATABASE_NAME = env('WICFUNDS_TEST_DATABASE_NAME')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INTERNAL_IPS = ('127.0.0.1', '10.16.1.151')

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']
AUTH_USER_MODEL = 'accounts.User'

CELERY_TIMEZONE = 'US/Eastern'

CELERY_BROKER_URL = env('CELERY_BROKER_URL')

CELERYBEAT_SCHEDULE = {
    'ESS_IDEA_DAILY_UPDATE': {
        'task': 'risk.tasks.ess_idea_daily_update',
        'schedule': crontab(hour=20, minute=00, day_of_week='mon-fri')
    # Execute every night to fetch EOD prices
    },
    'ESS_IDEA_FLAGGER': {
        'task': 'risk.tasks.premium_analysis_flagger',
        'schedule': crontab(hour=22, minute=00, day_of_week='mon-fri'),  # Execute after daily update
    },

    'DYNAMIC_DOWNSIDE_UPDATE': {
        'task': 'risk_reporting.tasks.refresh_base_case_and_outlier_downsides',
        'schedule': crontab(minute="*/11", hour='6-16', day_of_week='mon-fri'),  # Execute 20 min
    },
    'EMAIL_NAV_IMPACTS_REPORT': {
        'task': 'risk_reporting.tasks.email_nav_impacts_report',
        'schedule': crontab(minute="50", hour='6', day_of_week='mon-fri'),  # Execute weekdays morning at 6.50am
    },
    'EMAIL_DAILY_FORMULAE_LINKED_DOWNSIDES': {
        'task': 'risk_reporting.tasks.email_daily_formulae_linked_downsides',
        'schedule': crontab(minute="30", hour='16', day_of_week='mon-fri'),  # Execute weekdays morning at 6.40am
    },
    'CLEAN_UP_AWS_S3': {
        'task': 'cleanup.tasks.clean_up_aws_s3',
        'schedule': crontab(minute="00", hour="01", day_of_week=6),
    },
    'EMAIL_PL_TARGET_LOSS_BUDGETS': {
        'task': 'risk_reporting.tasks.email_pl_target_loss_budgets',
        'schedule': crontab(minute="00", hour="08", day_of_week='mon-fri')
    },
    'CALCULATE_REALTIME_PNL_BUDGETS': {
        'task': 'risk_reporting.tasks.calculate_realtime_pnl_budgets',
        'schedule': crontab(minute='*/15', hour='10-16', day_of_week='mon-fri'),
    },
    'SEND_DAILY_SITUATIONS_LOG': {
        'task': 'wic_news.tasks.email_news_additions',
        'schedule': crontab(minute="15", hour='19', day_of_week='mon-fri'),
    },
    'EMAIL_SALES_WEEKLY_REPORT': {
        'task': 'sales_reporting.tasks.email_weekly_sales_report',
        'schedule': crontab(minute="30", hour='9', day_of_week='mon'),
    },
    'REFRESH_ESS_LONG_SHORT_AND_IMPLIED_PROB': {
        'task': 'portfolio_optimization.tasks.refresh_ess_long_shorts_and_implied_probability',
        'schedule': crontab(minute="45", hour='18', day_of_week='mon-fri'),
    },
    'REFRESH_CREDIT_DEALS_UPSIDE_DOWNSIDE': {
        'task': 'risk_reporting.tasks.refresh_credit_deals_upside_downside',
        'schedule': crontab(minute='*/29', hour='6-16', day_of_week='mon-fri'),
    },
    'UPDATE_CREDIT_DEALS_UPSIDE_DOWNSIDE': {
        'task': 'risk_reporting.tasks.update_credit_deals_upside_downside_once_daily',
        'schedule': crontab(minute='00', hour='21', day_of_week='mon-fri'),
    },
    'ALERT_BEFORE_EZE_UPLOAD': {
        'task': 'risk_reporting.tasks.post_alert_before_eze_upload',
        'schedule': crontab(minute='00', hour='16', day_of_week='mon-fri'),
    },
    'DROP_ARB_DOWNSIDES_TO_EZE': {
        'task': 'risk_reporting.tasks.drop_arb_downsides_to_eze',
        'schedule': crontab(minute='59', hour='17', day_of_week='mon-fri'),
    },
    'REFRESH_ARB_RATE_OF_RETURNS': {
        'task': 'portfolio_optimization.tasks.get_arb_optimization_ranks',
        'schedule': crontab(minute='20', hour='20', day_of_week='mon-fri'),
    },
    'OPTIMIZE_HARD_CATALYST_FLOAT': {
        'task': 'portfolio_optimization.tasks.arb_hard_float_optimization',
        'schedule': crontab(minute='26', hour='20', day_of_week='mon-fri'),
    },

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
    'storages',
    'exposures',
    'celeryprogressmonitor',
    'position_stats',
    'cleanup',
    'risk_drawdown',
    'sales_reporting',
    'mna_deal',
    'etf',
    'position_rec',
    'portfolio_optimization',
    'credit_idea',
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
EMAIL_HOST_PASSWORD = '$' + env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True

ROOT_URLCONF = 'WicPortal_Django.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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
    'NorthPoint-PnLAppDb': {
        'ENGINE': 'sql_server.pyodbc',
        'HOST': env('NORTHPOINT_PNLAPPDB_DATABASE_HOST'),
        'USER': env('NORTHPOINT_PNLAPPDB_DATABASE_USER'),
        'PASSWORD': env('NORTHPOINT_PNLAPPDB_DATABASE_PASSWORD'),
        'NAME': env('NORTHPOINT_PNLAPPDB_DATABASE_NAME')
    },
    'NorthPoint-SecurityMaster': {
        'ENGINE': 'sql_server.pyodbc',
        'HOST': env('NORTHPOINT_PNLAPPDB_DATABASE_HOST'),
        'USER': env('NORTHPOINT_PNLAPPDB_DATABASE_USER'),
        'PASSWORD': env('NORTHPOINT_PNLAPPDB_DATABASE_PASSWORD'),
        'NAME': env('NORTHPOINT_SECURITYMASTER_DATABASE_NAME')
    },
}

if DEBUG == 'on':
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': env('LOCAL_TEST_DB_HOST'),
        'PORT': env('LOCAL_TEST_DB_PORT'),
        'USER': env('LOCAL_TEST_DB_USER'),
        'PASSWORD': env('LOCAL_TEST_DB_PASSWORD'),
        'NAME': env('LOCAL_TEST_DB_NAME'),
        'CONN_MAX_AGE': None,
    }
    DATABASES['wic'] = {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': env('LOCAL_TEST_DB_HOST'),
        'PORT': env('LOCAL_TEST_DB_PORT'),
        'USER': env('LOCAL_TEST_DB_USER'),
        'PASSWORD': env('LOCAL_TEST_DB_PASSWORD'),
        'NAME': 'wic',
        'CONN_MAX_AGE': None,
    }
else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': env('WICFUNDS_DATABASE_HOST'),
        'PORT': env('WICFUNDS_DATABASE_PORT'),
        'USER': env('WICFUNDS_DATABASE_USER'),
        'PASSWORD': env('WICFUNDS_DATABASE_PASSWORD'),
        'NAME': env('WICFUNDS_DATABASE_NAME'),
        'CONN_MAX_AGE': None,
    }
    DATABASES['wic'] = {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': env('WICFUNDS_DATABASE_HOST'),
        'PORT': env('WICFUNDS_DATABASE_PORT'),
        'USER': env('WICFUNDS_DATABASE_USER'),
        'PASSWORD': env('WICFUNDS_DATABASE_PASSWORD'),
        'NAME': 'wic',
        'CONN_MAX_AGE': None,
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
STATIC_ROOT = '../static'
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

# ****** AWS S3 for Static Files Serving ********
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')

# Tell django-storages the domain to use to refer to static files.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
MEDIA_URL = 'http://s3.amazonaws.com/{}/media/'.format(AWS_STORAGE_BUCKET_NAME)
# Tell the staticfiles app to use S3Boto3 storage when writing the collected static files (when
# you run `collectstatic`).


if DEBUG == 'on':
    DEBUG = True
    CURRENT_DATABASE = env('LOCAL_TEST_DB_NAME')
    DEAL_INFO_EZE_UPLOAD_PATH = r'DealInfo.csv'
    SECURITY_INFO_EZE_UPLOAD_PATH = r'SecurityInfo.csv'
else:
    DEBUG = False
    CURRENT_DATABASE = env('WICFUNDS_DATABASE_NAME')
    DEAL_INFO_EZE_UPLOAD_PATH = r'/mnt/shares/EzeData/Upload Files/DealInfo.csv'
    SECURITY_INFO_EZE_UPLOAD_PATH = r'/mnt/shares/EzeData/Upload Files/SecurityInfo.csv'

# DEBUG = False
# STATICFILES_LOCATION = 'static'
if not DEBUG:
    STATICFILES_LOCATION = 'static'
    STATICFILES_STORAGE = 'custom_storages.StaticStorage'

MEDIAFILES_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'
STATICFILES_LOCATION = 'static'

# Allow large data to be saved
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760 # 10 MB
