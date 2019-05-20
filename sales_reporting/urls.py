""" URL Mapping to Controller for Risk Reporting App. """
from django.conf.urls import url
from . import views

app_name = 'sales_reporting'

urlpatterns = [
    url('weekly_template$', views.weekly_template, name='weekly_template'),
]
