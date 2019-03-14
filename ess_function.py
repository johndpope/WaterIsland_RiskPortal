__author__ = 'aduprey'
import ess_premium_analysis
import bbgclient
import datetime
import dfutils
import pandas as pd
import ast
import statsmodels.formula.api as sm

#Necessary input items from the database
alpha = "GPS US EQUITY"
CIX_Index = ".ESSGPS INDEX"
unaffected_date = "2019-02-28"
tgt_date = "2019-03-01"
exp_close_date = "2020-12-31"

analyst_upside = 37.99
analyst_downside = 22.99
analyst_pt_wic = 22.99
peers_names = ["AEO US EQUITY", "EXPR US EQUITY", "URBN US EQUITY", "GES US EQUITY", "ANF US EQUITY"]
peers_weights = [0.2,0.2,0.2,0.2,0.2]
multiples_names = ["EV/Sales", "EV/EBITDA", "P/EPS", "DVD yield", "FCF yield"]
multiples_weights = [0,0.75,0.25,0,0]

#The functions as for the api_host and 
api_host = bbgclient.bbgclient.get_next_available_host()
#Create a dictionary of the peers and weights and the multiples and weights

def create_dict(keys, values):
    return dict(zip(keys, values + [None] * (len(keys) - len(values))))

#Take the peers vs. weights and the multiples vs. weights and create dictionaries
#These two factors must have type dictionary for input
peersVSweights = create_dict(peers_names, peers_weights)
multiplesVSweights = create_dict(multiples_names, multiples_weights)
as_of_dt = datetime.datetime.today()
unaff_dt = datetime.datetime.strptime(unaffected_date, '%Y-%m-%d')
tgt_dt = datetime.datetime.strptime(tgt_date, '%Y-%m-%d')


adjustments_df_bear = '[{"Date":"2019-03-08","PX":"0","BEST_EPS":"0","BEST_NET_INCOME":"0","BEST_OPP":"0","BEST_SALES":"0","CUR_EV_COMPONENT":"0","CUR_MKT_CAP":"0","DIVIDEND_INDICATED_YIELD":"0","BEST_CAPEX":"0","BEST_EBITDA":"0","EQY_SH_OUT":"0"}]'
adjustments_df_bull = '[{"Date":"2019-03-08","PX":"0","BEST_EPS":"0","BEST_NET_INCOME":"0","BEST_OPP":"0","BEST_SALES":"0","CUR_EV_COMPONENT":"0","CUR_MKT_CAP":"0","DIVIDEND_INDICATED_YIELD":"0","BEST_CAPEX":"0","BEST_EBITDA":"0","EQY_SH_OUT":"0"}]'
adjustments_df_pt = '[{"Date":"2019-03-08","PX":"0","BEST_EPS":"0","BEST_NET_INCOME":"0","BEST_OPP":"0","BEST_SALES":"0","CUR_EV_COMPONENT":"0","CUR_MKT_CAP":"0","DIVIDEND_INDICATED_YIELD":"0","BEST_CAPEX":"0","BEST_EBITDA":"0","EQY_SH_OUT":"0"}]'
bear_flag = None
bull_flag = None
pt_flag = None

def run_ess_premium_analysis(alpha_ticker, unaffectedDt, tgtDate, as_of_dt, analyst_upside, analyst_downside, analyst_pt_wic, peers2weight, metric2weight, api_host, adjustments_df_bear = None, adjustments_df_bull = None, adjustments_df_pt = None, bear_flag = None, bull_flag = None, pt_flag = None, f_period = '1BF'):
    slicer = dfutils.df_slicer()
    start_date = slicer.prev_n_business_days(120, unaffectedDt) #lookback is 120 days (6 months)
    metrics = {k: v for k, v in metric2weight.items() if v != 0}
    peers_list = list(peers2weight.keys())
    metric_list = list(metrics.keys())

    calib_data = ess_premium_analysis_3balancesheets.calibration_data(alpha_ticker, peers2weight, start_date, unaffectedDt, metric_list, api_host, f_period)

    OLS_results = ess_premium_analysis_3balancesheets.premium_analysis_df_OLS(alpha_ticker, peers_list, calib_data, analyst_upside, analyst_downside, analyst_pt_wic, as_of_dt, tgtDate, metric_list, metric2weight, api_host, adjustments_df_bear, adjustments_df_bull, adjustments_df_pt, bear_flag, bull_flag, pt_flag)
    premium_analysis_results = ess_premium_analysis_3balancesheets.premium_analysis_df(alpha_ticker, peers_list, as_of_dt, tgtDate, analyst_upside, analyst_downside, analyst_pt_wic, metric_list, metric2weight, calib_data['metric2rel'], api_host, adjustments_df_bear, adjustments_df_bull, adjustments_df_pt, bear_flag, bull_flag, pt_flag)

    return(premium_analysis_results, OLS_results)

def final_df(alpha_ticker, cix_index, unaffectedDt, expected_close, tgtDate, analyst_upside, analyst_downside, analyst_pt_wic, peers2weight, metric2weight, api_host, adjustments_df_bear = None, adjustments_df_bull = None, adjustments_df_pt = None, bear_flag = None, bull_flag = None, pt_flag = None, f_period = "1BF"):
    slicer = dfutils.df_slicer()
    as_of_dt = datetime.datetime.today()
    unaff_dt = datetime.datetime.strptime(unaffectedDt, '%Y-%m-%d')
    tgt_dt = datetime.datetime.strptime(tgtDate, '%Y-%m-%d')
    exp_close_dt = datetime.datetime.strptime(expected_close, '%Y-%m-%d')
    
    df = pd.Series()
    df["Alpha Ticker"] = alpha_ticker
    df["Unaffected Date"] = unaff_dt.strftime("%Y-%m-%d")
    df["CIX"] = cix_index
    df["Expected Close Date"] = exp_close_dt.strftime('%Y-%m-%d')
    
    df["Alpha Downside"] = analyst_downside
    df["Alpha PT (WIC)"] = analyst_pt_wic
    df["Alpha Upside"] = analyst_upside
    
    df["CIX at Target Date"] = bbgclient.bbgclient.get_timeseries(cix_index,'PX_LAST', slicer.prev_n_business_days(100,tgt_dt).strftime('%Y%m%d'), tgt_dt.strftime('%Y%m%d'), api_host=api_host).iloc[-1]
    df["Alpha at Target Date"] = bbgclient.bbgclient.get_timeseries(alpha_ticker,'PX_LAST', slicer.prev_n_business_days(100,tgt_dt).strftime('%Y%m%d'), tgt_dt.strftime('%Y%m%d'), api_host=api_host).iloc[-1]
    df["Alpha Last Price"] = bbgclient.bbgclient.get_timeseries(alpha_ticker,'PX_LAST', slicer.prev_n_business_days(100,as_of_dt).strftime('%Y%m%d'), as_of_dt.strftime('%Y%m%d'), api_host=api_host).iloc[-1]
    df["CIX Last Price"] = bbgclient.bbgclient.get_timeseries(cix_index,'PX_LAST', slicer.prev_n_business_days(100,as_of_dt).strftime('%Y%m%d'), as_of_dt.strftime('%Y%m%d'),api_host=api_host).iloc[-1]
    
    df["CIX Upside"] = (df["Alpha Upside"] - df["Alpha at Target Date"]) + df["CIX at Target Date"]
    df["CIX Downside"] = df["CIX at Target Date"] - (df["Alpha at Target Date"] - df["Alpha Downside"])
    df["CIX WIC Adjustment"] = (df["Alpha PT (WIC)"] - df["Alpha at Target Date"]) + df["CIX at Target Date"]
    df["Down Price (CIX)"] = df["Alpha Last Price"] - (df["CIX Last Price"] - df["CIX Downside"])
    df["Up Price (CIX)"] = df["Alpha Last Price"] + (df["CIX Upside"] - df["CIX Last Price"])
    df["PT WIC Price (CIX)"] = df["Alpha Last Price"] + (df["CIX WIC Adjustment"] - df["CIX Last Price"])
    
    try:
        model1, model2 = run_ess_premium_analysis(alpha_ticker, unaff_dt, tgt_dt, as_of_dt, analyst_upside, analyst_downside, analyst_pt_wic, peers2weight, metric2weight, api_host, adjustments_df_bear, adjustments_df_bull, adjustments_df_pt, bear_flag, bull_flag, pt_flag, f_period = "1BF")
    except Exception as e:
        print('failed running WIC and Regression models: ' + str(e.args))
    
    df["Down Price (WIC)"] = model1["Alpha Downside (Adj,weighted)"].sum()
    df["Down Price (Regression)"] = model2["Alpha Downside (Adj,weighted)"].sum()
    df["PT WIC Price (WIC)"] = model1["Alpha PT WIC (Adj,weighted)"].sum()
    df["PT WIC Price (Regression)"] = model2["Alpha PT WIC (Adj,weighted)"].sum()
    df["Up Price (WIC)"] = model1["Alpha Upside (Adj,weighted)"].sum()
    df["Up Price (Regression)"] = model2["Alpha Upside (Adj,weighted)"].sum()
    
    df["Embedded Premium($)"] = df["Alpha Last Price"] - ((df["Down Price (WIC)"] + df["Up Price (WIC)"])/2.0)
    df["Embedded Premium(%)"] = 100.0*(df["Embedded Premium($)"]/df["Alpha Last Price"])
    
    df["Probability (CIX)"] = 100.0*((df["CIX Last Price"] - df["CIX Downside"])/(df["CIX Upside"] - df["CIX Downside"]))
    df["Probability (Alpha)"] = 100.0*((df["Alpha Last Price"] - df["Alpha Downside"])/(df["Alpha Upside"] - df["Alpha Downside"]))
    if pd.isna(df['Probability (CIX)']):
        df['Probability(%)'] = df['Probability (Alpha)']
    else:
        df['Probability(%)'] = df['Probability (CIX)']
    #df['Probability(%)'] = [prob_cix if not pd.isnull(prob_cix) else prob_alpha for (prob_cix, prob_alpha) in zip(df["Probability (CIX)"], df["Probability (Alpha)"])]
    
    df["Return/Risk (CIX)"] = (df["CIX Upside"] - df["CIX Last Price"])/(df["CIX Last Price"] - df["CIX Downside"])
    df["Return/Risk (Alpha)"] = (df["Alpha Upside"] - df["Alpha Last Price"])/(df["Alpha Last Price"] - df["Alpha Downside"])
    if not pd.isna(df['Return/Risk (CIX)']):
        df['Return/Risk'] = df['Return/Risk (CIX)']
    else:
        df['Return/Risk'] = df['Probability (Alpha)']
    #df["Return/Risk"] = [radj_cix if not pd.isnull(radj_cix) else radj_alpha for (radj_cix, radj_alpha) in zip(df["Return/Risk (CIX)"], df["Return/Risk (Alpha)"])]
    
    df["Gross Return (CIX)"] = 100.0*((df["CIX Upside"] - df["CIX Last Price"])/df["Alpha Last Price"])
    df["Gross Return (Alpha)"] = 100.0*((df["Alpha Upside"] - df["Alpha Last Price"])/df["Alpha Last Price"])
    if not pd.isna(df['Gross Return (CIX)']):
        df['Gross Return(%)'] = df['Gross Return (CIX)']
        gross = df['Gross Return(%)']
    else:
        df['Gross Return(%)'] = df['Gross Return (Alpha)']
        gross = df['Gross Return(%)']
    #df['Gross Return(%)'] = [gross_ret_cix if not pd.isnull(gross_ret_cix) else gross_ret_alpha for (gross_ret_cix, gross_ret_alpha) in zip(df["Gross Return (CIX)"], df["Gross Return (Alpha)"])]

    days = abs((exp_close_dt - as_of_dt).days)
    df["Days to Close"] = [None if pd.isnull(days) else days]
    if (pd.isna(df['Gross Return(%)']) or pd.isna(df["Days to Close"]) or days <= 7):
        df['Ann. Return(%)'] = None
    else:
        df['Ann. Return(%)'] = 100.0*((1+gross/100)**(365.0/days)-1.0)
    #df['Ann. Return(%)'] = [None if (pd.isnull(ret) or pd.isnull(days) or days <= 7) else 100.0*((1+ret/100)**(365.0/days)-1.0) for (ret, days) in zip(df['Gross Return(%)'] , df["Days to Close"])]                
    
    float_cols = ["Alpha Upside",
                "Alpha Downside",
                "Alpha Last Price",
                'Up Price (CIX)',
                'Down Price (CIX)',
                'CIX Last Price',
                'Return/Risk',
                'Probability(%)',
                'Gross Return(%)',
                'Ann. Return(%)',
                'Up Price (WIC)',
                'Down Price (WIC)',
                'Up Price (Regression)',
                'Down Price (Regression)',
                'Embedded Premium($)',
                'Embedded Premium(%)']
    df[float_cols] = df[float_cols].astype(float)
    
    cols2show = ['Alpha Ticker',
                 'Unaffected Date',
                 'Expected Close Date',
                 'CIX',
                 'Alpha Last Price',
                 'CIX Last Price',
                 'Alpha Downside',
                 'Down Price (CIX)',
                 'Down Price (WIC)',
                 'Down Price (Regression)',
                 'Alpha PT (WIC)',
                 'PT WIC Price (CIX)',
                 'PT WIC Price (WIC)',
                 'PT WIC Price (Regression)',
                 'Alpha Upside',
                 'Up Price (CIX)',
                 'Up Price (WIC)',
                 'Up Price (Regression)',
                 'Embedded Premium($)',
                 'Embedded Premium(%)',
                 'Probability(%)',
                 'Return/Risk',
                 'Gross Return(%)',
                 'Ann. Return(%)']
    
    regression_model_display_columns = ['Metric',
                                        'Coefficients',
                                        'Peers Multiples @ Price Target Date',
                                        'Alpha Implied Multiple @ Price Target Date',
                                        'Alpha Bear Multiple @ Price Target Date',
                                        'Alpha PT WIC Multiple @ Price Target Date',
                                        'Alpha Bull Multiple @ Price Target Date',
                                        'Premium Bear (%)',
                                        'Premium PT WIC (%)',
                                        'Premium Bull (%)',
                                        'Peers Multiples @ Now',
                                        'Alpha Implied Multiple @ Now',
                                        'Alpha Bear Multiple @ Now',
                                        'Alpha PT WIC Multiple @ Now',
                                        'Alpha Bull Multiple @ Now',
                                        'Alpha Downside',
                                        'Alpha PT WIC',
                                        'Alpha Upside']
    
    regression_output = model2[regression_model_display_columns]
    regression_output = regression_output.set_index('Metric').to_dict('index')

    return {'Final Results': df[cols2show],
            'Regression Results': regression_output
           }

#final_results = final_df(alpha, CIX_Index, unaffected_date, exp_close_date, tgt_date, analyst_upside, analyst_downside, analyst_pt_wic, peersVSweights, multiplesVSweights, api_host, adjustments_df_bear = adjustments_df_bear, adjustments_df_bull = adjustments_df_bull, adjustments_df_pt = adjustments_df_pt, bear_flag = bear_flag, bull_flag = bull_flag, pt_flag = pt_flag, f_period = "1BF")
