""" URL Mapping to Controller for Risk Reporting App. """
from django.conf.urls import url
from . import views

app_name = 'risk_reporting'

urlpatterns = [
    url('merger_arb_risk_attributes', views.merger_arb_risk_attributes, name='merger_arb_risk_attributes'),
    url('merger_arb_nav_impacts', views.merger_arb_nav_impacts, name='merger_arb_nav_impacts'),
    url('formula_based_downsides$', views.formula_based_downsides, name='formula_based_downsides'),
    url('credit_upside_downsides$', views.CreditDealsUpsideDownsideView.as_view(), name='credit_upside_downsides'),
    url('risk_factors_summary$', views.RiskFactorsSummaryView.as_view(), name='risk_factors_summary'),
    url('update_credit_deals_upside_downside$', views.update_credit_deals_upside_downside, name='update_credit_deals_upside_downside'),
    url('fetch_from_bloomberg_by_spread_index$', views.fetch_from_bloomberg_by_spread_index, name='fetch_from_bloomberg_by_spread_index'),
    url('credit_deals_csv_import$', views.credit_deals_csv_import, name='credit_deals_csv_import'),
    url('get_details_from_arb$', views.get_details_from_arb, name='get_details_from_arb'),
    url('update_credit_deal_risk_limit$', views.update_credit_deal_risk_limit, name='update_credit_deal_risk_limit'),
    url('update_downside_formulae$', views.update_downside_formulae, name='update_downside_formulae'),
    url('update_risk_limit$', views.update_risk_limit, name='update_risk_limit'),
    url('formulae_downsides_new_deal_add$', views.formulae_downsides_new_deal_add, name='formulae_downsides_new_deal_add'),
    url('security_info_download$', views.security_info_download, name='security_info_download'),
    url('deal_info_download$', views.deal_info_download, name='deal_info_download'),
]
