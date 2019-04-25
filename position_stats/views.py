import pandas as pd
import json
from urllib.parse import urlencode
from django.shortcuts import render
from django.db import connection
from django_pandas.io import read_frame
from django.http import JsonResponse
# Create your views here.


def get_tradegroup_performance_main_page(request):
    as_of = '(select max(`Date`)'
    error = ''
    perf_dict = {}
    perf_dict_bips = {}
    if 'as_of' in request.GET:
        as_of = "(SELECT " + "\'" + request.GET['as_of'] + "\'"

    # Catching Value error referes to Absent Data
    try:

        tradegroup_performance_dollars = pd.read_sql_query("SELECT * FROM wic.tradegroup_attribution_to_fund_nav_dollar "
                                                           "where `Date` =  " + as_of +
                                                           " FROM wic.tradegroup_attribution_to_fund_nav_dollar LIMIT 1)",
                                                           con=connection)

        tradegroup_performance_bips = pd.read_sql_query("SELECT * FROM wic.tradegroup_attribution_to_fund_nav_bps "
                                                        "where `Date` =  " + as_of +
                                                        " FROM wic.tradegroup_attribution_to_fund_nav_bps LIMIT 1)",
                                                        con=connection)

        catalyst_df = pd.read_sql_query("SELECT DISTINCT TradeGroup, Fund, CatalystTypeWIC, CatalystRating FROM "
                                        "wic.daily_flat_file_db WHERE Flat_file_as_of = (select max(flat_file_as_of) "
                                        " FROM wic.daily_flat_file_db)", con=connection)

        tradegroup_performance_bips['Date'] = tradegroup_performance_bips['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        tradegroup_performance_dollars['Date'] = tradegroup_performance_dollars['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        tradegroup_performance_bips['InceptionDate'] = tradegroup_performance_bips['InceptionDate'].apply(lambda x: x.strftime('%Y-%m-%d') if not pd.isna(x) else x)
        tradegroup_performance_dollars['InceptionDate'] = tradegroup_performance_dollars['InceptionDate'].apply(lambda x: x.strftime('%Y-%m-%d') if not pd.isna(x) else x)
        tradegroup_performance_bips['EndDate'] = tradegroup_performance_bips['EndDate'].apply(lambda x: x.strftime('%Y-%m-%d') if not pd.isna(x) else x)
        tradegroup_performance_dollars['EndDate'] = tradegroup_performance_dollars['EndDate'].apply(lambda x: x.strftime('%Y-%m-%d') if not pd.isna(x) else x)

        tradegroup_performance_dollars = pd.merge(tradegroup_performance_dollars, catalyst_df, how='left',
                                                  on=['TradeGroup', 'Fund'])

        tradegroup_performance_bips = pd.merge(tradegroup_performance_bips, catalyst_df, how='left',
                                               on=['TradeGroup', 'Fund'])

        def create_story_url(row):
            url = '../position_stats/get_tradegroup_story?'
            tg_fund = {'TradeGroup': row['TradeGroup'], 'Fund': row['Fund']}
            url = url + urlencode(tg_fund)
            return "<a target='_blank' href='"+url+"'>View</a>"

        tradegroup_performance_dollars['story_url'] = tradegroup_performance_dollars.apply(create_story_url, axis=1)
        tradegroup_performance_bips['story_url'] = tradegroup_performance_bips.apply(create_story_url, axis=1)

        perf_dict = {}
        for fund in tradegroup_performance_dollars['Fund'].unique():
            perf_dict[fund] = tradegroup_performance_dollars[tradegroup_performance_dollars['Fund'] == fund].to_json(orient='records')

        perf_dict_bips = {}
        for fund in tradegroup_performance_bips['Fund'].unique():
            perf_dict_bips[fund] = tradegroup_performance_bips[tradegroup_performance_bips['Fund'] == fund].to_json(orient='records')
        as_of = tradegroup_performance_dollars['Date'].max()
    except ValueError:
        error = "No Data Found! Have you tried the legacy portal?"
        as_of = request.GET['as_of']
    return render(request, 'tradegroup_performance.html',
                  context={'tradegroup_performance_dollars': json.dumps(perf_dict),
                           'tradegroup_performance_bips': json.dumps(perf_dict_bips),
                           'as_of': as_of,
                           'error': error})


def get_tradegroup_story(request):
    """ Retrieve story charts and render in a template... """
    unique_tickers, tradegroup_name, exposures_and_pnl_df, fund_code = None, None, pd.DataFrame(), None
    options_pnl_contribution = {}
    tradegroup = request.GET['TradeGroup']
    fund = request.GET['Fund']
    tradegroup_overall_pnl = pd.read_sql_query("SELECT * FROM wic.tradegroup_overall_pnl where tradegroup "
                                               " like '"+tradegroup+"' and Fund like '"+fund+"'", con=connection)

    tradegroup_exposures_info = pd.read_sql_query("SELECT * FROM wic.tradegroup_exposure_nav_info where tradegroup "
                                                  " like '"+tradegroup+"' and Fund like '"+fund+"'", con=connection)

    if not tradegroup_overall_pnl.empty:
        tradegroup_overall_pnl = tradegroup_overall_pnl.sort_values(by='Date')
        tradegroup_overall_pnl['Cumulative_pnl_dollar'] = tradegroup_overall_pnl['Daily_PnL_Dollar'].cumsum()
        tradegroup_overall_pnl['Cumulative_pnl_bps'] = tradegroup_overall_pnl['Daily_PnL_bps'].cumsum()
        tradegroup_overall_pnl['Cumulative_options_pnl_dollar'] = tradegroup_overall_pnl['Options_PnL_Dollar'].cumsum()
        tradegroup_overall_pnl['Cumulative_options_pnl_bps'] = tradegroup_overall_pnl['Options_PnL_bps'].cumsum()
        tradegroup_overall_pnl['Cumulative_pnl_over_cap'] = 1e4*((1.0+(tradegroup_overall_pnl["PnL_Over_Cap_bps"].astype(float)/1e4)).cumprod() -1)
        tradegroup_overall_pnl['Pnl_over_cap_percent'] = tradegroup_overall_pnl['Cumulative_pnl_over_cap'].apply(lambda x: x/100.0)

        options_pnl_contribution['Options_PnL_Dollar'] = tradegroup_overall_pnl['Options_PnL_Dollar'].sum()
        options_pnl_contribution['Options_bps'] = tradegroup_overall_pnl['Options_PnL_bps'].sum()

        tradegroup_names = tradegroup_overall_pnl['TradeGroup'].unique()
        tradegroup_name = tradegroup_names[0] if tradegroup_names else None
        fund_codes = tradegroup_overall_pnl['Fund'].unique()
        fund_code = fund_codes[0] if fund_codes else None

    ticker_pnl_df = pd.read_sql_query("SELECT * FROM wic.ticker_pnl_breakdown where tradegroup "
                                      " like '" + tradegroup + "' and Fund like '" + fund + "'", con=connection)

    if not ticker_pnl_df.empty:
        ticker_pnl_df = ticker_pnl_df[['Date','Ticker_PnL_bps', 'Ticker_PnL_Dollar', 'Ticker']]
        security_pnl_breakdown = ticker_pnl_df.groupby('Ticker').sum().reset_index()
        security_pnl_breakdown = security_pnl_breakdown.append({'Ticker': 'Options',
                                                                'Ticker_PnL_bps': options_pnl_contribution['Options_bps'],
                                                                'Ticker_PnL_Dollar': options_pnl_contribution['Options_PnL_Dollar']},
                                                                ignore_index=True).to_dict('records')

        unique_tickers = list(ticker_pnl_df['Ticker'].unique())
        ticker_pnl_df = pd.pivot_table(ticker_pnl_df, index=['Date'], columns=['Ticker'],
                                       aggfunc='first', fill_value='')
        ticker_pnl_df.columns = ["_".join((i, j)) for i, j in ticker_pnl_df.columns]
        ticker_pnl_df.reset_index(inplace=True)
        ticker_pnl_df.columns = ticker_pnl_df.columns.str.replace(' ', '_')
        for column in ticker_pnl_df.columns:
            if column == 'Date': continue
            ticker_pnl_df[column] = ticker_pnl_df[column].apply(pd.to_numeric)
            ticker_pnl_df[column] = ticker_pnl_df[column].cumsum()

    if not tradegroup_overall_pnl.empty and not ticker_pnl_df.empty and not tradegroup_exposures_info.empty:
        tradegroup_story = pd.merge(tradegroup_overall_pnl, ticker_pnl_df, how='left', on='Date')
        tradegroup_story['Date'] = tradegroup_story['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        tradegroup_exposures_info['Date'] = tradegroup_exposures_info['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        exposures_and_pnl_df = pd.merge(tradegroup_exposures_info, tradegroup_story, on=['Date', 'Fund', 'TradeGroup'])
        exposures_and_pnl_df = exposures_and_pnl_df.sort_values(by='Date')

    # Get Position Summary Table
    position_summary = pd.read_sql_query("SELECT flat_file_as_of, Bucket, TradeGroup, Ticker, Strike, Expiration, "
                                         "Sector,AlphaHedge, CatalystTypeWIC, CatalystRating, amount, Exposure, "
                                         "DeltaAdj, BetaAdj from wic.daily_flat_file_db where "
                                         "Flat_file_as_of = (select max(flat_file_as_of) "
                                         "from wic.daily_flat_file_db) and TradeGroup like '"
                                         + tradegroup + "' and Fund like '" + fund + "'", con=connection)

    position_summary.columns = ['TradeDate', 'Bucket', 'TradeGroup', 'Ticker', 'Strike', 'Expiration', 'Sector',
                                'AlphaHedge', 'CatalystType', 'CatalystRating', 'Qty', 'Exposure', 'DeltaAdj',
                                'BetaAdj']
    position_summary = position_summary.to_dict('records')

    if request.is_ajax():
        return JsonResponse({'exposures_and_pnl_df': exposures_and_pnl_df.to_json(orient='records'),
                             'unique_tickers': json.dumps(unique_tickers)})

    return render(request, 'position_stats.html', {'unique_tickers': json.dumps(unique_tickers),
                                                   'tradegroup_name': tradegroup_name,
                                                   'fund_code': fund_code,
                                                   'exposures_and_pnl': exposures_and_pnl_df.to_json(orient='records'),
                                                   'position_summary': position_summary,
                                                   'security_pnl_breakdown': security_pnl_breakdown})


def get_tradegroup_attribution_over_own_capital(request):
    as_of = '(select max(`Date`)'
    error = ''
    perf_dict = {}
    volatility_distribution_charts = {}
    if 'as_of' in request.GET:
        as_of = "(SELECT " + "\'" + request.GET['as_of'] + "\'"

    try:
        tradegroup_performance_over_own_capital = pd.read_sql_query("SELECT * FROM "
                                                                    "wic.tradegroup_performance_over_own_capital WHERE "
                                                                    "`Date` = " + as_of +
                                                                    " FROM wic.tradegroup_performance_over_own_capital "
                                                                    "LIMIT 1)",
                                                                    con=connection)
        volatility_distribution_charts = pd.read_sql_query("SELECT vol_distribution_charts FROM "
                                                           "wic.volatility_distribution_timeseries WHERE"
                                                           "`Date`= " + as_of +
                                                           " FROM wic.volatility_distribution_timeseries LIMIT 1)",
                                                           con=connection)

        if not volatility_distribution_charts.empty:
            volatility_distribution_charts = volatility_distribution_charts['vol_distribution_charts'].iloc[0]
        else:
            volatility_distribution_charts = {}

        tradegroup_performance_over_own_capital['Date'] = tradegroup_performance_over_own_capital['Date'].\
            apply(lambda x: x.strftime('%Y-%m-%d'))
        tradegroup_performance_over_own_capital['InceptionDate'] = tradegroup_performance_over_own_capital['InceptionDate']\
            .apply(lambda x: x.strftime('%Y-%m-%d') if not pd.isna(x) else x)
        tradegroup_performance_over_own_capital['EndDate'] = tradegroup_performance_over_own_capital['EndDate'].\
            apply(lambda x: x.strftime('%Y-%m-%d') if not pd.isna(x) else x)

        def create_story_url(row):
            url = '../position_stats/get_tradegroup_story?'
            tg_fund = {'TradeGroup': row['TradeGroup'], 'Fund': row['Fund']}
            url = url + urlencode(tg_fund)
            return "<a target='_blank' href='"+url+"'>View</a>"

        tradegroup_performance_over_own_capital['story_url'] = tradegroup_performance_over_own_capital.apply(
            create_story_url, axis=1)

        perf_dict = {}
        for fund in tradegroup_performance_over_own_capital['Fund'].unique():
            perf_dict[fund] = tradegroup_performance_over_own_capital[
                tradegroup_performance_over_own_capital['Fund'] == fund].to_json(orient='records')
        as_of = tradegroup_performance_over_own_capital['Date'].max()
    except ValueError:
        error = "No Data available. Have you tried the legacy portal?"
        as_of = request.GET['as_of']

    return render(request, 'tradegroup_attribution_over_own.html', {'performance_over_own_capital':
                                                                    json.dumps(perf_dict),
                                                                    'volatility_distribution_charts':
                                                                    volatility_distribution_charts,
                                                                    'as_of': as_of,
                                                                    'error': error}
                  )