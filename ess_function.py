__author__ = 'aduprey'
import datetime
from collections import OrderedDict
import pandas as pd
import ess_premium_analysis
import bbgclient
import dfutils


def run_ess_premium_analysis(alpha_ticker, unaffectedDt, tgtDate, as_of_dt, analyst_upside, analyst_downside,
                             analyst_pt_wic, peers2weight, metric2weight, api_host, adjustments_df_bear=None,
                             adjustments_df_bull=None, adjustments_df_pt=None, bear_flag=None, bull_flag=None,
                             pt_flag=None, f_period='1BF', progress_recorder=None):
    slicer = dfutils.df_slicer()
    start_date = slicer.prev_n_business_days(120, unaffectedDt)  # lookback is 120 days (6 months)
    metrics = {k: v for k, v in metric2weight.items() if v != 0}
    try:
        peers_list = list(peers2weight.keys())
    except Exception:
        peers_list = [*peers2weight]
    try:
        metric_list = list(metrics.keys())
    except Exception:
        metric_list = [*metrics]

    if progress_recorder is not None:
        progress_recorder.set_progress(65, 100)

    calib_data = ess_premium_analysis.calibration_data(alpha_ticker, peers2weight, start_date, unaffectedDt,
                                                       metric_list, api_host, f_period)

    if progress_recorder is not None:
        progress_recorder.set_progress(75, 100)

    OLS_results, calculations_dict = ess_premium_analysis.premium_analysis_df_OLS(alpha_ticker, peers_list, calib_data,
                                                                                  analyst_upside, analyst_downside,
                                                                                  analyst_pt_wic, as_of_dt, tgtDate,
                                                                                  metric_list, metric2weight, api_host,
                                                                                  adjustments_df_bear,
                                                                                  adjustments_df_bull,
                                                                                  adjustments_df_pt, bear_flag,
                                                                                  bull_flag, pt_flag)

    if progress_recorder is not None:
        progress_recorder.set_progress(80, 100)

    premium_analysis_results = ess_premium_analysis.premium_analysis_df(alpha_ticker, peers_list, as_of_dt, tgtDate,
                                                                        analyst_upside, analyst_downside,
                                                                        analyst_pt_wic, metric_list, metric2weight,
                                                                        calib_data['metric2rel'], api_host,
                                                                        adjustments_df_bear, adjustments_df_bull,
                                                                        adjustments_df_pt, bear_flag, bull_flag,
                                                                        pt_flag)
    return premium_analysis_results, OLS_results, calculations_dict


def final_df(alpha_ticker, cix_index, unaffectedDt, expected_close, tgtDate, analyst_upside, analyst_downside,
             analyst_pt_wic, peers2weight, metric2weight, api_host, adjustments_df_bear=None,
             adjustments_df_bull=None, adjustments_df_pt=None, bear_flag=None, bull_flag=None,
             pt_flag=None, f_period="1BF", progress_recorder=None, as_of_dt=None):
    
    cix_calculations_dict = OrderedDict()
    slicer = dfutils.df_slicer()
    as_of_dt = datetime.datetime.today() if as_of_dt is None else as_of_dt

    print('Running Final_df as of : ' + str(as_of_dt))

    unaff_dt = datetime.datetime.strptime(unaffectedDt, '%Y-%m-%d')
    tgt_dt = datetime.datetime.strptime(tgtDate, '%Y-%m-%d')
    exp_close_dt = datetime.datetime.strptime(expected_close, '%Y-%m-%d')

    df = pd.Series()
    df["Alpha Ticker"] = alpha_ticker
    df["Unaffected Date"] = unaff_dt.strftime("%Y-%m-%d")
    df["CIX"] = cix_index
    df["Expected Close Date"] = exp_close_dt.strftime('%Y-%m-%d')

    if progress_recorder is not None:
        progress_recorder.set_progress(55, 100)

    df["Alpha Downside"] = analyst_downside
    df["Alpha PT (WIC)"] = analyst_pt_wic
    df["Alpha Upside"] = analyst_upside

    df["CIX at Target Date"] = bbgclient.bbgclient.get_timeseries(cix_index, 'PX_LAST',
                                                                  slicer.prev_n_business_days(100, tgt_dt).
                                                                  strftime('%Y%m%d'), tgt_dt.strftime('%Y%m%d'),
                                                                  api_host=api_host).iloc[-1]

    df["Alpha at Target Date"] = bbgclient.bbgclient.get_timeseries(alpha_ticker, 'PX_LAST',
                                                                    slicer.prev_n_business_days(100, tgt_dt).
                                                                    strftime('%Y%m%d'),
                                                                    tgt_dt.strftime('%Y%m%d'),
                                                                    api_host=api_host).iloc[-1]

    df["Alpha Last Price"] = bbgclient.bbgclient.get_timeseries(alpha_ticker, 'PX_LAST',
                                                                slicer.prev_n_business_days(100, as_of_dt).
                                                                strftime('%Y%m%d'), as_of_dt.strftime('%Y%m%d'),
                                                                api_host=api_host).iloc[-1]

    df["CIX Last Price"] = bbgclient.bbgclient.get_timeseries(cix_index, 'PX_LAST',
                                                              slicer.prev_n_business_days(100, as_of_dt)
                                                              .strftime('%Y%m%d'), as_of_dt.strftime('%Y%m%d'),
                                                              api_host=api_host).iloc[-1]

    df["CIX Upside"] = (df["Alpha Upside"] - df["Alpha at Target Date"]) + df["CIX at Target Date"]
    df["CIX Downside"] = df["CIX at Target Date"] - (df["Alpha at Target Date"] - df["Alpha Downside"])
    df["CIX WIC Adjustment"] = (df["Alpha PT (WIC)"] - df["Alpha at Target Date"]) + df["CIX at Target Date"]
    df["Down Price (CIX)"] = df["Alpha Last Price"] - (df["CIX Last Price"] - df["CIX Downside"])
    df["Up Price (CIX)"] = df["Alpha Last Price"] + (df["CIX Upside"] - df["CIX Last Price"])
    df["PT WIC Price (CIX)"] = df["Alpha Last Price"] + (df["CIX WIC Adjustment"] - df["CIX Last Price"])

    cix_calculations_dict['CIX Upside'] = ('(' + str(round(df['Alpha Upside'], 2)) + ' (Upside Analyst) - '
                                           + str(round(df['Alpha at Target Date'], 2)) +
                                           ' (Alpha at Target Date)) + '+ str(round(df['CIX at Target Date'], 2))
                                           + ' (CIX at Target Date) = ' + str(round(df['CIX Upside'], 2))
                                           + ' (CIX Upside)')
    cix_calculations_dict['CIX PT WIC'] = ('(' + str(round(df['Alpha PT (WIC)'], 2)) + ' (PT WIC Analyst) - '
                                           + str(round(df['Alpha at Target Date'], 2)) +
                                           ' (Alpha at Target Date)) + ' + str(round(df['CIX at Target Date'], 2))
                                           + ' (CIX at Target Date) = ' + str(round(df['CIX WIC Adjustment'], 2))
                                           + ' (CIX PT WIC Adjustment)')
    cix_calculations_dict['CIX Downside'] = (str(round(df['CIX at Target Date'], 2)) + ' (CIX at Target Date) - ('
                                             + str(round(df['Alpha at Target Date'], 2)) +
                                             ' (Alpha at Target Date) - ' + str(round(df['Alpha Downside'], 2))
                                             + ' (Alpha Downside)) = ' + str(round(df['CIX Downside'], 2))
                                             + ' (CIX Downside)')
    cix_calculations_dict['Down Price (CIX)'] = (str(round(df['Alpha Last Price'], 2)) + ' (Alpha Last Price) - ('
                                                 + str(round(df['CIX Last Price'], 2)) + ' (CIX Last Price) - '
                                                 + str(round(df['CIX Downside'], 2)) + ' (CIX Downside)) = '
                                                 + str(round(df['Down Price (CIX)'], 2)) + ' (Down Price (CIX))')
    cix_calculations_dict['PT WIC Price (CIX)'] = (str(round(df['Alpha Last Price'], 2)) + ' (Alpha Last Price) + ('
                                                   + str(round(df['CIX WIC Adjustment'], 2)) + ' (CIX WIC Adjustment) - '
                                                   + str(round(df['CIX Last Price'], 2)) +
                                                   ' (CIX Last Price)) = ' +
                                                   str(round(df['PT WIC Price (CIX)'], 2)) + ' (PT WIC Price (CIX))')
    cix_calculations_dict['Up Price (CIX)'] = (str(round(df['Alpha Last Price'], 2)) + ' (Alpha Last Price) + ('
                                               + str(round(df['CIX Upside'], 2)) + ' (CIX Upside) - ' +
                                               str(round(df['CIX Last Price'], 2)) + ' (CIX Last Price)) = '
                                               + str(round(df['Up Price (CIX)'], 2)) + ' (Up Price (CIX))')
    
    try:
        model1, model2, calculations_dict = run_ess_premium_analysis(alpha_ticker, unaff_dt, tgt_dt, as_of_dt,
                                                                     analyst_upside, analyst_downside, analyst_pt_wic,
                                                                     peers2weight, metric2weight, api_host,
                                                                     adjustments_df_bear, adjustments_df_bull,
                                                                     adjustments_df_pt, bear_flag, bull_flag, pt_flag,
                                                                     f_period, progress_recorder)
        df["Down Price (WIC)"] = model1["Alpha Downside (Adj,weighted)"].sum()
        df["Down Price (Regression)"] = model2["Alpha Downside (Adj,weighted)"].sum()
        df["PT WIC Price (WIC)"] = model1["Alpha PT WIC (Adj,weighted)"].sum()
        df["PT WIC Price (Regression)"] = model2["Alpha PT WIC (Adj,weighted)"].sum()
        df["Up Price (WIC)"] = model1["Alpha Upside (Adj,weighted)"].sum()
        df["Up Price (Regression)"] = model2["Alpha Upside (Adj,weighted)"].sum()

        df["Embedded Premium($)"] = df["Alpha Last Price"] - ((df["Down Price (WIC)"] + df["Up Price (WIC)"])/2.0)
        df["Embedded Premium(%)"] = 100.0*(df["Embedded Premium($)"]/df["Alpha Last Price"])

        df["Probability (CIX)"] = 100.0*((df["CIX Last Price"] - df["CIX Downside"])/(df["CIX Upside"] -
                                                                                      df["CIX Downside"]))
        df["Probability (Alpha)"] = 100.0*((df["Alpha Last Price"] - df["Alpha Downside"])/(df["Alpha Upside"] -
                                                                                            df["Alpha Downside"]))
        if pd.isna(df['Probability (CIX)']):
            df['Probability(%)'] = df['Probability (Alpha)']
        else:
            df['Probability(%)'] = df['Probability (CIX)']

        df["Return/Risk (CIX)"] = (df["CIX Upside"] - df["CIX Last Price"])/(df["CIX Last Price"] - df["CIX Downside"])
        df["Return/Risk (Alpha)"] = (df["Alpha Upside"] - df["Alpha Last Price"])/(df["Alpha Last Price"] -
                                                                                   df["Alpha Downside"])
        if not pd.isna(df['Return/Risk (CIX)']):
            df['Return/Risk'] = df['Return/Risk (CIX)']
        else:
            df['Return/Risk'] = df['Probability (Alpha)']

        df["Gross Return (CIX)"] = 100.0*((df["CIX Upside"] - df["CIX Last Price"])/df["Alpha Last Price"])
        df["Gross Return (Alpha)"] = 100.0*((df["Alpha Upside"] - df["Alpha Last Price"])/df["Alpha Last Price"])
        if not pd.isna(df['Gross Return (CIX)']):
            df['Gross Return(%)'] = df['Gross Return (CIX)']
            gross = df['Gross Return(%)']
        else:
            df['Gross Return(%)'] = df['Gross Return (Alpha)']
            gross = df['Gross Return(%)']

        days = abs((exp_close_dt - as_of_dt).days)
        df["Days to Close"] = [None if pd.isnull(days) else days]

        if pd.isna(df['Gross Return(%)']) or pd.isna(df["Days to Close"]) or days <= 7:
            df['Ann. Return(%)'] = None
        else:
            df['Ann. Return(%)'] = 100.0*((1+gross/100)**(365.0/days)-1.0)

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
    except Exception as e:
        cols2show = ['Alpha Ticker',
                     'Unaffected Date',
                     'Expected Close Date',
                     'CIX',
                     'Alpha Last Price',
                     'CIX Last Price',
                     'Alpha Downside',
                     'Down Price (CIX)',
                     'PT WIC Price (CIX)',
                     'Alpha Upside',
                     'Up Price (CIX)',
                    ]
        regression_output = None
        calculations_dict = None
        print('failed running WIC and Regression models: ' + str(e.args))


    return {'Final Results': df[cols2show],
            'Regression Results': regression_output,
            'Regression Calculations': calculations_dict,
            'CIX Calculations': cix_calculations_dict
           }