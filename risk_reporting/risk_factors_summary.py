from django.db import connection
from django.http import JsonResponse
import pandas as pd

from risk.forms import MaDealsRiskFactorsForm
from risk.models import MA_Deals, MA_Deals_Risk_Factors
from risk_reporting.models import DailyNAVImpacts


FUND_NAMES = ['AED', 'ARB', 'CAM', 'LEV', 'LG', 'MACO', 'MALT', 'TACO', 'TAQ', 'WED']


def get_summary_for_risk_factors():
    response = {'msg': 'Failed', 'data': {}}
    data = {}
    try:
        regulatory_tab_dict = {'SEC': 'sec_requirement', 'HSR': 'hsr_requirement', 'MOFCOM': 'mofcom_requirement',
                               'CIFIUS': 'cifius_requirement', 'EC': 'ec_requirement', 'ACCC': 'accc_requirement',
                               'CANADIAN': 'investment_canada_requirement', 'CADE': 'cade_requirement'}
        main_tabs_dict = {'Regulatory Risk': regulatory_tab_dict, 'Country Risk': ['other_country_regulatory_risk_one',
                          'other_country_regulatory_risk_two'], 'Divestitures Reqd': 'divestitures_required',
                          'Acquirer SH Vote Reqd': 'acquirer_sh_vote_required',
                          'Target SH Vote Reqd': 'target_sh_vote_required_percentage', 'Valuation': 'fair_valuation',
                          'Acquirer Becomes Target': 'acquirer_becomes_target', 'PE Deals': 'strategic_pe',
                          'Commodities Risk': 'commodity_risk', 'Cyclical Industry': 'cyclical_industry',
                          'Inversion Risk': 'is_inversion_deal_or_tax_avoidance'}

        risk_factors_df = pd.DataFrame.from_records(MA_Deals_Risk_Factors.objects.all().values())
        wic_flat_file_all_funds_df = pd.read_sql_query('SELECT * FROM wic.daily_flat_file_db where flat_file_as_of = ' \
                                                       '(select max(flat_file_as_of) from wic.daily_flat_file_db) and' \
                                                       ' Sleeve = \'Merger Arbitrage\'', con=connection)
        ma_deals_df = pd.DataFrame.from_records(MA_Deals.objects.all().values())
        merge_df = pd.merge(risk_factors_df, ma_deals_df[['id', 'deal_name', 'status']], left_on=['deal_id'],
                            right_on=['id'], how='left')
        merge_df.rename(columns={'id_x': 'id', 'id_y': 'deal_id'}, inplace=True)
        for fund in FUND_NAMES:
            wic_flat_file_df = wic_flat_file_all_funds_df[wic_flat_file_all_funds_df['Fund'] == fund]
            fund_tab_data = {}
            for main_tab in main_tabs_dict:
                if main_tab == 'Regulatory Risk':
                    main_tab_data = {}
                    for regulatory_tab in main_tabs_dict[main_tab]:
                        field_names_list = [regulatory_tab_dict[regulatory_tab]]
                        tab_data = get_tabs_data(wic_flat_file_df, merge_df, field_names_list)
                        main_tab_data[regulatory_tab] = tab_data
                    fund_tab_data['Regulatory Risk'] = main_tab_data
                else:
                    main_tab_data = {}
                    field_names_list = main_tabs_dict[main_tab]
                    field_names_list = field_names_list if isinstance(field_names_list, (list,)) else [field_names_list]
                    tab_data = get_tabs_data(wic_flat_file_df, merge_df, field_names_list)
                    fund_tab_data[main_tab] = tab_data
            data[fund] = fund_tab_data
        response = {'msg': 'Success', 'data': data}
    except Exception as e:
        response = {'msg': 'Failed', 'data': {}}
    return response


def get_unique_deal_names(dataframe, field_names, value):
    result = []
    if not dataframe.empty and field_names and value:
        for field_name in field_names:
            result += dataframe[dataframe[field_name] == value].deal_name.unique().tolist()
        return list(set(result))
    return result


def get_select_choices_list(fields_list, form):
    result = []
    if form and fields_list:
        for field_name in fields_list:
            form_field = form.fields.get(field_name)
            if form_field:
                choices = form_field._choices
                if choices:
                    for choice in choices:
                        result.append(choice[0])
        result = list(set(result))
    return result


def get_current_mkt_val(value, required_field):
    try:
        if not value.empty:
            index = value.index
            if not index.empty:
                index = index[0]
                return value.at[index, required_field] 
        else:
            return 0
    except Exception as e:
        return 0.0


def get_tabs_data(wic_flat_file_df, merge_df, field_names_list):
    tab_data = {}
    risk_form = MaDealsRiskFactorsForm()
    option_list = get_select_choices_list(field_names_list, risk_form)
    if option_list:
        impacts_df = pd.DataFrame.from_records(DailyNAVImpacts.objects.all().values())
        for option in option_list:
            if option:
                option_data = []
                unique_deal_names = get_unique_deal_names(merge_df, field_names_list, option)
                for deal_name in unique_deal_names:
                    deal_data = {}
                    deal_df = wic_flat_file_df[wic_flat_file_df['TradeGroup'] == deal_name.upper()]
                    deal_df = deal_df.groupby(['AlphaHedge']).agg('sum').reset_index()
                    alpha_mkt_val = get_current_mkt_val(deal_df[deal_df['AlphaHedge'] == 'Alpha'], 'CurrentMktVal')
                    alphahedge_mkt_val = get_current_mkt_val(deal_df[deal_df['AlphaHedge'] == 'AlphaHedge'], 'CurrentMktVal')
                    hedge_mkt_val = get_current_mkt_val(deal_df[deal_df['AlphaHedge'] == 'Hedge'], 'CurrentMktVal')
                    alpha_alphahedge_val = alpha_mkt_val + alphahedge_mkt_val
                    deal_mkt_val = hedge_mkt_val + alpha_alphahedge_val
                    deal_status = 'Unknown'
                    deal_status_index = merge_df[merge_df['deal_name'] == deal_name].index
                    if not deal_status_index.empty:
                        deal_status_index = deal_status_index[0]
                        deal_status = merge_df.loc[deal_status_index, 'status']
                    impacts_df_index = impacts_df[impacts_df['TradeGroup'] == deal_name].index
                    if not impacts_df_index.empty:
                        impacts_df_index = impacts_df_index[0]
                        try:
                            outlier_nav_impact = float(impacts_df.at[impacts_df_index, 'OUTLIER_NAV_IMPACT_ARB'])
                        except ValueError:
                            outlier_nav_impact = 0.0
                    else:
                        outlier_nav_impact = 0.0
                    deal_data = {'deal_name': deal_name, 'alpha_mkt_val': alpha_mkt_val,
                                 'alphahedge_mkt_val': alphahedge_mkt_val, 'hedge_mkt_val': hedge_mkt_val,
                                 'alpha_alphahedge_val': alpha_alphahedge_val, 'deal_mkt_val': deal_mkt_val,
                                 'outlier_nav_impact': outlier_nav_impact, 'deal_status': deal_status}
                    option_data.append(deal_data)
                tab_data[option] = option_data
    return tab_data
