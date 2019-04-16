from django.conf.urls import url
from . import views

app_name = 'position_stats'

urlpatterns = [
    url('get_tradegroup_story/$', views.get_tradegroup_story, name='get_tradegroup_story'),
    url('get_tradegroup_performance_main_page', views.get_tradegroup_performance_main_page,
        name='get_tradegroup_performance_main_page'),
    url('get_tradegroup_attribution_over_own_capital', views.get_tradegroup_attribution_over_own_capital,
        name='get_tradegroup_attribution_over_own_capital'),


]
