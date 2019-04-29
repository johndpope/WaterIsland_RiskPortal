from django.conf.urls import url
from . import views

app_name = 'realtime_pnl_impacts'

urlpatterns = [
    url('live_tradegroup_pnl$', views.live_tradegroup_pnl, name='live_tradegroup_pnl'),
    url('live_pnl_monitors$', views.live_pnl_monitors, name='live_pnl_monitors'),
    url('fund_level_pnl$', views.fund_level_pnl, name='fund_level_pnl'),

]


