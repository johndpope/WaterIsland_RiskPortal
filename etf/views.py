import pandas as pd
import numpy as np
import json
from django.shortcuts import render
from django.db import connection
from securities.models import SecurityMaster
from urllib.parse import urlencode
from django.http import HttpResponse, JsonResponse
# Create your views here.


def get_etf_positions(request):
    as_of = "(SELECT MAX(Flat_file_as_of) from wic.daily_flat_file_db)"
    if 'as_of' in request.GET:
        as_of = "'" + request.GET['as_of'] + "'"
    positions_df = SecurityMaster.objects.raw("SELECT 1 as id,flat_file_as_of, fund, Sleeve, Bucket, AlphaHedge, "
                                              "CatalystTypeWIC, CatalystRating, TradeGroup, Ticker, amount, Price, "
                                              "CurrentMktVal, aum, CurrentMktVal_Pct, CCY FROM "
                                              "wic.daily_flat_file_db where Fund like '%%ETF%%' and flat_file_as_of="+
                                              as_of)

    return render(request, 'etf_positions.html', {'etf_positions': positions_df})


def get_etf_performances(request):

    def get_tg_cum_pnl(row, y):
        current_tg = row
        cum_pnl_df = y[y['TradeGroup'] == current_tg]['pnl'].cumsum()
        try:
            value = cum_pnl_df.iloc[-1]
        except IndexError:
            value = 0
        return value

    def create_pnl_chart_url(row):
        url = '../etf/get_tradegroup_etf_pnl?'
        tg_fund = {'TradeGroup': row['TradeGroup'], 'Fund': row['Fund']}
        url = url + urlencode(tg_fund)
        return "<button class='btn btn-sm' data-url="+url+">View Line Graph </button>"

    perf_df = pd.read_sql_query("SELECT * FROM wic.tradegroups_pnl_cache where Fund like '%ETF%'",
                                con=connection)

    fund_aum_df = pd.read_sql_query("SELECT DISTINCT flat_file_as_of as `DATE`,Fund, `aum` FROM wic.daily_flat_file_db "
                                    , con=connection)

    tradegroups_pnl_df = pd.read_sql_query("SELECT `Date`, Fund, TradeGroup, pnl FROM wic.tradegroups_pnl_cache WHERE "
                                           "Fund LIKE '%ETF%' AND `Date` = (SELECT MAX(`Date`) FROM "
                                           "wic.tradegroups_pnl_cache)", con=connection)

    tg_perf_df = pd.read_sql_query("SELECT `date`,TradeGroup, Fund, `pnl` FROM wic.tradegroups_pnl_cache where "
                                   "Fund like '%ETF%' ", con=connection)

    pct_of_assets = pd.read_sql_query("SELECT DISTINCT flat_file_as_of as `Date`, TradeGroup, Fund, "
                                      "100*(CurrentMktVal / aum) AS "
                                      "`pct_of_assets` FROM wic.daily_flat_file_db WHERE Fund LIKE '%ETF%' AND "
                                      "Flat_file_as_of = (SELECT MAX(Flat_file_as_of) FROM "
                                      "wic.daily_flat_file_db)", con=connection)

    tg_perf_df['pnl'] = tg_perf_df['pnl'].apply(lambda x: int(float(x)))
    pct_of_assets['pct_of_assets'] = pct_of_assets['pct_of_assets'].apply(lambda x: str(np.round(x, decimals=2)) + "%")

    tradegroups_pnl_df = pd.merge(tradegroups_pnl_df, pct_of_assets, how='inner', on=['Date', 'TradeGroup', 'Fund'])

    tradegroups_pnl_df['Date'] = tradegroups_pnl_df['Date'].apply(str)
    tradegroups_pnl_df['pnl'] = tradegroups_pnl_df['pnl'].apply(lambda x: int(float(x)))

    tradegroups_pnl_df['pnl_chart_url'] = tradegroups_pnl_df.apply(create_pnl_chart_url, axis=1)

    perf_df = pd.merge(perf_df, fund_aum_df, on=['DATE', 'Fund'])
    perf_df['DATE'] = perf_df['DATE'].apply(str)
    # Remove CCY
    perf_df['pnl_bps'] = perf_df.apply(convert_to_bps, axis=1)
    perf_df = perf_df[perf_df['IsAllFromCCY'] != 1]
    del perf_df['IsAllFromCCY']
    del perf_df['cumpnl']
    del perf_df['aum']
    del perf_df['pnl']

    tradegroups_pnl_dict = {}

    fund_level_df = perf_df.groupby(['DATE', 'Fund']).agg('sum').reset_index()
    perf_dict = {}
    unique_funds = fund_level_df['Fund'].unique()
    for fund in unique_funds:
        fund_cum_pnl = fund_level_df[fund_level_df['Fund'] == fund]
        fund_cum_pnl['cum_pnl'] = fund_cum_pnl['pnl_bps'].cumsum()
        perf_dict[fund] = fund_cum_pnl.to_json(orient='records')
        tg_fund_perf = tg_perf_df[tg_perf_df['Fund'] == fund]
        tradegroups_df = tradegroups_pnl_df[tradegroups_pnl_df['Fund'] == fund]
        tradegroups_df['cum_pnl'] = tradegroups_df['TradeGroup'].apply(lambda x: get_tg_cum_pnl(x, tg_fund_perf))
        tradegroups_pnl_dict[fund] = tradegroups_df.to_json(orient='records')

    return render(request, 'etf_performances.html', {'fund_level_performance': fund_level_df.to_json(orient='records'),
                                                     'etf_cum_pnl': json.dumps(perf_dict),
                                                     'tradegroups_pnl': json.dumps(tradegroups_pnl_dict)
                                                     })


def get_tradegroup_etf_pnl(request):
    fund = request.GET['Fund']
    tradegroup = request.GET['TradeGroup']

    tg_perf_df = pd.read_sql_query("SELECT `date`, `pnl` FROM wic.tradegroups_pnl_cache where "
                                   "Fund like '"+fund+"' AND TradeGroup like '"+tradegroup+"'", con=connection)

    fund_aum_df = pd.read_sql_query("SELECT DISTINCT flat_file_as_of as `date`, `aum` FROM wic.daily_flat_file_db where "
                                    "Fund like '"+fund+"'", con=connection)

    tg_perf_df = pd.merge(tg_perf_df, fund_aum_df, how='inner', on=['date'])
    tg_perf_df['pnl'] = tg_perf_df.apply(convert_to_bps, axis=1)
    tg_perf_df['date'] = tg_perf_df['date'].apply(str)
    tg_perf_df['cum_pnl'] = tg_perf_df['pnl'].cumsum()

    return HttpResponse(tg_perf_df.to_json(orient='records'))


def convert_to_bps(row):
        return 1e4*(float(row['pnl'])/float(row['aum']))