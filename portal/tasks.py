import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import django
django.setup()

from celery import shared_task
from django_slack import slack_message
from django.conf import settings

from slack_utils import get_channel_name


@shared_task
def sqlalchemy_connection_pinging():
    """ Run this task every 30 mins to keep SQL Alchemy connection alive """
    try:
        settings.SQLALCHEMY_CONNECTION.execute('SELECT 1')
        slack_message('generic.slack', {'message': 'Connection ping successful. Waiting another 30 mins'},
                      channel=get_channel_name('sqlconnectionmonitor'),
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')
    except Exception as e:
        slack_message('generic.slack', {'message':'Warning!. SQL Server has gone away! Trying to Reconnect\n' + str(e)},
                      channel=get_channel_name('sqlconnectionmonitor'), token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')
        settings.SQLALCHEMY_CONNECTION.close()
