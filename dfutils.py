import itertools
import pandas as pd
import numpy as np
import math
import datetime
import dbutils

def round_df(df, cln2decimal_pts=None, color=True):
    def default_rounder(val):
        try:
                if 0<abs(float(val))<0.1: decimal_points=3
                if 0.1<=abs(float(val))<1: decimal_points=2
                if 1<=abs(float(val))<100: decimal_points=1
                if abs(float(val))>100: decimal_points=0
                res = round(float(val),decimal_points) if decimal_points > 0 else int(val)
                res = format_and_color(res)
        except:
            res = val
        return res

    def rounder(val,digits):
        try:
            res = round(float(val),digits) if digits > 0 else int(val)
            res = format_and_color(res)
        except:
            res = val

        return res

    def format_and_color(val):
        try:
            if not color:
                return  "{:,}".format(val)
            if val >= 0:
                return "<font color=\"green\">" + "{:,}".format(val) + "</font>"
            return "<font color=\"red\">" + "{:,}".format(val) + "</font>"
        except:
            return str(val)

    if cln2decimal_pts is None:
        for cln in df.columns:
            df[cln] = df[cln].apply(lambda x: default_rounder(x))
        return df

    for cln in df.columns:
        df[cln] = df[cln].apply(lambda x: x if cln not in cln2decimal_pts else rounder(x,cln2decimal_pts[cln]))
    return df

def df2json(df,decimal_pts=1):
    try:
        data = [[((datetime.datetime.strptime(str(df.ix[idx][df.columns[0]]) + " 00:00:00", '%Y-%m-%d %H:%M:%S')) - datetime.datetime(1970, 1,1)).total_seconds() * 1000, round(float(df.ix[idx][df.columns[1]]),decimal_pts)] for idx in df.index]
    except:
        try:
            data = [[((datetime.datetime.strptime(str(df.ix[idx][df.columns[0]]) + " 00:00:00", '%m-%d-%Y %H:%M:%S')) - datetime.datetime(1970, 1,1)).total_seconds() * 1000, round(float(df.ix[idx][df.columns[1]]),decimal_pts)] for idx in df.index]
        except:
            try:
                data = [[((datetime.datetime.strptime(str(df.ix[idx][df.columns[0]]), '%Y-%m-%d %H:%M:%S')) - datetime.datetime(1970, 1,1)).total_seconds() * 1000, round(float(df.ix[idx][df.columns[1]]),decimal_pts)] for idx in df.index]
            except:
                data=""
    return data


## receives a pcvh dataframe with columns {Date, AlphaHedge, Exposure_Net,NetMktVal}
# and calculates {Exposure,NetMktVal,GrossMktVal} for  {alpha,alphahedge,hedge,bet,total}
## where bet = alpha+alphahedge and total = alpha+alphahedge+hedge
def mktval_df(pcvh_df):
    float_cols = ['Alpha Exposure','AlphaHedge Exposure','Hedge Exposure',
                  'Alpha NetMktVal', 'AlphaHedge NetMktVal','Hedge NetMktVal',
                  'Alpha GrossMktVal','AlphaHedge GrossMktVal','Hedge GrossMktVal',
                  'Alpha GrossExp','AlphaHedge GrossExp','Hedge GrossExp'
                  ]
    calc_cols = ['Bet Exposure','Bet NetMktVal','Bet GrossMktVal','Total NetExposure','Total NetMktVal','Total GrossMktVal',]

    if len(pcvh_df) == 0: return pd.DataFrame(columns=["Date"]+float_cols+calc_cols)

    alpha_pcvh = pcvh_df[pcvh_df['AlphaHedge']=='Alpha']
    alphahedge_pcvh = pcvh_df[pcvh_df['AlphaHedge']=='Alpha Hedge']
    hedge_pcvh = pcvh_df[pcvh_df['AlphaHedge']=='Hedge']

    alpha_net_exp = alpha_pcvh[['Date','Exposure_Net']].groupby('Date').sum().reset_index().rename(columns={'index':'Date', 'Exposure_Net':'Alpha Exposure'})
    alpha_net_mv = alpha_pcvh[['Date','NetMktVal']].groupby('Date').sum().reset_index().rename(columns={'index':'Date', 'NetMktVal':'Alpha NetMktVal'})
    alpha_gross_mv = alpha_pcvh[['Date','NetMktVal']].groupby('Date').agg(lambda x: sum(abs(x))).reset_index().rename(columns={'index':'Date', 'NetMktVal':'Alpha GrossMktVal'})
    alpha_gross_exp = alpha_pcvh[['Date','Exposure_Net']].groupby('Date').agg(lambda x: sum(abs(x))).reset_index().rename(columns={'index':'Date', 'Exposure_Net':'Alpha GrossExp'})

    alphahedge_net_exp = alphahedge_pcvh[['Date','Exposure_Net']].groupby('Date').sum().reset_index().rename(columns={'index':'Date', 'Exposure_Net':'AlphaHedge Exposure'})
    alphahedge_net_mv = alphahedge_pcvh[['Date','NetMktVal']].groupby('Date').sum().reset_index().rename(columns={'index':'Date', 'NetMktVal':'AlphaHedge NetMktVal'})
    alphahedge_gross_mv = alphahedge_pcvh[['Date','NetMktVal']].groupby('Date').agg(lambda x: sum(abs(x))).reset_index().rename(columns={'index':'Date', 'NetMktVal':'AlphaHedge GrossMktVal'})
    alphahedge_gross_exp = alphahedge_pcvh[['Date','Exposure_Net']].groupby('Date').agg(lambda x: sum(abs(x))).reset_index().rename(columns={'index':'Date', 'Exposure_Net':'AlphaHedge GrossExp'})

    hedge_net_exp = hedge_pcvh[['Date','Exposure_Net']].groupby('Date').sum().reset_index().rename(columns={'index':'Date','Exposure_Net':'Hedge Exposure'})
    hedge_net_mv = hedge_pcvh[['Date','NetMktVal']].groupby('Date').sum().reset_index().rename(columns={'index':'Date', 'NetMktVal':'Hedge NetMktVal'})
    hedge_gross_mv = hedge_pcvh[['Date','NetMktVal']].groupby('Date').agg(lambda x: sum(abs(x))).reset_index().rename(columns={'index':'Date', 'NetMktVal':'Hedge GrossMktVal'})
    hedge_gross_exp = hedge_pcvh[['Date','Exposure_Net']].groupby('Date').agg(lambda x: sum(abs(x))).reset_index().rename(columns={'index':'Date', 'Exposure_Net':'Hedge GrossExp'})

    mktval_df=pd.merge(alpha_net_exp, alphahedge_net_exp, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, hedge_net_exp, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, alpha_net_mv, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, alphahedge_net_mv, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, hedge_net_mv, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, alpha_gross_mv, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, alphahedge_gross_mv, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, hedge_gross_mv, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, alpha_gross_exp, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, alphahedge_gross_exp, how='outer', on=['Date']).fillna(0)
    mktval_df=pd.merge(mktval_df, hedge_gross_exp, how='outer', on=['Date']).fillna(0)

    mktval_df[float_cols] = mktval_df[float_cols].astype(float)
    mktval_df['Bet Exposure'] = mktval_df['Alpha Exposure'] + mktval_df['AlphaHedge Exposure']
    mktval_df['Bet NetMktVal'] = mktval_df['Alpha NetMktVal'] + mktval_df['AlphaHedge NetMktVal']
    mktval_df['Bet GrossMktVal'] = mktval_df['Alpha GrossMktVal'] + mktval_df['AlphaHedge GrossMktVal']
    mktval_df['Total NetExposure'] = mktval_df['Alpha Exposure'] + mktval_df['AlphaHedge Exposure'] + mktval_df['Hedge Exposure']
    mktval_df['Total GrossExposure'] = mktval_df['Alpha GrossExp'] + mktval_df['AlphaHedge GrossExp'] + mktval_df['Hedge GrossExp']
    mktval_df['Total NetMktVal'] = mktval_df['Alpha NetMktVal'] + mktval_df['AlphaHedge NetMktVal'] + mktval_df['Hedge NetMktVal']
    mktval_df['Total GrossMktVal'] = mktval_df['Alpha GrossMktVal'] + mktval_df['AlphaHedge GrossMktVal'] + mktval_df['Hedge GrossMktVal']


    return mktval_df.sort_values(by='Date')

def exposure_df(as_of_yyyy_mm_dd=None):
    try:
        if as_of_yyyy_mm_dd is None:
            as_of_yyyy_mm_dd = dbutils.northpoint.get_position_calculated_values_history_max_date()

        if datetime.datetime.strptime(as_of_yyyy_mm_dd,'%Y-%m-%d') < datetime.datetime(2015,11,9,0,0): return None

        fund_code2name =  dbutils.northpoint.get_fund_code2name()
        pcvh_df = dbutils.northpoint.get_position_calculated_values_history(as_of_yyyy_mm_dd,as_of_yyyy_mm_dd)
        pcvh_df = pcvh_df[pcvh_df['Sleeve'] != 'Forwards']
        timestamp, risk_df = dbutils.wic.get_risk_snapshot(position_date_yyyy_mm_dd=as_of_yyyy_mm_dd)
        risk_df = risk_df[risk_df['Sleeve'] != 'Forwards']

        funds = ['ARB','AED','CAM','WED','LEV','TACO','LG','TAQ','MACO','MALT'] #Added (KG)
        tab2body_tuple_list = []
        df = pd.DataFrame()
        for fund_code in funds:
            fund_pcvh_df = pcvh_df[pcvh_df['FundCode']==fund_code].copy()
            fund_risk_df = risk_df[risk_df['FundCode']==fund_code].copy()
            if len(fund_pcvh_df) == 0:
                tab2body_tuple_list.append((fund_code,"<h9>EMPTY POSITION DATA FOR "+fund_code+"</h9>"))
                continue

            fund_nav_df = dbutils.northpoint.get_NAV_df(fund_code2name[fund_code])
            fund_navs = fund_nav_df[fund_nav_df['Date'] == as_of_yyyy_mm_dd]['NAV'].values
            if len(fund_navs) != 1:
                tab2body_tuple_list.append((fund_code,"<h9>BAD NAV DATA FOR "+as_of_yyyy_mm_dd+"</h9>"))
                continue
            fund_nav = fund_navs[0]

            net_exp_df = fund_pcvh_df[['LongShort','Sleeve','TradeGroup','Exposure_Net','Bucket']].groupby(['LongShort','Sleeve','TradeGroup','Bucket']).sum().reset_index().rename(columns={'Exposure_Net':'Net Exposure'})
            gross_exp_df = fund_pcvh_df[['LongShort','Sleeve','TradeGroup','Exposure_Net','Bucket']].groupby(['LongShort','Sleeve','TradeGroup','Bucket']).agg(lambda x: sum(abs(x))).reset_index().rename(columns={'Exposure_Net':'Gross Exposure'})
            alpha_exp_df = fund_pcvh_df[fund_pcvh_df['AlphaHedge'].isin(['Alpha','Alpha Hedge'])][['LongShort','Sleeve','TradeGroup','Exposure_Net','Bucket']].groupby(['LongShort','Sleeve','TradeGroup','Bucket']).sum().reset_index().rename(columns={'Exposure_Net':'Alpha Exposure'})
            hedge_exp_df = fund_pcvh_df[fund_pcvh_df['AlphaHedge'].isin(['Hedge'])][['LongShort','Sleeve','TradeGroup','Exposure_Net','Bucket']].groupby(['LongShort','Sleeve','TradeGroup','Bucket']).sum().reset_index().rename(columns={'Exposure_Net':'Hedge Exposure'})
            capital_df = fund_pcvh_df[fund_pcvh_df['AlphaHedge'].isin(['Alpha','Alpha Hedge'])][['LongShort','Sleeve','TradeGroup','NetMktVal','Bucket']].groupby(['LongShort','Sleeve','TradeGroup','Bucket']).agg(lambda x: sum(abs(x))).reset_index().rename(columns={'NetMktVal':'Capital'})
            directional_exp_df = fund_risk_df[['LongShort','Sleeve','TradeGroup','Bucket','Equity DeltaExp(%)','Adj_CR01(bps)','DV01(bps)']].groupby(['LongShort','Sleeve','TradeGroup','Bucket']).sum().reset_index().rename(columns={'Equity DeltaExp(%)':'Directional Equity Risk', 'Adj_CR01(bps)':'Directional Credit Risk(bps)', 'DV01(bps)': 'Directional IR Risk(bps)'})
            #directional_exp_df = fund_pcvh_df[['LongShort','Sleeve','TradeGroup','Bucket','Equity_Risk_Exp','DV01','CR01','Adj_CR01']].groupby(['LongShort','Sleeve','TradeGroup','Bucket']).sum().reset_index().rename(columns={'Equity_Risk_Exp':'Directional Equity Risk', 'Adj_CR01':'Directional Credit Risk(bps)', 'DV01': 'Directional IR Risk(bps)' })

            f_exp_df = pd.DataFrame(columns=['Sleeve','TradeGroup','LongShort','Bucket'])
            if len(net_exp_df) > 0:f_exp_df = pd.merge(f_exp_df,net_exp_df,how='outer', on=['Sleeve','TradeGroup','LongShort','Bucket'])
            if len(gross_exp_df) > 0:f_exp_df = pd.merge(f_exp_df,gross_exp_df,how='outer', on=['Sleeve','TradeGroup','LongShort','Bucket'])
            if len(alpha_exp_df) > 0: f_exp_df = pd.merge(f_exp_df,alpha_exp_df,how='outer', on=['Sleeve','TradeGroup','LongShort','Bucket'])
            if len(hedge_exp_df) > 0: f_exp_df = pd.merge(f_exp_df,hedge_exp_df,how='outer', on=['Sleeve','TradeGroup','LongShort','Bucket'])
            if len(capital_df) > 0: f_exp_df = pd.merge(f_exp_df,capital_df,how='outer', on=['Sleeve','TradeGroup','LongShort','Bucket'])
            if len(directional_exp_df) > 0: f_exp_df = pd.merge(f_exp_df,directional_exp_df,how='outer', on=['Sleeve','TradeGroup','LongShort','Bucket'])

            f_exp_df['Alpha Exposure'] = 100.0*(f_exp_df['Alpha Exposure'].astype(float)/fund_nav) if 'Alpha Exposure' in f_exp_df.columns else None
            f_exp_df['Hedge Exposure'] = 100.0*(f_exp_df['Hedge Exposure'].astype(float)/fund_nav) if 'Hedge Exposure' in f_exp_df.columns else None
            f_exp_df['Net Exposure'] = 100.0*(f_exp_df['Net Exposure'].astype(float)/fund_nav) if 'Net Exposure' in f_exp_df.columns else None
            f_exp_df['Gross Exposure'] = 100.0*(f_exp_df['Gross Exposure'].astype(float)/fund_nav) if 'Gross Exposure' in f_exp_df.columns else None
            f_exp_df['Capital'] = 100.0*(f_exp_df['Capital'].astype(float)/fund_nav) if 'Capital' in f_exp_df.columns else None
            f_exp_df['Date'] = as_of_yyyy_mm_dd
            f_exp_df['Fund'] = fund_code

            df = df.append(f_exp_df)

        return df[['Date', 'Fund','LongShort', 'Sleeve', 'TradeGroup', 'Bucket', 'Net Exposure',
                  'Gross Exposure', 'Alpha Exposure', 'Hedge Exposure', 'Capital',
                  'Directional Equity Risk', 'Directional Credit Risk(bps)',
                  'Directional IR Risk(bps)']]
    except Exception as e:
        msg = '' if e.message is None else e.message
        print('Failed calculating dfutils.exposure_df')
        print(msg)
        return pd.DataFrame(columns=['Date', 'Fund','LongShort', 'Sleeve', 'TradeGroup', 'Bucket', 'Net Exposure',
                                     'Gross Exposure', 'Alpha Exposure', 'Hedge Exposure', 'Capital',
                                     'Directional Equity Risk', 'Directional Credit Risk(bps)',
                                     'Directional IR Risk(bps)'])

def perf_timeseries_df(pnl_df, capital_df, as_of_date=None, calc_stats=True, periods=('MTD','QTD','YTD','ITD',"1D","3D","5D","30D")):
    empty_stats_df = pd.DataFrame(columns=["Period",'P&L($)','P&L(bps)','ROMC(bps)', 'ANN. VOL','CAPITAL($)','CAPITAL CHG(%)'])
    empty_stats_df["Period"] = periods
    empty_perf_df = pd.DataFrame(columns=pnl_df.columns)
    empty_res = (empty_perf_df, empty_stats_df) if calc_stats else empty_perf_df
    if len(pnl_df) == 0 or len(pnl_df[pd.isnull(pnl_df['Total P&L'])])>0: return empty_res

    # pnl data present. at least calculate p&l cumsum
    slicer = df_slicer(as_of_date)
    empty_stats_df['P&L($)'] = [None if len(sliced_df) == 0 else sliced_df['Total P&L'].sum() for (period,sliced_df) in zip(periods, [slicer.slice(pnl_df,p) for p in periods])]

    if capital_df is None: return empty_res
    if len(capital_df) == 0 or len(capital_df.columns) <= 1: return empty_res
    if len(capital_df[pd.isnull(capital_df[capital_df.columns[1]])])>0: return empty_res

    capital_cln = capital_df.columns[1]
    capital_df_cpy = capital_df.copy() # don't change capital_df. work on its copy
    capital_df_cpy['Capital'] = capital_df_cpy[capital_cln]
    capital_df_cpy['Shifted Capital'] = capital_df_cpy[capital_cln].shift(1)

    df = pd.merge(pnl_df, capital_df_cpy, how='left', on=['Date']).sort_values(by='Date') #assuming NAV's first element is removed here





    if pd.isnull(df['Shifted Capital'].iloc[0]): df.loc[0,'Shifted Capital'] = df['Capital'].iloc[0] # adjust null-starting shift
    df['Shifted Capital'] = df['Shifted Capital'].apply(lambda x: np.nan if x == 0 else x)
    # if pd.isna(df['Shifted Capital'].iloc[1]):
    #     print('Updating Shifted capital')
    #     df['Shifted Capital'].loc[1] = df['Capital'].loc[1]
    #
    df['Shifted Forward-Filled Capital'] = df['Shifted Capital'].ffill()
    # if pd.isna(df['Shifted Forward-Filled Capital'].iloc[1]):
    #     print('Updating Shifted Forward-filled Capital')
    #     df['Shifted Forward-Filled Capital'].loc[1] = df['Capital'].loc[1]
    try:
        if df['Fund'].iloc[0] == 'MACO':   # Temp Fix for MACO
            df['Shifted Capital'].iloc[1] = df['Capital'].iloc[1]
            df['Shifted Forward-Filled Capital'].iloc[1] = df['Capital'].iloc[1]
        # df.drop(df.index[0], inplace=True)
        #df.to_csv('TEMPDF-aprl3.csv')

    except Exception as err:
        print(err)
        print('Fund not found in Dataframe')

    df["P&L bps (ffiled)"] = 1e4*(df["Total P&L"]/df["Shifted Forward-Filled Capital"]).replace([np.inf, -np.inf], np.nan)
    df["Cumulative P&L ($)"] = df["Total P&L"].cumsum()
    df["Cumulative P&L bps (ffiled)"] = 1e4*((1.0+(df["P&L bps (ffiled)"].astype(float)/1e4)).cumprod() -1)
    df['Rolling 30D Vol(%)'] = math.sqrt(252)*pd.rolling_std(df['P&L bps (ffiled)'],window=30)/100.0
    df['Rolling 60D Vol(%)'] = math.sqrt(252)*pd.rolling_std(df['P&L bps (ffiled)'],window=60)/100.0
    df['Rolling 90D Vol(%)'] = math.sqrt(252)*pd.rolling_std(df['P&L bps (ffiled)'],window=90)/100.0
    if not calc_stats: return df

    # calc stats
    stats_df = pd.DataFrame(columns=["Period",'P&L($)','P&L(bps)','ROMC(bps)','ANN. VOL','CAPITAL($)','CAPITAL CHG(%)'])

    for period in periods:
        p_df = slicer.slice(df, period)
        next_idx = 0 if pd.isnull(stats_df.index.max()) else stats_df.index.max()+1
        if len(p_df)==0:
            stats_df.loc[next_idx] = [period,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]
            continue

        rets = p_df["P&L bps (ffiled)"].astype(float)
        vol_pct = math.sqrt(252)*np.std(rets/1e4, ddof=1)*1e2
        cumpnl_usd = p_df['Total P&L'].sum()
        cumret_bps = ((1+rets/1e4).prod() -1)*1e4
        capitals = p_df['Shifted Forward-Filled Capital'].fillna(0).astype(float)
        mean_capital = capitals.mean()
        if mean_capital == 0:
            stats_df.loc[next_idx] = [period,cumpnl_usd,cumret_bps,np.nan,vol_pct,np.nan,np.nan]
            continue
        #mw_rets = (rets/1e4)*(capitals/mean_capital)
        #romwc_bps = ((1+mw_rets).prod() -1)*1e4
        romc_bps = 1e4*(cumpnl_usd/mean_capital)
        capital_usd = capitals.iloc[-1]
        capital_chg_pct = 1e2*((capitals.iloc[-1]/capitals.iloc[0])-1.0) if capitals.iloc[0] != 0 else np.nan
        stats_df.loc[next_idx] = [period,cumpnl_usd,cumret_bps,romc_bps,vol_pct,capital_usd,capital_chg_pct]
    return df, stats_df

def df2row(pivot_col, df):
    dfcols = [c for c in df.columns if c != pivot_col]
    cols = [colname+'|'+period for (colname,period) in itertools.product(dfcols,df[pivot_col])]
    cols2vals = {c:None for c in cols}

    for idx in df.index:
        row = df.ix[idx]
        pivot = row[pivot_col]
        for cln in dfcols:
            key = cln+'|'+pivot
            cols2vals[key] = row[cln]
    res = pd.Series()
    for cln in cols:
        res[cln] = cols2vals[cln]
    return res

def json2row(json):
    df = pd.read_json(json)
    return df2row('Period',df)

def df2hist(values, values_rng):
    df = pd.DataFrame()
    df['values'] = values
    df = df.groupby('values').size().reset_index().rename(columns={0:'Count'})
    df2 = pd.DataFrame()
    df2['values'] = [round(v,2) for v in values_rng]
    hist_df = pd.merge(df,df2,on='values',how='right').fillna(0)
    hist_df['Probability'] = 100.0*(hist_df['Count']/hist_df['Count'].sum())
    return hist_df[['values','Probability']].sort_values(by='values')

def format_df(df, cln2decimal_point={}):
    if len(cln2decimal_point) == 0 or len(df) == 0: return df
    cpy_df = df.copy()
    color = lambda x: "'green'" if x >= 0 else "'red'"
    rounder = lambda x,dec: int(x) if dec == 0 else round(x,dec)
    for cln in cln2decimal_point:
        cpy_df[cln] = cpy_df[cln].apply(lambda x: "<font color="+color(x)+"><center>" + '{0:,}'.format(rounder(x,cln2decimal_point[cln])) + "</center></font>" if not pd.isnull(x) else '<center>-</center>')
    # for cln in cpy_df.columns:
    #     cpy_df[cln] = cpy_df[cln].apply(lambda x: "<center>"+('-' if pd.isnull(x) else str(x))+"</center>")

    return cpy_df

def diff_merge(df1,df2,merge_on_cols, diff_cols,merge_how='outer', diff_col2highlighting_fn={}, diff_col2decimal_pts={}):
    cols = merge_on_cols + diff_cols
    df = pd.merge(df1,df2,how=merge_how,on=merge_on_cols)

    if len(df) == 0: return pd.DataFrame(columns=cols)
    formatter = lambda x: '' if pd.isnull(x) else str(x)
    for col in diff_cols:
        rnd_fn = (lambda x: x) if col not in diff_col2decimal_pts else lambda x: (round(float(x),diff_col2decimal_pts[col]) if diff_col2decimal_pts[col]>0 else (int(float(x)) if not pd.isnull(x) else x))
        highlighting_fn = (lambda x: False) if col not in diff_col2highlighting_fn else lambda x: diff_col2highlighting_fn[col](x)
        df[col] = [formatter(rnd_fn(l))+' ('+formatter(rnd_fn(r))+ ')' for (l,r) in zip(df[col+'_x'],df[col+'_y'])]
        df[col] = [('<b>'+parsed_l+'</b>') if highlighting_fn(l) else parsed_l for (parsed_l,l) in zip(df[col],df[col+'_x'])]
        del df[col+'_x']; del df[col+'_y']

    return df

def center_df(df,float_cols):
    w_df = df.copy()
    for c in [cln for cln in w_df.columns if cln not in float_cols]:
        w_df[c] = w_df[c].apply(lambda x: "<center>"+(str(x) if not pd.isnull(x) else "")+"</center>")
    return w_df


def unjsonify_snapshot_to_nav_contr_df(snapshot_df, fund_code):
    metrics_cln = 'Metrics in NAV JSON'
    metrics2include = [('P&L(bps)', 'ITD'), ('P&L($)', 'ITD'),
                       ('P&L(bps)', 'YTD'), ('P&L($)', 'YTD'),
                       ('P&L(bps)', 'QTD'), ('P&L($)', 'QTD'),
                       ('P&L(bps)', 'MTD'), ('P&L($)', 'MTD'),
                       ('P&L(bps)', '5D'), ('P&L($)', '5D'),
                       ('P&L(bps)', '1D'), ('P&L($)', '1D')]

    metric2display_name = {'P&L(bps)': '', 'P&L($)': ''}
    metric2unit = {'P&L(bps)': 'bps', 'P&L($)': '$'}
    # endregion

    f_df = snapshot_df[snapshot_df['Fund'] == fund_code].copy()
    if len(f_df) == 0: return pd.DataFrame()
    metrics_df = pd.DataFrame([json2row(json) for json in f_df[metrics_cln]]) # unjsonify metrics, and append columns
    metrics_df.index = f_df.index
    cln2decimal_pts = {}
    colnames_to_sum = []
    display_columns = []
    for (metric, period) in metrics2include:
        unit = metric2unit[metric]
        disp_name = metric2display_name[metric]
        display_colname = disp_name + ' ' + period + '(' + unit + ')'
        f_df[display_colname] = metrics_df[metric + '|' + period]
        if unit == '$':
            cln2decimal_pts[display_colname] = 0
            colnames_to_sum.append(display_colname)
        if unit == 'bps':
            cln2decimal_pts[display_colname] = 1
            colnames_to_sum.append(display_colname)
        if unit == '%': cln2decimal_pts[display_colname] = 2
        display_columns.append(display_colname)

    del f_df['Metrics in NAV JSON'];
    del f_df['Metrics in Bet JSON'];
    del f_df['Metrics in NAV notes JSON'];
    del f_df['Metrics in Bet notes JSON']
    f_df = f_df[(~pd.isnull(f_df[' YTD($)']))]  # don't show null ytds
    f_df.sort_values(by=' YTD($)', inplace=True)
    return f_df


def unjsonify_snapshot_to_roc_df(snapshot_df, fund_code):
    metrics_cln = 'Metrics in Bet JSON'

    # region formatting configuration
    metrics2include = [('P&L(bps)', 'ITD'), ('P&L(bps)', 'YTD'), ('ROMC(bps)', 'YTD'), ('P&L(bps)', 'MTD'),
                       ('ROMC(bps)', 'MTD'), ('P&L(bps)', '5D'), ('P&L(bps)', '1D'),
                       ('P&L($)', 'ITD'),('P&L($)', 'YTD'), ('P&L($)', 'MTD'),('P&L($)', '5D'), ('P&L($)', '1D'),
                       ('ANN. VOL', '30D'),('CAPITAL($)', '1D')]
    metric2display_name = {'P&L(bps)': '', 'P&L($)': '', 'ANN. VOL': 'VOL',
                           'ROMC(bps)':'ROMC', 'CAPITAL($)':'CAPITAL'}
    metric2unit = {'P&L(bps)': 'bps', 'P&L($)': '$', 'ANN. VOL': '%',
                   'ROMC(bps)': 'bps', 'CAPITAL($)':'%'} # will transform capital from $ to % later
    # endregion

    f_df = snapshot_df[snapshot_df['Fund'] == fund_code].copy()
    if len(f_df) == 0: return pd.DataFrame()
    metrics_df = pd.DataFrame([json2row(json) for json in f_df[metrics_cln]]) # unjsonify metrics, and append columns
    metrics_df.index = f_df.index
    cln2decimal_pts = {}
    colnames_to_sum = []
    display_columns = []
    for (metric, period) in metrics2include:
        unit = metric2unit[metric]
        disp_name = metric2display_name[metric]
        display_colname = disp_name + ' ' + period + '(' + unit + ')'
        f_df[display_colname] = metrics_df[metric + '|' + period]
        if unit == '$':
            cln2decimal_pts[display_colname] = 0
            colnames_to_sum.append(display_colname)
        if unit == 'bps':
            cln2decimal_pts[display_colname] = 1
            colnames_to_sum.append(display_colname)
        if unit == '%': cln2decimal_pts[display_colname] = 2
        display_columns.append(display_colname)

    f_nav = dbutils.northpoint.get_NAV_df2(fund_code)
    f_curr_nav = f_nav['NAV'].iloc[-1]
    f_df['CAPITAL 1D(%)'] = [np.nan if status == 'CLOSED' else 1e2*(cap_usd/f_curr_nav) for (cap_usd,status) in zip(f_df['CAPITAL 1D(%)'],f_df['Status'])]

    del f_df['Metrics in NAV JSON'];
    del f_df['Metrics in Bet JSON'];
    del f_df['Metrics in NAV notes JSON'];
    del f_df['Metrics in Bet notes JSON']
    f_df = f_df[(~pd.isnull(f_df[' YTD($)']))]  # don't show null ytds
    f_df.sort_values(by=' YTD($)', inplace=True)
    return f_df

def unjsonify_snapshot_df(snapshot_df, fund_code):
    contr_df = unjsonify_snapshot_to_nav_contr_df(snapshot_df,fund_code)
    roc_df = unjsonify_snapshot_to_roc_df(snapshot_df, fund_code)

    contr_df = contr_df.rename(columns={' ITD(bps)': 'NAV ITD(bps)', ' YTD(bps)':'NAV YTD(bps)',
                                        ' MTD(bps)': 'NAV MTD(bps)', ' 5D(bps)':'NAV 5D(bps)',
                                        ' QTD(bps)': 'NAV QTD(bps)', ' 1D(bps)':'NAV 1D(bps)'})

    roc_df = roc_df.rename(columns={' ITD(bps)': 'ROC ITD(bps)', ' YTD(bps)':'ROC YTD(bps)',
                                    ' MTD(bps)': 'ROC MTD(bps)', ' 5D(bps)':'ROC 5D(bps)',
                                    ' 1D(bps)':'ROC 1D(bps)'})

    df = pd.merge(contr_df, roc_df, how='inner', on=['Fund', 'Sleeve', 'TradeGroup', 'Analyst', 'InceptionDate','EndDate', 'Status'])
    df = df.rename(columns={' ITD($)_x':'ITD($)',' YTD($)_x':'YTD($)',' QTD($)':'QTD($)',
                            ' MTD($)_x':'MTD($)',' 5D($)_x':'5D($)',' 1D($)_x':'1D($)'})

    cols2include = ['Fund', 'Sleeve', 'TradeGroup', 'Analyst', 'InceptionDate','EndDate', 'Status',
                    'NAV ITD(bps)','ROC ITD(bps)',
                    'NAV YTD(bps)','ROC YTD(bps)','ROMC YTD(bps)',
                    'NAV QTD(bps)',
                    'NAV MTD(bps)','ROC MTD(bps)','ROMC MTD(bps)',
                    'NAV 5D(bps)','ROC 5D(bps)',
                    'NAV 1D(bps)','ROC 1D(bps)',
                    'ITD($)', 'YTD($)',
                    'QTD($)', 'MTD($)',
                    '5D($)', '1D($)',
                    'VOL 30D(%)', 'CAPITAL 1D(%)']

    return df[cols2include]

    # contr_cols = ['Fund', 'Sleeve', 'TradeGroup', 'Analyst', 'InceptionDate','EndDate', 'Status',
    #               ' ITD(bps)', ' ITD($)', ' YTD(bps)',' YTD($)',
    #               ' QTD(bps)', ' QTD($)', ' MTD(bps)', ' MTD($)',
    #               ' 5D(bps)', ' 5D($)', ' 1D(bps)', ' 1D($)']
    #
    # roc_cols = ['Fund', 'Sleeve', 'TradeGroup', 'Analyst', 'InceptionDate','EndDate', 'Status',
    #             'ROC ITD(bps)',' ITD($)', 'ROC YTD(bps)',' YTD($)',
    #             'ROMC YTD(bps)', 'ROMC MTD(bps)',
    #             'ROC MTD(bps)',' MTD($)' , 'ROC 5D(bps)', ' 5D($)',
    #             'ROC 1D(bps)', ' 1D($)',
    #             'VOL 30D(%)', 'CAPITAL 1D(%)']

def escape_columns_for_sql(df,columns):
    for cln in columns:
        df[cln] = df[cln].apply(lambda x: x.replace("'","\\'") )
    return df

def transpose_df(df):
    # df has m rows and n columns
    dfT = pd.DataFrame(columns=df.columns, data=[tuple(df.columns)]).append(df).transpose()
    dfT.columns = dfT.iloc[0]
    dfT = dfT.ix[dfT.index[1:]]
    dfT.index = range(len(dfT))
    return dfT

class df_slicer:
    def __init__(self, as_of_date=None):
        #today = datetime.date.today() if as_of_date is None else as_of_date
        #if as_of_date is None: as_of_date = today - datetime.timedelta(days=1)
        #self.today = today

        self.as_of_date = as_of_date if not pd.isnull(as_of_date) else datetime.date.today()
        self.holidays = \
            ['2015-01-01','2015-01-19','2015-02-16','2015-04-03',
             '2015-05-25','2015-07-03','2015-09-07','2015-10-12',
             '2015-11-11','2015-11-26','2015-12-25','2016-01-01',
             '2016-01-18','2016-02-15','2016-03-25','2016-05-30',
             '2016-07-04','2016-09-05','2016-11-24','2016-12-25',
             '2016-12-26',
             "2017-01-02","2017-01-16","2017-02-20","2017-04-14",
             "2017-05-29",'2017-07-04',"2017-09-04","2017-11-23",
             "2017-12-25","2018-01-01","2018-01-15","2018-02-19","2018-03-30",
             "2018-05-28","2018-07-04","2018-09-03","2018-11-22","2018-12-25"
             ]
        self.holidays_dts = [datetime.datetime.strptime(dt,'%Y-%m-%d') for dt in self.holidays]

    def slice(self, df, period):
        if period == 'MTD': return df[(df['Date'] >= self.mtd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == 'QTD': return df[(df['Date'] >= self.qtd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == 'YTD': return df[(df['Date'] >= self.ytd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == 'ITD': return df[(df['Date'] >= self.itd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == '1D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 1,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]
        if period == '3D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 3,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]
        if period == '5D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 5,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]
        if period == '30D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 30,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]

        return df

    def shift_back_if_not_business_day(self, date):
        as_of = date
        if as_of.weekday() == 5: as_of = (as_of - datetime.timedelta(days=1)) #Saturday -> Friday
        if as_of.weekday() == 6: as_of = (as_of - datetime.timedelta(days=2)) #Sunday -> Friday
        if as_of.strftime('%Y-%m-%d') in self.holidays:
            as_of = (as_of - datetime.timedelta(days=1))
            if as_of.weekday() == 5: as_of = (as_of - datetime.timedelta(days=1)) #Saturday -> Friday
            if as_of.weekday() == 6: as_of = (as_of - datetime.timedelta(days=2)) #Sunday -> Friday
        return as_of

    def shift_forward_if_not_business_day(self, date):
        as_of = date
        if as_of.weekday() == 5: as_of = (as_of + datetime.timedelta(days=2)) #Saturday -> Monday
        if as_of.weekday() == 6: as_of = (as_of + datetime.timedelta(days=1)) #Sunday -> Monday
        if as_of.strftime('%Y-%m-%d') in self.holidays:
            as_of = (as_of + datetime.timedelta(days=1))
            if as_of.weekday() == 5: as_of = (as_of + datetime.timedelta(days=2)) #Saturday -> Monday
            if as_of.weekday() == 6: as_of = (as_of + datetime.timedelta(days=1)) #Sunday -> Monday
        return as_of

    def qtd(self, date):
        return datetime.datetime(date.year, 1, 1).strftime("%Y%m%d") if date.month <= 3 else\
                    datetime.datetime(date.year, 4, 1).strftime("%Y%m%d") if date.month <= 6 else\
                    datetime.datetime(date.year, 7, 1).strftime("%Y%m%d") if date.month <= 9 else\
                    datetime.datetime(date.year, 10, 1).strftime("%Y%m%d")

    def mtd(self, date):
        return (datetime.datetime(date.year, date.month, 1)).strftime("%Y%m%d")

    def ytd(self, date):
        return (datetime.datetime(date.year, 1, 1)).strftime("%Y%m%d")

    def itd(self, date):
        return '20150101'

    def prev_n_business_days(self, n, date):
        for i in range(n):
            prev_day = df_slicer.shift_back_if_not_business_day(self, date - datetime.timedelta(1))
            date = prev_day
        return date

    def is_business_day(self, dt):
        if dt.weekday() in [5,6]: return False #weekend
        if dt in self.holidays_dts: return False #holiday
        return True


    def business_days_in_range(self, start_date, end_date):
        return sorted([start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1) if self.is_business_day(start_date + datetime.timedelta(days=i))])


    def slice_date_range(self, start_date_yyyymmdd, end_date_yyyymmdd, interval_days=7):
        start_date = datetime.datetime.strptime(start_date_yyyymmdd,'%Y%m%d')
        end_date = datetime.datetime.strptime(end_date_yyyymmdd,'%Y%m%d')
        k = interval_days
        dates = []
        i=0
        while True:
            start_dt = start_date + datetime.timedelta(k*i)
            end_dt = start_date + datetime.timedelta(k*(i+1)-1)
            if end_dt >= end_date:
                end_dt = end_date
                dates.append((start_dt.strftime('%Y%m%d'),end_dt.strftime('%Y%m%d')))
                break
            dates.append((start_dt.strftime('%Y%m%d'),end_dt.strftime('%Y%m%d')))
            i+=1
        return dates

    def next_n_business_days(self, n, date):
        for i in range(n):
            next_day = df_slicer.shift_forward_if_not_business_day(self, date + datetime.timedelta(1))
            date = next_day
        return date