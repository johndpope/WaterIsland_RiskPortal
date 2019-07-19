from django.conf.urls import url
from . import views

app_name = 'portfolio_optimization'

urlpatterns = [
    url('ess_target_configs$', views.EssDealTypeParametersView.as_view(), name='ess_target_configs'),
    url('update_normlized_sizing_by_risk_adj_prob$', views.update_normlized_sizing_by_risk_adj_prob,
        name='update_normlized_sizing_by_risk_adj_prob'),
    url('update_soft_catalyst_risk_sizing$', views.update_soft_catalyst_risk_sizing,
        name='update_soft_catalyst_risk_sizing'),
    url('ess_potential_long_shorts', views.EssLongShortView.as_view(), name='ess_potential_long_shorts'),
    url('ess_implied_probabilites$', views.ess_implied_probabilites,
        name='ess_implied_probabilites'),
    url('ess_implied_prob_drilldown$', views.ess_implied_prob_drilldown,
        name='ess_implied_prob_drilldown'),
    url('get_deal_type_details/', views.get_deal_type_details, name='get_deal_type_details'),
    url('delete_deal_type/', views.delete_deal_type, name='delete_deal_type'),
    url('merer_arb_rors', views.MergerArbRorView.as_view(), name='merger_arb_rors'),
    url('arb_hard_optimization$', views.ArbHardOptimizationView.as_view(), name='arb_hard_optimization'),
    url('save_hard_opt_commment$', views.save_hard_opt_comment, name='save_hard_opt_comment'),
    url('save_rebal_paramaters$', views.save_rebal_paramaters, name='save_rebal_paramaters'),


]
