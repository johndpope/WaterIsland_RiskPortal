from django.conf.urls import url
from . import views

urlpatterns = [
    url('get_latest_tweets/',views.get_latest_tweets,name='get_latest_tweets'),
]
