""" URL Mapping to Controller for Risk Reporting App. """
from django.conf.urls import url
from . import views

app_name = 'risk_reporting'

urlpatterns = [
    url('merger_arb_risk_attributes', views.merger_arb_risk_attributes, name='merger_arb_risk_attributes'),
    url('merger_arb_nav_impacts', views.merger_arb_nav_impacts, name='merger_arb_nav_impacts'),
    url('formula_based_downsides$', views.formula_based_downsides, name='formula_based_downsides'),
    url('update_downside_formulae$', views.update_downside_formulae, name='update_downside_formulae'),
    url('formulae_downsides_new_deal_add$', views.formulae_downsides_new_deal_add, name='formulae_downsides_new_deal_add'),
]
