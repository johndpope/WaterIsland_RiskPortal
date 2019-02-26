import json
import pandas as pd
from django.shortcuts import render
from .models import ArbitrageYTDPerformance
from django_pandas.io import read_frame
from django.http import HttpResponse
import dbutils

# Create your views here.


def px_adjuster(bbg_sectype, northpoint_sectype, px, crncy, fx_rate, factor):
    if bbg_sectype == 'FORWARD' and crncy != 'USD': return factor*fx_rate*(1.0/px) if not pd.isnull(px) else None
    if northpoint_sectype == 'EQSWAP': return px*factor # don't fx eqswaps
    return px*factor*fx_rate


def live_tradegroup_pnl(request):

    """ Returns the Live PnL and YTD PnL at the Tradegroup level """
    ytd_performance = read_frame(ArbitrageYTDPerformance.objects.all())

    ytd_performance.columns = ['id', 'Fund', 'Sleeve','Catalyst', 'TradeGroup', 'LongShort', 'InceptionDate', 'EndDate', 'Status',
                               'YTD($)']
    del ytd_performance['id']

    assert len(ytd_performance) > 0
    all_portfolios_df = dbutils.Wic.get_live_pnl_monitored_portfolio_ids()
    portfolio_df = all_portfolios_df.copy()

    px_df = dbutils.Wic.get_live_pnl_df()
    px_df = px_df[px_df.PX_LAST.notnull()]
    px_factor_df = dbutils.Wic.get_live_pnl_px_factors_df()  # ['BBGID','CRNCY','FACTOR','FX_SYMBOL','DATA_TIMESTAMP']
    fx_df = dbutils.Wic.get_live_pnl_fx_rates_df()  # cols = ['Timestamp','FX_SYMBOL','FX_RATE']

    df = pd.merge(px_df, px_factor_df, how='inner', on='API_IDENTIFIER')
    df = pd.merge(df, fx_df, how='left', on=['FX_SYMBOL','Timestamp'])
    df = pd.merge(df, portfolio_df, how='inner',on='API_IDENTIFIER')


    df['FX_RATE'] = df['FX_RATE'].fillna(1) # Non FX_RATE is USD, rate = 1
    df['ADJ_PX'] = [px_adjuster(sectype,np_sectype,px,crncy,fx_rate,factor) for
                    (sectype,np_sectype,px,crncy,fx_rate,factor) in
                        zip(df['SECURITY_TYP'],df['NP_SecType'],df['PX_LAST'],df['CRNCY'],df['FX_RATE'],df['FACTOR'])]

    df['MktVal'] = df['ADJ_PX'].astype(float)*df['Qty'].astype(float)
    df['MktVal Chg Factor'] = [fx_rate if np_sectype == 'EQSWAP' else 1.0 for (fx_rate,np_sectype) in
                               zip(df['FX_RATE'],df['NP_SecType'])]
    float_cols = ['ADJ_PX','Qty','MktVal','Capital($)','Capital(%)','BaseCaseNavImpact','OutlierNavImpact']
    df[float_cols] = df[float_cols].astype(float)


    cols2include = ['Group', 'TradeGroup','TICKER','API_IDENTIFIER','ADJ_PX','Qty','MktVal','FX_RATE',
                        'Sleeve','Bucket','AlphaHedge','LongShort','CatalystName','Analyst','NP_SecType','Capital($)',
                        'Capital(%)','BaseCaseNavImpact','OutlierNavImpact']
    join_on_cols = ['Group','TradeGroup','API_IDENTIFIER','Sleeve','Bucket','AlphaHedge','LongShort','CatalystName',
                            'Analyst','NP_SecType']

    start_df = df[df['Timestamp']==df['Timestamp'].min()][cols2include].rename(
        columns={'ADJ_PX':'START_ADJ_PX','MktVal':'START_MKTVAL', 'FX_RATE':'START_FX_RATE'})
    end_df = df[df['Timestamp']==df['Timestamp'].max()][cols2include].rename(
        columns={'ADJ_PX':'END_ADJ_PX','MktVal':'END_MKTVAL', 'FX_RATE':'END_FX_RATE'})
    table_df = pd.merge(start_df, end_df, how='inner',on=join_on_cols)

    table_df['MKTVAL_CHG_USD'] = [(end_mktval-start_mktval)*end_fx_rate if np_sectype == 'EQSWAP' else
                                  (end_mktval-start_mktval) for (end_mktval, start_mktval, end_fx_rate,np_sectype) in
                                  zip(table_df['END_MKTVAL'],table_df['START_MKTVAL'],table_df['END_FX_RATE'],
                                      table_df['NP_SecType'])]
    table_df['PX_CHG_PCT'] = 100.0*((table_df['END_ADJ_PX'].astype(float)/table_df['START_ADJ_PX'].astype(float))-1.0)
    table_df = table_df[['Group', 'TradeGroup','START_ADJ_PX','END_ADJ_PX','PX_CHG_PCT','Qty_x','Analyst',
                          'Capital($)_x','Capital(%)_x', 'START_MKTVAL','END_MKTVAL','MKTVAL_CHG_USD']]

    table_df = table_df.groupby(['Group','TradeGroup']).sum().reset_index()
    ytd_performance['TradeGroup'] = ytd_performance['TradeGroup'].apply(lambda x: x.strip())
    ytd_performance.loc[ytd_performance['TradeGroup'] == 'BEL -  MC FP', ['TradeGroup']] = 'BEL - MC FP' # Todo: Update
    final_live_df = pd.merge(table_df, ytd_performance, how='outer', left_on=['Group','TradeGroup'], right_on=['Fund', 'TradeGroup'])

    final_live_df[['Fund']] = final_live_df[['Fund']].fillna('NA')
    final_live_df.fillna(0, inplace=True)
    final_live_df['YTD($)'] = final_live_df['YTD($)'].apply(round)
    final_live_df['MKTVAL_CHG_USD'] = final_live_df['MKTVAL_CHG_USD'].apply(round)

    final_live_df['Total YTD PnL'] = final_live_df['YTD($)'] + final_live_df['MKTVAL_CHG_USD']

    final_live_df['InceptionDate'] = final_live_df['InceptionDate'].apply(str)
    final_live_df['EndDate'] = final_live_df['EndDate'].apply(str)



    # final_live_df['Threshold I'] = final_live_df['Total YTD PnL'].apply(lambda x: 'Breached' if x < -500000 else 'Not Breached')
    # final_live_df['Threshold II'] = final_live_df['Total YTD PnL'].apply(lambda x: 'Breached' if x < -750000 else 'Not Breached')
    # final_live_df['Threshold III'] = final_live_df['Total YTD PnL'].apply(lambda x: 'Breached' if x < -1000000 else 'Not Breached')
    final_live_df = final_live_df[final_live_df['Fund'].isin(['ARB','AED','LG', 'MACO', 'TAQ', 'CAM',])]
    final_live_df = final_live_df[['Fund', 'TradeGroup','Sleeve', 'Catalyst', 'Total YTD PnL']]


    final_live_df = pd.pivot_table(final_live_df, index=['TradeGroup', 'Sleeve', 'Catalyst'], columns='Fund', fill_value=0).reset_index()
    final_live_df.columns = ["_".join((i, j)) for i, j in final_live_df.columns]
    final_live_df.reset_index(inplace=True)
    del final_live_df['index']


    if request.is_ajax():
        return_data = {'data':final_live_df.to_json(orient='records')}



        return HttpResponse(json.dumps(return_data), content_type='application/json')

    return render(request, 'realtime_pnl_impacts.html',{})
