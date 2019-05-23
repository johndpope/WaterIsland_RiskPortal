""" URL Mapping to Controller for Securities App. """
from django.conf.urls import url
from . import views

app_name = 'etf'

urlpatterns = [
    url('get_etf_positions$', views.get_etf_positions, name='get_etf_positions'),
    url('get_etf_performances$', views.get_etf_performances, name='get_etf_performances'),
    url('get_tradegroup_etf_pnl$', views.get_tradegroup_etf_pnl, name='get_tradegroup_etf_pnl'),
]
