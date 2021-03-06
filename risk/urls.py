from django.conf.urls import url,include
from risk import views

app_name = 'risk'

urlpatterns = [
    url('mna_idea_database$', views.mna_idea_database, name='mna_idea_database'),
    url('ess_idea_database$', views.ess_idea_database, name='ess_idea_database'),
    url('show_ess_idea$', views.show_ess_idea, name='show_ess_idea'),
    url('add_new_ess_idea_deal$', views.add_new_ess_idea_deal, name='add_new_ess_idea_deal'),
    url('edit_ess_deal$', views.edit_ess_deal, name='edit_ess_deal'),
    url('delete_ess_idea$', views.delete_ess_idea, name='delete_ess_idea'),
    url('ess_idea_download_handler$', views.ess_idea_download_handler, name='ess_idea_download_handler'),
    url('get_ess_idea_celery_status$', views.get_celery_status, name='get_ess_idea_celery_status'),
    url('show_risk_factors(?P<deal_id>\w+)$', views.MaDealsRiskFactorsView.as_view(), name='show_risk_factors'),
    url('show_mna_idea$', views.show_mna_idea, name='show_mna_idea'),
    url('mna_idea_run_scenario_analysis$', views.mna_idea_run_scenario_analysis, name='mna_idea_run_scenario_analysis'),
    url('update_comments$', views.update_comments, name='update_comments'),
    url('add_new_mna_idea$', views.add_new_mna_idea, name='add_new_mna_idea'),
    url('archive_mna_idea$', views.archive_mna_idea, name='archive_mna_idea'),
    url('archive_ess_idea$', views.archive_ess_idea, name='archive_ess_idea'),
    url('restore_ess_idea$', views.restore_ess_idea, name='restore_ess_idea'),
    url('restore_merger_arb_idea$', views.restore_from_archive_mna_idea, name='restore_from_archive_mna_idea'),
    url('get_gics_sector$', views.get_gics_sector, name='get_gics_sector'),
    url('mna_idea_add_peers$', views.mna_idea_add_peers, name='mna_idea_add_peers'),
    url('add_new_mna_idea_lawyer_report$', views.add_new_mna_idea_lawyer_report, name='add_new_mna_idea_lawyer_report'),
    url('update_mna_idea_lawyer_report$', views.update_mna_idea_lawyer_report, name='update_mna_idea_lawyer_report'),
    url('delete_mna_idea_lawyer_report$', views.delete_mna_idea_lawyer_report, name='delete_mna_idea_lawyer_report'),
    url('add_or_update_mna_idea_weekly_downside_estimates$', views.add_or_update_mna_idea_weekly_downside_estimates,
        name='add_or_update_mna_idea_weekly_downside_estimates'),
    url('mna_idea_historical_downside_estimate$', views.mna_idea_historical_downside_estimate,
        name='mna_idea_historical_downside_estimate'),
    url('ess_idea_premium_analysis$', views.ess_idea_premium_analysis, name='ess_idea_premium_analysis'),
    url('calculate_mna_idea_deal_value$', views.calculate_mna_idea_deal_value, name='calculate_mna_idea_deal_value'),
    url('check_if_deal_present$', views.check_if_deal_present, name='check_if_deal_present'),
    url('fetch_bloomberg_data$', views.fetch_bloomberg_data, name='fetch_bloomberg_data'),
    url('delete_mna_idea$', views.delete_mna_idea, name='delete_mna_idea'),
    url('mna_idea_add_unaffected_date$', views.mna_idea_add_unaffected_date, name='mna_idea_add_unaffected_date'),
    url('edit_mna_idea_action_id$', views.edit_mna_idea_action_id, name='edit_mna_idea_action_id'),
    url('retrieve_cix_index$', views.retrieve_cix_index, name='retrieve_cix_index'),
    url('retrieve_spread_index$', views.retrieve_spread_index, name='retrieve_spread_index'),
    #Credit Section
    url('add_new_credit_deal$', views.add_new_credit_deal, name='add_new_credit_deal'),
    url('delete_credit_deal$', views.delete_credit_deal, name='delete_credit_deal'),
    url('show_all_credit_deals$', views.show_all_credit_deals, name='show_all_credit_deals'),
    url('credit_show_deal$', views.credit_show_deal, name='credit_show_deal'),
    url('ess_idea_view_balance_sheet$', views.ess_idea_view_balance_sheet, name='ess_idea_view_balance_sheet'),
    url('ess_idea_save_balance_sheet$', views.ess_idea_save_balance_sheet, name='ess_idea_save_balance_sheet'),
    url('get_premium_analysis_results_from_worker$', views.get_premium_analysis_results_from_worker,
        name='get_premium_analysis_results_from_worker'),
    url('premium_analysis_get_latest_calculations$', views.premium_analysis_get_latest_calculations,
        name='premium_analysis_get_latest_calculations'),
    url('get_attachments/', views.get_attachments, name='get_attachments'),
    url('ma_deal_detailed_export', views.ma_deal_detailed_export, name='ma_deal_detailed_export'),
]
