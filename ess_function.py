__author__ = 'aduprey'
import ess_premium_analysis
import bbgclient
import datetime
import dfutils
import pandas as pd


# Function that takes input and runs the ess_premium_analysis.py document
# The output of this function is the rsults of each model as dataframes
def run_ess_premium_analysis(alpha_ticker, unaffectedDt, tgtDate, as_of_dt, analyst_upside, analyst_downside,
                             analyst_pt_wic, peers2weight, metric2weight, api_host, adjustments_df_now=None,
                             adjustments_df_ptd=None, premium_as_percent=None, f_period='1BF'):
    slicer = dfutils.df_slicer()
    start_date = slicer.prev_n_business_days(120, unaffectedDt)  # lookback is 120 days (6 months)
    metrics = {k: v for k, v in metric2weight.items() if v != 0}
    peers_list = list(peers2weight.keys())
    metric_list = list(metrics.keys())

    calib_data = ess_premium_analysis.calibration_data(alpha_ticker, peers2weight, start_date, unaffectedDt,
                                                       metric_list, api_host, f_period)

    OLS_results = ess_premium_analysis.premium_analysis_df_OLS(alpha_ticker, peers_list, calib_data, analyst_upside,
                                                               analyst_downside, analyst_pt_wic, as_of_dt, tgtDate,
                                                               metric_list, metric2weight, api_host, adjustments_df_now,
                                                               adjustments_df_ptd, premium_as_percent)
    premium_analysis_results = ess_premium_analysis.premium_analysis_df(alpha_ticker, peers_list, as_of_dt, tgtDate,
                                                                        analyst_upside, analyst_downside,
                                                                        analyst_pt_wic, metric_list, metric2weight,
                                                                        calib_data['metric2rel'], api_host,
                                                                        adjustments_df_now, adjustments_df_ptd,
                                                                        premium_as_percent)

    return (premium_analysis_results, OLS_results)


def final_df(alpha_ticker, cix_index, unaffectedDt, expected_close, tgtDate, analyst_upside, analyst_downside,
             analyst_pt_wic, peers2weight, metric2weight, api_host, adjustments_df_now=None, adjustments_df_ptd=None,
             premium_as_percent=None, f_period="1BF"):
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

    df["CIX at Target Date"] = bbgclient.bbgclient.get_timeseries(cix_index, 'PX_LAST',
                                                                  slicer.prev_n_business_days(100, tgt_dt).strftime(
                                                                      '%Y%m%d'), tgt_dt.strftime('%Y%m%d'),
                                                                  api_host=api_host).iloc[-1]
    df["Alpha at Target Date"] = bbgclient.bbgclient.get_timeseries(alpha_ticker, 'PX_LAST',
                                                                    slicer.prev_n_business_days(100, tgt_dt).strftime(
                                                                        '%Y%m%d'), tgt_dt.strftime('%Y%m%d'),
                                                                    api_host=api_host).iloc[-1]
    df["Alpha Last Price"] = bbgclient.bbgclient.get_timeseries(alpha_ticker, 'PX_LAST',
                                                                slicer.prev_n_business_days(100, as_of_dt).strftime(
                                                                    '%Y%m%d'), as_of_dt.strftime('%Y%m%d'),
                                                                api_host=api_host).iloc[-1]
    df["CIX Last Price"] = bbgclient.bbgclient.get_timeseries(cix_index, 'PX_LAST',
                                                              slicer.prev_n_business_days(100, as_of_dt).strftime(
                                                                  '%Y%m%d'), as_of_dt.strftime('%Y%m%d'),
                                                              api_host=api_host).iloc[-1]

    df["CIX Upside"] = (df["Alpha Upside"] - df["Alpha at Target Date"]) + df["CIX at Target Date"]
    df["CIX Downside"] = df["CIX at Target Date"] - (df["Alpha at Target Date"] - df["Alpha Downside"])
    df["CIX WIC Adjustment"] = (df["Alpha PT (WIC)"] - df["Alpha at Target Date"]) + df["CIX at Target Date"]
    df["Down Price (CIX)"] = df["Alpha Last Price"] - (df["CIX Last Price"] - df["CIX Downside"])
    df["Up Price (CIX)"] = df["Alpha Last Price"] + (df["CIX Upside"] - df["CIX Last Price"])
    df["PT WIC Price (CIX)"] = df["Alpha Last Price"] + (df["CIX WIC Adjustment"] - df["CIX Last Price"])

    # try:
    model1, model2 = run_ess_premium_analysis(alpha_ticker, unaff_dt, tgt_dt, as_of_dt, analyst_upside,
                                              analyst_downside, analyst_pt_wic, peers2weight, metric2weight, api_host,
                                              adjustments_df_now, adjustments_df_ptd, premium_as_percent,
                                              f_period="1BF")
    # except Exception as e:
    # print('failed running WIC and Regression models: ' + str(e.args))

    df["Down Price (WIC)"] = model1["Alpha Downside (Adj,weighted)"].sum()
    df["Down Price (Regression)"] = model2["Alpha Downside (Adj,weighted)"].sum()
    df["PT WIC Price (WIC)"] = model1["Alpha PT WIC (Adj,weighted)"].sum()
    df["PT WIC Price (Regression)"] = model2["Alpha PT WIC (Adj,weighted)"].sum()
    df["Up Price (WIC)"] = model1["Alpha Upside (Adj,weighted)"].sum()
    df["Up Price (Regression)"] = model2["Alpha Upside (Adj,weighted)"].sum()

    df["Embedded Premium($)"] = df["Alpha Last Price"] - ((df["Down Price (WIC)"] + df["Up Price (WIC)"]) / 2.0)
    df["Embedded Premium(%)"] = 100.0 * (df["Embedded Premium($)"] / df["Alpha Last Price"])

    df["Probability (CIX)"] = 100.0 * (
                (df["CIX Last Price"] - df["CIX Downside"]) / (df["CIX Upside"] - df["CIX Downside"]))
    df["Probability (Alpha)"] = 100.0 * (
                (df["Alpha Last Price"] - df["Alpha Downside"]) / (df["Alpha Upside"] - df["Alpha Downside"]))
    if pd.isna(df['Probability (CIX)']):
        df['Probability(%)'] = df['Probability (Alpha)']
    else:
        df['Probability(%)'] = df['Probability (CIX)']
    # df['Probability(%)'] = [prob_cix if not pd.isnull(prob_cix) else prob_alpha for (prob_cix, prob_alpha) in zip(df["Probability (CIX)"], df["Probability (Alpha)"])]

    df["Return/Risk (CIX)"] = (df["CIX Upside"] - df["CIX Last Price"]) / (df["CIX Last Price"] - df["CIX Downside"])
    df["Return/Risk (Alpha)"] = (df["Alpha Upside"] - df["Alpha Last Price"]) / (
                df["Alpha Last Price"] - df["Alpha Downside"])
    if not pd.isna(df['Return/Risk (CIX)']):
        df['Return/Risk'] = df['Return/Risk (CIX)']
    else:
        df['Return/Risk'] = df['Probability (Alpha)']
    # df["Return/Risk"] = [radj_cix if not pd.isnull(radj_cix) else radj_alpha for (radj_cix, radj_alpha) in zip(df["Return/Risk (CIX)"], df["Return/Risk (Alpha)"])]

    df["Gross Return (CIX)"] = 100.0 * ((df["CIX Upside"] - df["CIX Last Price"]) / df["Alpha Last Price"])
    df["Gross Return (Alpha)"] = 100.0 * ((df["Alpha Upside"] - df["Alpha Last Price"]) / df["Alpha Last Price"])
    if not pd.isna(df['Gross Return (CIX)']):
        df['Gross Return(%)'] = df['Gross Return (CIX)']
        gross = df['Gross Return(%)']
    else:
        df['Gross Return(%)'] = df['Gross Return (Alpha)']
        gross = df['Gross Return(%)']
    # df['Gross Return(%)'] = [gross_ret_cix if not pd.isnull(gross_ret_cix) else gross_ret_alpha for (gross_ret_cix, gross_ret_alpha) in zip(df["Gross Return (CIX)"], df["Gross Return (Alpha)"])]

    # d1 = datetime.datetime.strptime(expected_close, '%Y-%m-%d')
    # d1 = datetime.datetime.strptime(as_of_dt, '%Y-%m-%d')
    days = abs((exp_close_dt - as_of_dt).days)
    df["Days to Close"] = [None if pd.isnull(days) else days]
    if (pd.isna(df['Gross Return(%)']) or pd.isna(df["Days to Close"]) or days <= 7):
        df['Ann. Return(%)'] = None
    else:
        df['Ann. Return(%)'] = 100.0 * ((1 + gross / 100) ** (365.0 / days) - 1.0)
    # df['Ann. Return(%)'] = [None if (pd.isnull(ret) or pd.isnull(days) or days <= 7) else 100.0*((1+ret/100)**(365.0/days)-1.0) for (ret, days) in zip(df['Gross Return(%)'] , df["Days to Close"])]

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

    return (df[cols2show])

