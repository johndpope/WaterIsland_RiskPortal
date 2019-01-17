from django.conf.urls import url
from . import views

app_name = 'portfolio_analytics'

urlpatterns = [
    url('show_current_deal_universe$',views.show_current_deal_universe,name = 'show_current_deal_universe')
]


