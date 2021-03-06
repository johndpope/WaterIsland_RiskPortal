__author__ = 'aduprey'
import OLS_regression_analysis
import bbgclient
import datetime
import dfutils
import pandas as pd

# The line below is the function to run the REGRESSION PART
# results = OLS_regression_analysis.run_regression_optimal_peers(alpha_ticker, unaffected_date, lookback_period = 120)

def run_OLS_regression_analysis(alpha_ticker, tgtDate, analyst_upside, analyst_downside, analyst_pt_wic,
                                regression_results, adjustments_df_now=None, adjustments_df_ptd=None,
                                f_period='1BF'):

    api_host = bbgclient.bbgclient.get_next_available_host()
    metrics = ['P/E', "EV/EBITDA", "EV/Sales", 'DVD Yield', 'FCF Yield']
    slicer = dfutils.df_slicer()
    price_tgt_dt = datetime.datetime.strptime(tgtDate, '%Y-%m-%d')
    as_of_dt = datetime.datetime.today()

    if len(regression_results) == 2:
        optimal_results = regression_results[0]
        overlap_results = regression_results[1]
    else:
        optimal_results = regression_results

    peers = []
    for metric in metrics:
        for x in optimal_results[metric]:
            if x not in peers:
                peers.append(x)
    peers.remove('(Intercept)')

    peer2ptd_multiple = {
    p: OLS_regression_analysis.multiples_df(p, slicer.prev_n_business_days(100, price_tgt_dt).strftime('%Y%m%d'),
                                            price_tgt_dt.strftime('%Y%m%d'), api_host, fperiod='1BF',
                                            multiples_to_query=metrics) for p in peers}
    peer2now_multiple = {
    p: OLS_regression_analysis.multiples_df(p, slicer.prev_n_business_days(100, as_of_dt).strftime('%Y%m%d'),
                                            as_of_dt.strftime('%Y%m%d'), api_host, fperiod='1BF',
                                            multiples_to_query=metrics) for p in peers}

    dataframes = {
        'peer2ptd_multiple': peer2ptd_multiple,
        'peer2now_multiple': peer2now_multiple
    }

    original_results = OLS_regression_analysis.premium_analysis_df_OLS_quick(dataframes, regression_results,
                                                                             alpha_ticker, analyst_upside, tgtDate,
                                                                             api_host, fperiod="1BF")

    adjusted_results = OLS_regression_analysis.premium_analysis_df_OLS2_quick(dataframes, regression_results,
                                                                              alpha_ticker, analyst_upside,
                                                                              analyst_downside, analyst_pt_wic, tgtDate,
                                                                              api_host, adjustments_df_now=None,
                                                                              adjustments_df_ptd=None, fperiod="1BF")

    return {'original_results': original_results,
            'adjusted_results': adjusted_results
            }
