from django.conf.urls import url
from portfolio_optimization import views

app_name = 'portfolio_optimization'

urlpatterns = [
    url('portfolio_optimization$', views.get_portfolio_optimization, name='portfolio_optimization'),
]
