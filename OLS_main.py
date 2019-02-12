import OLS_regression_analysis
import bbgclient
import datetime
import dfutils
import pandas as pd

metrics = ['P/E', "EV/EBITDA", "EV/Sales", 'DVD Yield', 'FCF Yield']
alpha_ticker = 'NXST US EQUITY'
analyst_upside = 97.50
analyst_downside = 61
analyst_pt_wic = 83
lookback = 120
unaffected_date = '2018-11-30'
target_date = "2019-01-08"
api_host = bbgclient.bbgclient.get_next_available_host()
fperiod = "1BF"

#OlS_results = OLS_regression_analysis.premium_analysis_df_OLS(alpha_ticker, analyst_upside, lookback, unaffected_date, target_date, metrics, api_host, fperiod = '1BF')
#OlS_results2 = OLS_regression_analysis.premium_analysis_df_OLS2(alpha_ticker, analyst_upside, analyst_downside, analyst_pt_wic, lookback, unaffected_date, target_date, metrics, api_host, adjustments_df_now = None, adjustments_df_ptd = None, fperiod = '1BF')

def run_OLS_regression_analysis(alpha_ticker, unaffectedDt, tgtDate, analyst_upside, analyst_downside, analyst_pt_wic, api_host, lookback = 120, adjustments_df_now = None, adjustments_df_ptd = None, f_period = '1BF'):
    metrics = ['P/E', "EV/EBITDA", "EV/Sales", 'DVD Yield', 'FCF Yield']
    slicer = dfutils.df_slicer()
    unaff_dt = datetime.datetime.strptime(unaffectedDt, '%Y-%m-%d')
    price_tgt_dt = datetime.datetime.strptime(tgtDate, '%Y-%m-%d')
    as_of_dt = datetime.datetime.today()
    
    peer_ticker_list = OLS_regression_analysis.bloomberg_peers(alpha_ticker)
    
    alpha_historical_mult_df = OLS_regression_analysis.multiples_df(alpha_ticker, slicer.prev_n_business_days(lookback,unaff_dt).strftime('%Y%m%d'), unaff_dt.strftime('%Y%m%d'), api_host, fperiod) 
    peer2historical_mult_df = {p:OLS_regression_analysis.multiples_df(p,slicer.prev_n_business_days(lookback,unaff_dt).strftime('%Y%m%d'), unaff_dt.strftime('%Y%m%d'), api_host, fperiod, multiples_to_query=metrics) for p in peer_ticker_list}
    
    peer2ptd_multiple = {p:OLS_regression_analysis.multiples_df(p,slicer.prev_n_business_days(100,price_tgt_dt).strftime('%Y%m%d'),price_tgt_dt.strftime('%Y%m%d'),api_host,fperiod='1BF',multiples_to_query=metrics) for p in peer_ticker_list}
    peer2now_multiple = {p:OLS_regression_analysis.multiples_df(p,slicer.prev_n_business_days(100,as_of_dt).strftime('%Y%m%d'),as_of_dt.strftime('%Y%m%d'),api_host,fperiod='1BF',multiples_to_query=metrics) for p in peer_ticker_list}
    
    dataframes = {
        'alpha_historical_mult_df':alpha_historical_mult_df,
        'peer2historical_mult_df':peer2historical_mult_df,
        'peer2ptd_multiple': peer2ptd_multiple,
        'peer2now_multiple': peer2now_multiple
    }
    
    original_results = OLS_regression_analysis.premium_analysis_df_OLS_quick(dataframes, alpha_ticker, analyst_upside, lookback, unaffectedDt, tgtDate, metrics, api_host, fperiod = "1BF")

    adjusted_results = OLS_regression_analysis.premium_analysis_df_OLS2_quick(dataframes, alpha_ticker, analyst_upside, analyst_downside, analyst_pt_wic, lookback, unaffectedDt, tgtDate, metrics, api_host, adjustments_df_now = None, adjustments_df_ptd = None, fperiod = "1BF")
    
    return { 'original_results': original_results, 
            'adjusted_results': adjusted_results
           }

#run_OLS_regression_analysis(alpha_ticker, unaffected_date, target_date, analyst_upside, analyst_downside, analyst_pt_wic, api_host, lookback = lookback, adjustments_df_now = None, adjustments_df_ptd = None, f_period = '1BF')