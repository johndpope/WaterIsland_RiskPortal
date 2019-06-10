from django.conf.urls import url
from . import views

app_name = 'portfolio_optimization'

urlpatterns = [
    url('ess_target_configs$', views.ess_target_configs, name='ess_target_configs'),
    url('update_normlized_sizing_by_risk_adj_prob$', views.update_normlized_sizing_by_risk_adj_prob,
        name='update_normlized_sizing_by_risk_adj_prob'),
    url('update_soft_catalyst_risk_sizing$', views.update_soft_catalyst_risk_sizing,
        name='update_soft_catalyst_risk_sizing'),
    url('ess_potential_long_shorts', views.ess_potential_long_shorts,
        name='ess_potential_long_shorts'),
    url('ess_implied_probabilites$', views.ess_implied_probabilites,
        name='ess_implied_probabilites'),

]