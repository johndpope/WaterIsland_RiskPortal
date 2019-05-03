import json
import pandas as pd

from django.conf import settings
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_pandas.io import read_frame

import dbutils
from holiday_utils import is_market_closed
from realtime_pnl_impacts.models import ArbitrageYTDPerformance, PnlLossBudget, PnlProfitTarget
from risk_reporting import tasks


def px_adjuster(bbg_sectype, northpoint_sectype, px, crncy, fx_rate, factor):
    if bbg_sectype == 'FORWARD' and crncy != 'USD': return factor * fx_rate * (1.0 / px) if not pd.isnull(px) else None
    if northpoint_sectype == 'EQSWAP': return px * factor  # don't fx eqswaps
    return px * factor * fx_rate


def fund_level_pnl(request):
    final_live_df, final_daily_pnl, position_level_pnl, last_updated, fund_level_live, final_position_level_ytd_pnl = get_data()
    fund_level_live = fund_level_live.groupby(['Group', 'TradeGroup']).sum().reset_index()
    assets_df = pd.read_sql_query('SELECT DISTINCT Fund, aum from wic.daily_flat_file_db where flat_file_as_of ='
                                  '(select max(flat_file_as_of) from wic.daily_flat_file_db)', con=connection)
    fund_details = pd.merge(fund_level_live, assets_df, left_on='Group', right_on='Fund')
    fund_details['ROC'] = 100.0 * (fund_details['MKTVAL_CHG_USD']/fund_details['Capital($)_x'])
    fund_details['Contribution_to_NAV'] = 1e4* (fund_details['MKTVAL_CHG_USD']/fund_details['aum'])
    del fund_details['Fund']
    del fund_details['Qty_x']
    fund_details_dict = {}
    funds = fund_details['Group'].unique()
    for each_fund in funds:
        fund_details_dict[each_fund] = fund_details[fund_details['Group'] == each_fund].to_json(orient='records')

    if request.is_ajax():
        return JsonResponse({
            'fund_details': fund_details_dict
        })


def apply_red_green_formatting(dataframe):
    for cols in dataframe.columns.values[2:]:
        dataframe[cols] = dataframe[cols].apply(lambda x: '<td style="color:red">'+'{0:,.2f}'.format(x)+'</td>'
                                                if x < 0 else '<td style="color:green">'+'{0:,.2f}'.format(x)+'</td>')
    return dataframe


def live_tradegroup_pnl(request):
    """ Returns the Live PnL and YTD PnL at the Tradegroup level """

    final_live_df, final_daily_pnl, position_level_pnl, last_updated, fund_level_live, final_position_level_ytd_pnl = get_data()

    position_level_pnl = apply_red_green_formatting(position_level_pnl)
    final_position_level_ytd_pnl = apply_red_green_formatting(final_position_level_ytd_pnl)

    if request.is_ajax():
        return_data = {'data': final_live_df.to_json(orient='records'),
                       'daily_pnl': final_daily_pnl.to_json(orient='records'),
                       'position_level_pnl': position_level_pnl.to_json(orient='records'),
                       'final_position_level_ytd_pnl': final_position_level_ytd_pnl.to_json(orient='records'),
                       'last_synced_on': last_updated}

        return JsonResponse(return_data)

    return render(request, 'realtime_pnl_impacts.html', {'last_updated': last_updated})


def get_data():
    position_level_ytd_pnl = pd.read_sql_query('select Fund, TradeGroup, Ticker, SUM(Ticker_PnL_Dollar) as '
                                               'YtdTickerPnlDollar from wic.ticker_pnl_breakdown where YEAR(`Date`) = '
                                               'YEAR(current_timestamp()) GROUP BY Fund, TradeGroup, Ticker',
                                               con=connection)
    ytd_options = pd.read_sql_query('select Fund, TradeGroup, SUM(Options_PnL_Dollar) as YtdOptionsDollar from '
                                    'wic.tradegroup_overall_pnl where YEAR(`Date`) = YEAR(current_timestamp())'
                                    ' GROUP BY Fund, TradeGroup;', con=connection)
    ytd_options['Options'] = 'Options'

    ytd_performance = read_frame(ArbitrageYTDPerformance.objects.all())

    ytd_performance.columns = ['id', 'Fund', 'Sleeve', 'Catalyst', 'TradeGroup', 'LongShort', 'InceptionDate',
                               'EndDate',
                               'Status', 'YTD($)', 'fund_aum', 'pnl_bps']
    del ytd_performance['id']

    assert len(ytd_performance) > 0
    all_portfolios_df = dbutils.Wic.get_live_pnl_monitored_portfolio_ids()
    portfolio_df = all_portfolios_df.copy()

    # Get this only if markeet is OPEN
    px_df = dbutils.Wic.get_live_pnl_df()
    px_df = px_df[px_df.PX_LAST.notnull()]
    px_factor_df = dbutils.Wic.get_live_pnl_px_factors_df()  # ['BBGID','CRNCY','FACTOR','FX_SYMBOL','DATA_TIMESTAMP']
    fx_df = dbutils.Wic.get_live_pnl_fx_rates_df()  # cols = ['Timestamp','FX_SYMBOL','FX_RATE']
    last_updated = fx_df['Timestamp'].max()
    df = pd.merge(px_df, px_factor_df, how='inner', on='API_IDENTIFIER')
    df = pd.merge(df, fx_df, how='left', on=['FX_SYMBOL', 'Timestamp'])
    df = pd.merge(df, portfolio_df, how='inner', on='API_IDENTIFIER')

    df['FX_RATE'] = df['FX_RATE'].fillna(1)  # Non FX_RATE is USD, rate = 1
    df['ADJ_PX'] = [px_adjuster(sectype, np_sectype, px, crncy, fx_rate, factor) for
                    (sectype, np_sectype, px, crncy, fx_rate, factor) in
                    zip(df['SECURITY_TYP'], df['NP_SecType'], df['PX_LAST'], df['CRNCY'], df['FX_RATE'], df['FACTOR'])]

    df['MktVal'] = df['ADJ_PX'].astype(float) * df['Qty'].astype(float)
    df['MktVal Chg Factor'] = [fx_rate if np_sectype == 'EQSWAP' else 1.0 for (fx_rate, np_sectype) in
                               zip(df['FX_RATE'], df['NP_SecType'])]
    float_cols = ['ADJ_PX', 'Qty', 'MktVal', 'Capital($)', 'Capital(%)', 'BaseCaseNavImpact', 'OutlierNavImpact']
    df[float_cols] = df[float_cols].astype(float)

    cols2include = ['Group', 'TradeGroup', 'TICKER', 'API_IDENTIFIER', 'ADJ_PX', 'Qty', 'MktVal', 'FX_RATE',
                    'Sleeve', 'Bucket', 'AlphaHedge', 'LongShort', 'CatalystName', 'Analyst', 'NP_SecType',
                    'Capital($)',
                    'Capital(%)', 'BaseCaseNavImpact', 'OutlierNavImpact']

    join_on_cols = ['Group', 'TradeGroup', 'API_IDENTIFIER', 'Sleeve', 'Bucket', 'AlphaHedge', 'LongShort',
                    'CatalystName',
                    'Analyst', 'NP_SecType']

    start_df = df[df['Timestamp'] == df['Timestamp'].min()][cols2include].rename(
        columns={'ADJ_PX': 'START_ADJ_PX', 'MktVal': 'START_MKTVAL', 'FX_RATE': 'START_FX_RATE'})
    end_df = df[df['Timestamp'] == df['Timestamp'].max()][cols2include].rename(
        columns={'ADJ_PX': 'END_ADJ_PX', 'MktVal': 'END_MKTVAL', 'FX_RATE': 'END_FX_RATE'})
    table_df = pd.merge(start_df, end_df, how='inner', on=join_on_cols)

    table_df['MKTVAL_CHG_USD'] = [(end_mktval - start_mktval) * end_fx_rate if np_sectype == 'EQSWAP' else
                                  (end_mktval - start_mktval) for (end_mktval, start_mktval, end_fx_rate, np_sectype) in
                                  zip(table_df['END_MKTVAL'], table_df['START_MKTVAL'], table_df['END_FX_RATE'],
                                      table_df['NP_SecType'])]
    table_df['PX_CHG_PCT'] = 100.0 * (
            (table_df['END_ADJ_PX'].astype(float) / table_df['START_ADJ_PX'].astype(float)) - 1.0)

    position_level_pnl = table_df[['Group', 'TradeGroup', 'TICKER_x', 'START_ADJ_PX', 'END_ADJ_PX',
                                   'MKTVAL_CHG_USD']].copy()
    funds_list = ['ARB', 'AED', 'LG', 'MACO', 'TAQ', 'CAM', 'LEV', 'TACO', 'MALT', 'WED']
    position_level_pnl = position_level_pnl[position_level_pnl['Group'].isin(funds_list)]
    final_position_level_ytd_pnl = pd.merge(position_level_pnl, position_level_ytd_pnl,
                                            left_on=['Group', 'TradeGroup', 'TICKER_x'],
                                            right_on=['Fund', 'TradeGroup', 'Ticker'])
    final_position_level_ytd_pnl['MKTVAL_CHG_USD'] = (final_position_level_ytd_pnl['MKTVAL_CHG_USD'] +
                                                      final_position_level_ytd_pnl['YtdTickerPnlDollar'])
    final_ytd_options = pd.merge(final_position_level_ytd_pnl, ytd_options, on=['Fund', 'TradeGroup'], how='right')
    final_ytd_options = final_ytd_options[['Group', 'TradeGroup', 'YtdOptionsDollar', 'Options']].copy()
    final_ytd_options['START_ADJ_PX'] = 0
    final_ytd_options['END_ADJ_PX'] = 0
    final_ytd_options.rename(columns={'YtdOptionsDollar': 'MKTVAL_CHG_USD', 'Options': 'TICKER_x'}, inplace=True)
    final_ytd_options = pd.pivot_table(final_ytd_options,
                                       index=['TradeGroup', 'TICKER_x', 'START_ADJ_PX', 'END_ADJ_PX'],
                                       columns=['Group'], aggfunc='first', fill_value=0).reset_index()
    final_ytd_options.columns = ["_".join((i, j)) for i, j in final_ytd_options.columns]

    final_position_level_ytd_pnl = final_position_level_ytd_pnl[['TradeGroup', 'TICKER_x', 'START_ADJ_PX',
                                                                 'END_ADJ_PX', 'Group', 'MKTVAL_CHG_USD']].copy()
    final_position_level_ytd_pnl = pd.pivot_table(final_position_level_ytd_pnl,
                                                  index=['TradeGroup', 'TICKER_x', 'START_ADJ_PX', 'END_ADJ_PX'],
                                                  columns=['Group'], aggfunc='first',
                                                  fill_value=0).reset_index()
    final_position_level_ytd_pnl.columns = ["_".join((i, j)) for i, j in final_position_level_ytd_pnl.columns]
    final_position_level_ytd_pnl = final_position_level_ytd_pnl.append(final_ytd_options)
    final_position_level_ytd_pnl.reset_index(inplace=True)
    del final_position_level_ytd_pnl['index']
    position_level_pnl = pd.pivot_table(position_level_pnl, index=['TradeGroup', 'TICKER_x', 'START_ADJ_PX',
                                                                   'END_ADJ_PX'], columns=['Group'], aggfunc='first',
                                        fill_value=0).reset_index()
    position_level_pnl.columns = ["_".join((i, j)) for i, j in position_level_pnl.columns]
    position_level_pnl.reset_index(inplace=True)
    del position_level_pnl['index']
    position_level_pnl = position_level_pnl.round(decimals=2)
    final_position_level_ytd_pnl = final_position_level_ytd_pnl.round(decimals=2)  # Round to 2 decimals

    table_df = table_df[['Group', 'TradeGroup', 'START_ADJ_PX', 'END_ADJ_PX', 'PX_CHG_PCT', 'Qty_x', 'Analyst',
                         'Capital($)_x', 'Capital(%)_x', 'START_MKTVAL', 'END_MKTVAL', 'MKTVAL_CHG_USD']]

    table_df = table_df.groupby(['Group', 'TradeGroup']).sum().reset_index()
    daily_live_pnl = table_df.copy()
    daily_live_pnl = daily_live_pnl[daily_live_pnl['Group'].isin(['ARB', 'AED', 'LG', 'MACO', 'TAQ', 'CAM', 'LEV',
                                                                  'TACO', 'MALT', 'WED'])]
    #  Daily P&L Calculations
    fund_level_live = daily_live_pnl.copy()

    daily_live_pnl = daily_live_pnl[['Group', 'TradeGroup', 'MKTVAL_CHG_USD']]
    daily_live_pnl[['Group']] = daily_live_pnl[['Group']].fillna('NA')
    daily_live_pnl.fillna(0, inplace=True)
    daily_live_pnl = pd.merge(daily_live_pnl, ytd_performance[['TradeGroup', 'Fund', 'Sleeve', 'Catalyst']],
                              left_on=['TradeGroup', 'Group'], right_on=['TradeGroup', 'Fund'])
    del daily_live_pnl['Fund']
    daily_live_pnl.columns = ['Fund', 'TradeGroup', 'Daily PnL', 'Sleeve', 'Catalyst']

    ytd_performance['TradeGroup'] = ytd_performance['TradeGroup'].apply(lambda x: x.strip())
    ytd_performance.loc[ytd_performance['TradeGroup'] == 'BEL -  MC FP', ['TradeGroup']] = 'BEL - MC FP'  # Todo: Update

    # Merge Only if Market is open...
    if is_market_closed():
        table_df = table_df.iloc[0:0]
    final_live_df = pd.merge(table_df, ytd_performance, how='outer', left_on=['Group', 'TradeGroup'],
                             right_on=['Fund', 'TradeGroup'])

    final_live_df[['Fund']] = final_live_df[['Fund']].fillna('NA')
    final_live_df.fillna(0, inplace=True)
    final_live_df['YTD($)'] = final_live_df['YTD($)'].apply(round)
    final_live_df['MKTVAL_CHG_USD'] = final_live_df['MKTVAL_CHG_USD'].apply(round)

    final_live_df['Total YTD PnL'] = final_live_df['YTD($)'] + final_live_df['MKTVAL_CHG_USD']

    final_live_df['InceptionDate'] = final_live_df['InceptionDate'].apply(str)
    final_live_df['EndDate'] = final_live_df['EndDate'].apply(str)

    final_live_df = final_live_df[final_live_df['Fund'].isin(['ARB', 'AED', 'LG', 'MACO', 'TAQ', 'CAM', 'LEV', 'TACO',
                                                              'MALT', 'WED'])]

    final_live_df = final_live_df[['Fund', 'TradeGroup', 'Sleeve', 'Catalyst', 'Total YTD PnL']]

    final_live_df = pd.pivot_table(final_live_df, index=['TradeGroup', 'Sleeve', 'Catalyst'],
                                   columns='Fund', fill_value=0).reset_index()
    final_live_df.columns = ["_".join((i, j)) for i, j in final_live_df.columns]
    final_live_df.reset_index(inplace=True)
    del final_live_df['index']

    try:
        final_daily_pnl = pd.pivot_table(daily_live_pnl, index=['TradeGroup', 'Sleeve', 'Catalyst'],
                                         columns='Fund', fill_value=0).reset_index()
        final_daily_pnl.columns = ["_".join((i, j)) for i, j in final_daily_pnl.columns]
        final_daily_pnl.reset_index(inplace=True)
        del final_daily_pnl['index']
    except:
        final_daily_pnl = pd.DataFrame()

    return final_live_df, final_daily_pnl, position_level_pnl, last_updated, fund_level_live, final_position_level_ytd_pnl


def live_pnl_monitors(request):
    if request.is_ajax():
        df = pd.read_sql_query("SELECT * FROM " + settings.CURRENT_DATABASE + ".realtime_pnl_impacts_pnlmonitors"
                                                                              " where last_updated = "
                                                                              "(select max(last_updated) from "
                               + settings.CURRENT_DATABASE+".realtime_pnl_impacts_pnlmonitors)",
                               con=connection)
        last_updated = df['last_updated'].max()
        del df['last_updated']
        df.rename(columns={'fund': 'Fund', 'ytd_active_deal_losses': 'YTD Active Deal Losses',
                           'ytd_closed_deal_losses': 'YTD Closed Deal Losses', 'ann_loss_budget_perc': 'Loss Budget',
                           'investable_assets': 'AUM', 'gross_ytd_pnl': 'Gross YTD P&L',
                           'ann_gross_pnl_target_perc': 'Ann. Gross P&L Target %', 'time_passed': 'Time Passed',
                           'gross_ytd_return': 'Gross YTD Return',
                           'ann_gross_pnl_target_dollar': 'Ann. Gross P&L Target $',
                           'ytd_pnl_perc_target': 'YTD P&L % of Target', 'ann_loss_budget_dollar': 'Ann Loss Budget $',
                           'ytd_total_loss_perc_budget': 'YTD Total Loss % of Budget'}, inplace=True)

        pivoted = pd.pivot_table(df, columns=['Fund'], aggfunc=lambda x: x, fill_value='')

        pivoted = pivoted[['ARB', 'MACO', 'MALT', 'AED', 'CAM', 'LG', 'LEV', 'TACO', 'TAQ']]
        pivoted = pivoted.reindex(['AUM',
                                   'Ann. Gross P&L Target %',
                                   'Gross YTD Return',
                                   'YTD P&L % of Target',
                                   'Time Passed',
                                   'Ann. Gross P&L Target $',
                                   'Gross YTD P&L',
                                   'Loss Budget',
                                   'YTD Total Loss % of Budget',
                                   'Time Passed',
                                   'Ann Loss Budget $',
                                   'YTD Closed Deal Losses',
                                   'YTD Active Deal Losses',
                                   ])
        df1 = pivoted.iloc[:7].copy()
        df2 = pivoted.iloc[7:].copy()
        df3 = pd.DataFrame([list(pivoted.columns.values)], columns=list(pivoted.columns.values))
        df1 = df1.append(df3)
        df1.index.values[5] = '* Ann. Gross P&L Target $'
        df1.index.values[7] = 'Loss Budgets'
        df1 = df1.append(df2)
        df1.index.values[8] = 'Ann Loss Budget %'
        df1.index.values[0] = 'Investable Assets'
        df1.index.values[4] = 'Time Passed%'
        df1.index.values[10] = 'Time Passed %'
        df1.index.values[11] = '* Ann Loss Budget $'

        return JsonResponse({'data': df1.to_json(orient='index'),
                             'last_updated': last_updated})


def update_profit_loss_targets(request):
    response = 'Failed'
    if request.POST:
        is_profit_target = request.POST.get('is_profit_target') == 'true'
        fund = request.POST.get('fund')
        value = float(request.POST.get('value'))
        if is_profit_target:
            PnlProfitTarget(fund=fund, profit_target=value).save()
        else:
            if value > 0:
                value = value * -1
            PnlLossBudget(fund=fund, loss_budget=value).save()
        calculated_pnl_budgets = tasks.calculate_pnl_budgets()
        response = 'Success'
    return HttpResponse(response)
