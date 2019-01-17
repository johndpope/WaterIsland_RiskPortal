from django.conf.urls import url
from . import views
app_name = 'equity_fixedincome_risk_reward'

urlpatterns = [
    url('compare_equity_bond/',views.compare_equity_bond, name='compare_equity_bond'),
    url('list_speculated_deals/',views.list_speculated_deals, name='list_speculated_deals'),
]