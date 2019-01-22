from django.conf.urls import url
from . import views

app_name = 'realtime_pnl_impacts'

urlpatterns = [
    url('live_tradegroup_pnl$',views.live_tradegroup_pnl,name='live_tradegroup_pnl'),
]


