from django.conf.urls import url, include
from . import views

app_name = 'risk_drawdown'

urlpatterns = [
    url('all_drawdowns', views.get_drawdowns, name='all_drawdowns'),
]
