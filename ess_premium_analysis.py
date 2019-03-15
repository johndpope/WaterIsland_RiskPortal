import bbgclient
import dfutils
import datetime
import pandas as pd
import statsmodels.formula.api as sm
import ast


def multiple_underlying_df(ticker, end_date_yyyymmdd, api_host, fperiod="1BF"):
    slicer = dfutils.df_slicer()

    if type(end_date_yyyymmdd) == str:
        end_date_yyyymmdd = datetime.datetime.strptime(end_date_yyyymmdd, '%Y%m%d')

    def last_elem_or_null(ts):
        if ts is None: return None
        if len(ts) == 0: return None
        return ts.iloc[-1]

    px = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'PX_LAST',
                                                              slicer.prev_n_business_days(100, end_date_yyyymmdd).
                                                              strftime('%Y%m%d'), end_date_yyyymmdd.strftime('%Y%m%d'),
                                                              api_host=api_host))

    mkt_cap = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'CUR_MKT_CAP',
                                                                   slicer.prev_n_business_days(100, end_date_yyyymmdd).
                                                                   strftime('%Y%m%d'), end_date_yyyymmdd.
                                                                   strftime('%Y%m%d'), api_host=api_host))

    ev_component = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'CUR_EV_COMPONENT',
                                                                        slicer.prev_n_business_days(100,
                                                                                                    end_date_yyyymmdd)
                                                                        .strftime('%Y%m%d'), end_date_yyyymmdd.
                                                                        strftime('%Y%m%d'), api_host=api_host))

    eqy_sh_out = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'EQY_SH_OUT',
                                                                      slicer.prev_n_business_days(100,
                                                                                                  end_date_yyyymmdd).
                                                                      strftime('%Y%m%d'),
                                                                      end_date_yyyymmdd.strftime('%Y%m%d'),
                                                                      api_host=api_host))
    best_ebitda = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'BEST_EBITDA',
                                                                       slicer.prev_n_business_days(100,
                                                                                                   end_date_yyyymmdd)
                                                                       .strftime('%Y%m%d'),
                                                                       end_date_yyyymmdd.strftime('%Y%m%d'),
                                                                       {'BEST_FPERIOD_OVERRIDE': fperiod}, api_host))
    best_sales = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'BEST_SALES',
                                                                      slicer.prev_n_business_days(100,
                                                                                                  end_date_yyyymmdd).
                                                                      strftime('%Y%m%d'),
                                                                      end_date_yyyymmdd.strftime('%Y%m%d'),
                                                                      {'BEST_FPERIOD_OVERRIDE': fperiod}, api_host))

    best_eps = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'BEST_EPS',
                                                                    slicer.prev_n_business_days(100, end_date_yyyymmdd)
                                                                    .strftime('%Y%m%d'), end_date_yyyymmdd.
                                                                    strftime('%Y%m%d'), {'BEST_FPERIOD_OVERRIDE':
                                                                                         fperiod}, api_host))

    div_ind_yield = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'DIVIDEND_INDICATED_YIELD',
                                                                         slicer.prev_n_business_days(100,
                                                                                                     end_date_yyyymmdd)
                                                                         .strftime('%Y%m%d'),
                                                                         end_date_yyyymmdd.strftime('%Y%m%d'),
                                                                         api_host=api_host))

    best_opp = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'BEST_OPP',
                                                                    slicer.prev_n_business_days(100, end_date_yyyymmdd)
                                                                    .strftime('%Y%m%d'), end_date_yyyymmdd.
                                                                    strftime('%Y%m%d'), api_host=api_host))

    best_ni = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'BEST_NET_INCOME',
                                                                   slicer.prev_n_business_days(100,
                                                                                               end_date_yyyymmdd)
                                                                   .strftime('%Y%m%d'), end_date_yyyymmdd.
                                                                   strftime('%Y%m%d'), {'BEST_FPERIOD_OVERRIDE':
                                                                                        fperiod},
                                                                   api_host=api_host))
    best_capex = last_elem_or_null(bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CAPEX',
                                                                      slicer.prev_n_business_days(100,
                                                                                                  end_date_yyyymmdd).
                                                                      strftime('%Y%m%d'),
                                                                      end_date_yyyymmdd.strftime('%Y%m%d'),
                                                                      api_host=api_host))

    cols = ['Date', 'PX', 'CUR_MKT_CAP', 'EQY_SH_OUT', 'BEST_EBITDA', 'BEST_SALES',
            'BEST_EPS', 'DIVIDEND_INDICATED_YIELD', 'BEST_OPP', 'BEST_NET_INCOME', 'BEST_CAPEX', 'CUR_EV_COMPONENT']
    datum = [(pd.to_datetime(end_date_yyyymmdd), px, mkt_cap, eqy_sh_out, best_ebitda, best_sales, best_eps,
              div_ind_yield, best_opp, best_ni, best_capex, ev_component)]
    df = pd.DataFrame(columns=cols, data=datum)

    return df


def multiples_df(ticker, start_date_yyyymmdd, unaffected_date_yyyymmdd, api_host, fperiod, multiples_to_query='ALL'):
    if multiples_to_query == 'ALL':
        multiples_to_query = ['EV/EBITDA', 'EV/Sales', 'P/EPS', 'DVD yield', 'FCF yield']
    pe = pd.Series()
    ev_to_ebitda = pd.Series()
    ev_to_sales = pd.Series()
    dvd_yield = pd.Series()
    px = bbgclient.bbgclient.get_timeseries(ticker, 'PX_LAST', start_date_yyyymmdd, unaffected_date_yyyymmdd,
                                            api_host=api_host)
    if 'EV/EBITDA' in multiples_to_query:
        ev_to_ebitda = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CUR_EV_TO_EBITDA', start_date_yyyymmdd,
                                                          unaffected_date_yyyymmdd, {'BEST_FPERIOD_OVERRIDE': fperiod},
                                                          api_host)
    if 'EV/Sales' in multiples_to_query:
        ev_to_sales = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CURRENT_EV_BEST_SALES', start_date_yyyymmdd,
                                                         unaffected_date_yyyymmdd, {'BEST_FPERIOD_OVERRIDE': fperiod},
                                                         api_host)
    if 'P/EPS' in multiples_to_query:
        pe = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_PE_RATIO', start_date_yyyymmdd, unaffected_date_yyyymmdd,
                                                {'BEST_FPERIOD_OVERRIDE': fperiod}, api_host)
    if 'DVD yield' in multiples_to_query:
        dvd_yield = bbgclient.bbgclient.get_timeseries(ticker, 'DIVIDEND_INDICATED_YIELD', start_date_yyyymmdd,
                                                       unaffected_date_yyyymmdd, api_host=api_host)

    df = px.reset_index().rename(columns={'index': 'Date', 0: 'PX'})
    if 'FCF yield' in multiples_to_query:
        ebitda = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_EBITDA', start_date_yyyymmdd,
                                                    unaffected_date_yyyymmdd, {'BEST_FPERIOD_OVERRIDE': fperiod},
                                                    api_host).reset_index().rename(
            columns={'index': 'Date', 0: 'EBITDA'})
        opp = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_OPP', start_date_yyyymmdd, unaffected_date_yyyymmdd,
                                                 {'BEST_FPERIOD_OVERRIDE': fperiod}, api_host).reset_index().rename(
            columns={'index': 'Date', 0: 'OPP'})
        capex = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CAPEX', start_date_yyyymmdd, unaffected_date_yyyymmdd,
                                                   {'BEST_FPERIOD_OVERRIDE': fperiod}, api_host).reset_index().rename(
            columns={'index': 'Date', 0: 'CAPEX'})
        eqy_sh_out = bbgclient.bbgclient.get_timeseries(ticker, 'EQY_SH_OUT', start_date_yyyymmdd,
                                                        unaffected_date_yyyymmdd,
                                                        api_host=api_host).reset_index().rename(
            columns={'index': 'Date', 0: 'EQY_SH_OUT'})
        ni = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_NET_INCOME', start_date_yyyymmdd,
                                                unaffected_date_yyyymmdd, {'BEST_FPERIOD_OVERRIDE': fperiod},
                                                api_host).reset_index().rename(columns={'index': 'Date', 0: 'NI'})

        fcf = pd.merge(px.reset_index().rename(columns={'index': 'Date', 0: 'PX'}), ebitda, how='left',
                       on=['Date']).ffill().bfill()
        fcf = pd.merge(fcf, opp, how='left', on=['Date']).ffill().bfill()
        fcf = pd.merge(fcf, capex, how='left', on=['Date']).ffill().bfill()
        fcf = pd.merge(fcf, eqy_sh_out, how='left', on=['Date']).ffill().bfill()
        fcf = pd.merge(fcf, ni, how='left', on=['Date']).ffill().bfill()
        fcf['FCF'] = (fcf['NI'] + fcf['EBITDA'] - fcf['OPP'] + fcf['CAPEX']) / fcf['EQY_SH_OUT']
        fcf['FCF yield'] = fcf['FCF'] / fcf['PX']
        df = pd.merge(df, fcf[['Date', 'FCF yield']], how='left', on='Date').ffill().bfill()

    df = pd.merge(df, pe.reset_index().rename(columns={'index': 'Date', 0: 'P/EPS'}), how='left',
                  on=['Date']).ffill().bfill()
    df = pd.merge(df, ev_to_ebitda.reset_index().rename(columns={'index': 'Date', 0: 'EV/EBITDA'}), how='left',
                  on='Date').ffill().bfill()
    df = pd.merge(df, ev_to_sales.reset_index().rename(columns={'index': 'Date', 0: 'EV/Sales'}), how='left',
                  on='Date').ffill().bfill()
    df = pd.merge(df, dvd_yield.reset_index().rename(columns={'index': 'Date', 0: 'DVD yield'}), how='left',
                  on='Date').ffill().bfill()

    # Date     PX     P/EPS  EV/EBITDA  EV/Sales  DVD yield  FCF yield
    return df


def compare_multiples(y_mult_df, x_mult_df, mult_colname):
    if len(y_mult_df[~pd.isnull(y_mult_df[mult_colname])]) == 0: return pd.DataFrame(columns=['Date', 'Multiple Ratio'])
    if len(x_mult_df[~pd.isnull(x_mult_df[mult_colname])]) == 0: return pd.DataFrame(columns=['Date', 'Multiple Ratio'])
    df = pd.merge(x_mult_df[['Date', mult_colname]], y_mult_df[['Date', mult_colname]], how='right', on='Date')
    df['Multiple Ratio'] = df[mult_colname + '_y'] / df[mult_colname + '_x']
    return df[['Date', 'Multiple Ratio']].sort_values(by='Date')


def compute_implied_price_from_multiple(metric_name, multiple, mult_underlying_df):
    try:
        if metric_name == 'EV/EBITDA':
            ebitda = float(mult_underlying_df['BEST_EBITDA'].iloc[0])
            eqy_sh_out = float(mult_underlying_df['EQY_SH_OUT'].iloc[0])
            ev_component = float(mult_underlying_df['CUR_EV_COMPONENT'].iloc[0])
            return ((multiple * ebitda) - ev_component) / eqy_sh_out

        if metric_name == 'EV/Sales':
            sales = float(mult_underlying_df['BEST_SALES'].iloc[0])
            eqy_sh_out = float(mult_underlying_df['EQY_SH_OUT'].iloc[0])
            ev_component = float(mult_underlying_df['CUR_EV_COMPONENT'].iloc[0])
            return ((multiple * sales) - ev_component) / eqy_sh_out

        if metric_name == 'P/EPS':
            eps = float(mult_underlying_df['BEST_EPS'].iloc[0])
            return eps * multiple

        if metric_name == 'DVD yield':
            curr_dvd_yield = float(mult_underlying_df['DIVIDEND_INDICATED_YIELD'].iloc[0])
            curr_px = float(mult_underlying_df['PX'].iloc[0])
            curr_dvd = curr_dvd_yield * curr_px
            implied_px = curr_dvd / multiple
            return implied_px

        if metric_name == 'FCF yield':
            ni = float(mult_underlying_df['BEST_NET_INCOME'].iloc[0])
            ebitda = float(mult_underlying_df['BEST_EBITDA'].iloc[0])
            opp = float(mult_underlying_df['BEST_OPP'].iloc[0])
            capex = float(mult_underlying_df['BEST_CAPEX'].iloc[0])
            eqy_sh_out = float(mult_underlying_df['EQY_SH_OUT'].iloc[0])
            fcf = (ni + ebitda - opp + capex) / eqy_sh_out
            implied_px = fcf / multiple
            return implied_px

    except Exception as e:
        print('failed calculating implied price from multiple: ' + str(metric_name) + ' ' + str(e.args))
        return None


def compute_multiple_from_price(metric_name, price, mult_underlying_df):
    try:
        if metric_name == 'EV/EBITDA':
            ebitda = float(mult_underlying_df['BEST_EBITDA'].iloc[0])
            eqy_sh_out = float(mult_underlying_df['EQY_SH_OUT'].iloc[0])
            ev_component = float(mult_underlying_df['CUR_EV_COMPONENT'].iloc[0])
            return ((price * eqy_sh_out) + ev_component) / ebitda

        if metric_name == 'EV/Sales':
            sales = float(mult_underlying_df['BEST_SALES'].iloc[0])
            eqy_sh_out = float(mult_underlying_df['EQY_SH_OUT'].iloc[0])
            ev_component = float(mult_underlying_df['CUR_EV_COMPONENT'].iloc[0])
            return ((price * eqy_sh_out) + ev_component) / sales

        if metric_name == 'P/EPS':
            eps = float(mult_underlying_df['BEST_EPS'].iloc[0])
            return price / eps

        if metric_name == 'DVD yield':
            curr_dvd_yield = float(mult_underlying_df['DIVIDEND_INDICATED_YIELD'].iloc[0])
            curr_px = float(mult_underlying_df['PX'].iloc[0])
            curr_dvd = curr_dvd_yield * curr_px
            multiple = curr_dvd / price
            return multiple

        if metric_name == 'FCF yield':
            ni = float(mult_underlying_df['BEST_NET_INCOME'].iloc[0])
            ebitda = float(mult_underlying_df['BEST_EBITDA'].iloc[0])
            opp = float(mult_underlying_df['BEST_OPP'].iloc[0])
            capex = float(mult_underlying_df['BEST_CAPEX'].iloc[0])
            eqy_sh_out = float(mult_underlying_df['EQY_SH_OUT'].iloc[0])
            fcf = (ni + ebitda - opp + capex) / eqy_sh_out
            multiple = fcf / price
            return multiple

    except Exception as e:
        print('failed calculating implied price from multiple: ' + str(metric_name) + ' ' + str(e.args))
        return None


def calibration_data(alpha_ticker, peer2weight, start_date_yyyy_mm_dd, end_date_yyyy_mm_dd, metrics, api_host, fperiod):
    peer_tickers = list(peer2weight.keys())
    alpha_historical_mult = multiples_df(alpha_ticker, start_date_yyyy_mm_dd.strftime('%Y%m%d'),
                                         end_date_yyyy_mm_dd.strftime('%Y%m%d'), api_host, fperiod)
    peer2historical_mult = {
        p: multiples_df(p, start_date_yyyy_mm_dd.strftime('%Y%m%d'), end_date_yyyy_mm_dd.strftime('%Y%m%d'), api_host,
                        fperiod, multiples_to_query=metrics) for p in peer_tickers}

    metric2rel = {}
    for metric in metrics:
        alpha_over_peers_df = pd.DataFrame()
        alpha_over_peers_df['Date'] = alpha_historical_mult['Date']
        alpha_over_peer_df_list = []
        tot_adj_weight = 0
        peers_included = []
        for (peer, weight) in peer2weight.items():
            peer_mult = peer2historical_mult[peer]
            alpha_over_peer_df = compare_multiples(alpha_historical_mult, peer_mult, metric)
            if len(alpha_over_peer_df) > 0:
                tot_adj_weight += weight
                peers_included.append(peer)
                alpha_over_peers_df = pd.merge(alpha_over_peers_df, alpha_over_peer_df, how='left', on='Date').rename(
                    columns={'Multiple Ratio': 'vs. ' + peer})
                alpha_over_peer_df_list.append(
                    alpha_over_peer_df[['Date', 'Multiple Ratio']].rename(columns={'Multiple Ratio': 'vs. ' + peer}))

        peer2adj_weight = {p: (peer2weight[p] / tot_adj_weight) for p in peers_included}
        for p in peer2adj_weight:
            alpha_over_peers_df['vs. ' + p + '(weighted)'] = peer2adj_weight[p] * alpha_over_peers_df['vs. ' + p]

        alpha_over_peers_df['vs. all peers'] = alpha_over_peers_df[
            ['vs. ' + p + '(weighted)' for p in peers_included]].sum(axis=1)

        mu = alpha_over_peers_df['vs. all peers'].mean()
        sigma = alpha_over_peers_df['vs. all peers'].std()

        metric2rel[metric] = {
            'Mu': mu,
            'Sigma': sigma,
            'Alpha vs. all peers, dataframe': alpha_over_peers_df,
            'Alpha vs. each peer, list': alpha_over_peer_df_list,
            'Peers adjusted weight': peer2adj_weight
        }

    return {
        'metric2rel': metric2rel,
        'alpha_historical_mult_df': alpha_historical_mult,
        'peer2historical_mult_df': peer2historical_mult
    }


def metric2implied_px(alpha_ticker, peer_tickers, dt, metrics, api_host, metric2stat_rel, adjustments_df=None,
                      fperiod='1BF'):
    slicer = dfutils.df_slicer()

    start_date_yyyymmdd = slicer.prev_n_business_days(100, dt).strftime('%Y%m%d')
    # alpha_mult_df = multiples_df(alpha_ticker,start_date_yyyymmdd, dt.strftime('%Y%m%d'),api_host,fperiod=fperiod)
    peer2mult_df = {
        p: multiples_df(p, start_date_yyyymmdd, dt.strftime('%Y%m%d'), api_host, fperiod, multiples_to_query=metrics)
    for p
        in peer_tickers}
    alpha_mult_underlying_df = multiple_underlying_df(alpha_ticker, dt.strftime('%Y%m%d'), api_host, fperiod)

    metric2data = {m: {} for m in metrics}
    for metric in metrics:
        # alpha_mult = alpha_mult_df[metric].iloc[-1]
        # alpha_px = alpha_mult_df['PX'].iloc[-1]
        alpha_balance_sheet_df = alpha_mult_underlying_df[alpha_mult_underlying_df['Date'] == dt.strftime('%Y-%m-%d')]
        peer2mult = {p: peer2mult_df[p][metric].iloc[-1] for p in peer_tickers}
        stat_rel = metric2stat_rel[metric]
        mu = stat_rel['Mu']
        sigma = stat_rel['Sigma']
        peer2adj_weight = stat_rel['Peers adjusted weight']
        peers_multiple = sum(
            [(peer2adj_weight[p] * peer2mult[p] if p in peer2adj_weight else 0.0) for p in peer_tickers])

        implied_multiple_high = (mu + 2 * sigma) * peers_multiple
        implied_multiple_mean = mu * peers_multiple
        implied_multiple_low = (mu - 2 * sigma) * peers_multiple

        if metric in ['FCF yield', 'DVD yield']:  # flip
            tmp = implied_multiple_high
            implied_multiple_high = implied_multiple_low
            implied_multiple_low = tmp

        metric2data[metric]['Alpha implied multiple (high)'] = implied_multiple_high
        metric2data[metric]['Alpha implied multiple (mean)'] = implied_multiple_mean
        metric2data[metric]['Alpha implied multiple (low)'] = implied_multiple_low
        metric2data[metric]['Alpha Balance Sheet DataFrame'] = alpha_balance_sheet_df
        # metric2data[metric]['Alpha observed multiple'] = alpha_mult ### takes extra api call, use only if needed
        metric2data[metric]['Peers multiple'] = peers_multiple
        metric2data[metric]['Peer2Multiple'] = peer2mult
        metric2data[metric]['Alpha Unaffected PX (-2sigma)'] = compute_implied_price_from_multiple(metric,
                                                                                                    implied_multiple_low,
                                                                                                    alpha_balance_sheet_df)
        metric2data[metric]['Alpha Unaffected PX (avg)'] = compute_implied_price_from_multiple(metric,
                                                                                               implied_multiple_mean,
                                                                                               alpha_balance_sheet_df)
        metric2data[metric]['Alpha Unaffected PX (+2sigma)'] = compute_implied_price_from_multiple(metric,
                                                                                                   implied_multiple_high,
                                                                                                   alpha_balance_sheet_df)
        # metric2data[metric]['Alpha PX'] = alpha_px

    return metric2data


def premium_analysis_df_OLS(alpha_ticker, peer_ticker_list, calib_data, analyst_upside, analyst_downside,
                            analyst_pt_wic, as_of_dt, price_tgt_dt, metrics, metric2weight, api_host,
                            adjustments_df_bear, adjustments_df_bull, adjustments_df_pt, bear_flag=None, bull_flag=None,
                            pt_flag=None):
    alpha_historical_mult_df = calib_data['alpha_historical_mult_df']
    peer2historical_mult_df = calib_data['peer2historical_mult_df']
    ticker2short_ticker = {p: p.split(' ')[0] for p in peer_ticker_list + [alpha_ticker]}

    rows = []
    metric2peer2coeff = {m: {} for m in metrics}
    for metric in metrics:
        m_df = alpha_historical_mult_df[['Date', metric]].rename(columns={metric: ticker2short_ticker[alpha_ticker]})
        for p in peer2historical_mult_df:
            m_df = pd.merge(m_df, peer2historical_mult_df[p][['Date', metric]], how='left', on='Date').rename(
                columns={metric: ticker2short_ticker[p]})
        peer_ticker_list = [p for p in peer_ticker_list if
                            len(m_df[~pd.isnull(m_df[p.split(' ')[0]])]) > 0]  # remove peers with all nulls
        m_ols_df = m_df[[alpha_ticker.split(' ')[0]] + [t.split(' ')[0] for t in peer_ticker_list]]
        # regress a vs. p1,p2,...,pn
        formula = alpha_ticker.split(' ')[0] + ' ~ ' + " + ".join([t.split(' ')[0] for t in peer_ticker_list])
        ols_result = sm.ols(formula=formula, data=m_ols_df).fit()
        peer2coeff = {p: ols_result.params[p.split(' ')[0]] for p in peer_ticker_list}
        peer2coeff['Intercept'] = ols_result.params['Intercept']
        metric2peer2coeff[metric] = peer2coeff
        rows.append([metric, ols_result.params.to_dict()] + [peer2coeff[p] for p in peer_ticker_list] + [
            peer2coeff['Intercept']])

    slicer = dfutils.df_slicer()
    peer2ptd_multiple = {p: multiples_df(p, slicer.prev_n_business_days(100, price_tgt_dt).strftime('%Y%m%d'),
                                         price_tgt_dt.strftime('%Y%m%d'), api_host, fperiod='1BF',
                                         multiples_to_query=metrics) for p in peer_ticker_list}
    peer2now_multiple = {
        p: multiples_df(p, slicer.prev_n_business_days(100, as_of_dt).strftime('%Y%m%d'), as_of_dt.strftime('%Y%m%d'),
                        api_host, fperiod='1BF', multiples_to_query=metrics) for p in peer_ticker_list}
    alpha_balance_sheet_df_ptd = multiple_underlying_df(alpha_ticker, price_tgt_dt, api_host, fperiod='1BF')
    # alpha_balance_sheet_df_now = multiple_underlying_df(alpha_ticker,as_of_dt,api_host,fperiod='1BF')

    df = pd.DataFrame(columns=['Metric', 'Coefficients'] + peer_ticker_list + ['Intercept'], data=rows)

    df['Alpha Upside (analyst)'] = analyst_upside
    df['Alpha Downside (analyst)'] = analyst_downside
    df['Alpha PT WIC (analyst)'] = analyst_pt_wic

    df['Peers Multiples DataFrame @ Price Target Date'] = df['Metric'].apply(
        lambda m: pd.DataFrame(columns=['Peer', 'Multiple'],
                               data=[(p, peer2ptd_multiple[p][m].fillna(0).iloc[-1]) for p in peer_ticker_list]))
    df['Peers Multiples @ Price Target Date'] = df['Metric'].apply(
        lambda m: {p: peer2ptd_multiple[p][m].fillna(0).iloc[-1] for p in peer_ticker_list})
    df['Alpha Implied Multiple @ Price Target Date'] = df['Metric'].apply(lambda m: sum(
        [metric2peer2coeff[m][p] * peer2ptd_multiple[p][m].fillna(0).iloc[-1] for p in peer_ticker_list]) +
                                                                                    metric2peer2coeff[m]['Intercept'])


    if adjustments_df_bear is None:
        alpha_balance_sheet_df_bear = alpha_balance_sheet_df_ptd
        df['Alpha Balance Sheet DataFrame (Bear Case)'] = [alpha_balance_sheet_df_bear] * len(df)
        df['Alpha Bear Multiple @ Price Target Date'] = [
            compute_multiple_from_price(m, analyst_downside, alpha_balance_sheet_df_bear) for (m, price) in
            zip(df['Metric'], df['Alpha Downside (analyst)'])]
    else:
        if bear_flag is None:
            adjustments = ast.literal_eval(adjustments_df_bear)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bear = alpha_balance_sheet_df_ptd.add(adjustments_df, axis='columns')
            df['Alpha Balance Sheet DataFrame (Bear Case)'] = [alpha_balance_sheet_df_bear] * len(df)
            df['Alpha Bear Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_downside, alpha_balance_sheet_df_bear) for (m, price) in
                zip(df['Metric'], df['Alpha Downside (analyst)'])]
        else:
            adjustments = ast.literal_eval(adjustments_df_bear)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bear = adjustments_df
            df['Alpha Balance Sheet DataFrame (Bear Case)'] = [alpha_balance_sheet_df_bear] * len(df)
            df['Alpha Bear Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_downside, alpha_balance_sheet_df_bear) for (m, price) in
                zip(df['Metric'], df['Alpha Downside (analyst)'])]

    if adjustments_df_bull is None:
        alpha_balance_sheet_df_bull = alpha_balance_sheet_df_ptd
        df['Alpha Balance Sheet DataFrame (Bull Case)'] = [alpha_balance_sheet_df_bull] * len(df)
        df['Alpha Bull Multiple @ Price Target Date'] = [
            compute_multiple_from_price(m, analyst_upside, alpha_balance_sheet_df_bull) for (m, price) in
            zip(df['Metric'], df['Alpha Upside (analyst)'])]
    else:
        if bull_flag is None:
            adjustments = ast.literal_eval(adjustments_df_bull)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bull = alpha_balance_sheet_df_ptd.add(adjustments_df, axis='columns')
            df['Alpha Balance Sheet DataFrame (Bull Case)'] = [alpha_balance_sheet_df_bull] * len(df)
            df['Alpha Bull Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_upside, alpha_balance_sheet_df_bull) for (m, price) in
                zip(df['Metric'], df['Alpha Upside (analyst)'])]
        else:
            adjustments = ast.literal_eval(adjustments_df_bear)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bull = adjustments_df
            df['Alpha Balance Sheet DataFrame (Bull Case)'] = [alpha_balance_sheet_df_bull] * len(df)
            df['Alpha Bull Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_upside, alpha_balance_sheet_df_bull) for (m, price) in
                zip(df['Metric'], df['Alpha Upside (analyst)'])]

    if adjustments_df_pt is None:
        alpha_balance_sheet_df_pt = alpha_balance_sheet_df_ptd
        df['Alpha Balance Sheet DataFrame (PT WIC Case)'] = [alpha_balance_sheet_df_pt] * len(df)
        df['Alpha PT WIC Multiple @ Price Target Date'] = [
            compute_multiple_from_price(m, analyst_pt_wic, alpha_balance_sheet_df_ptd) for (m, price) in
            zip(df['Metric'], df['Alpha PT WIC (analyst)'])]
    else:
        if pt_flag is None:
            adjustments = ast.literal_eval(adjustments_df_pt)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_pt = alpha_balance_sheet_df_ptd.add(adjustments_df, axis='columns')
            df['Alpha Balance Sheet DataFrame (PT WIC Case)'] = [alpha_balance_sheet_df_pt] * len(df)
            df['Alpha PT WIC Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_pt_wic, alpha_balance_sheet_df_pt) for (m, price) in
                zip(df['Metric'], df['Alpha PT WIC (analyst)'])]
        else:
            adjustments = ast.literal_eval(adjustments_df_pt)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_pt = adjustments_df
            df['Alpha Balance Sheet DataFrame (PT WIC Case)'] = [alpha_balance_sheet_df_pt] * len(df)
            df['Alpha PT WIC Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_pt_wic, alpha_balance_sheet_df_pt) for (m, price) in
                zip(df['Metric'], df['Alpha PT WIC (analyst)'])]

    df['Premium Bear (%)'] = (((df['Alpha Bear Multiple @ Price Target Date'] / df[
        'Alpha Implied Multiple @ Price Target Date']) * 100.0) - 100.0).astype(float)
    df['Premium PT WIC (%)'] = (((df['Alpha PT WIC Multiple @ Price Target Date'] / df[
        'Alpha Implied Multiple @ Price Target Date']) * 100.0) - 100.0).astype(float)
    df['Premium Bull (%)'] = (((df['Alpha Bull Multiple @ Price Target Date'] / df[
        'Alpha Implied Multiple @ Price Target Date']) * 100.0) - 100.0).astype(float)

    df['Peers Multiples DataFrame @ Now'] = df['Metric'].apply(lambda m: pd.DataFrame(columns=['Peer', 'Multiple'],
                                                                                      data=[(p, peer2now_multiple[p][
                                                                                          m].fillna(0).iloc[-1]) for p
                                                                                            in peer_ticker_list]))
    df['Peers Multiples @ Now'] = df['Metric'].apply(
        lambda m: {p: peer2now_multiple[p][m].fillna(0).iloc[-1] for p in peer_ticker_list})
    df['Alpha Implied Multiple @ Now'] = df['Metric'].apply(lambda m: sum(
        [metric2peer2coeff[m][p] * peer2now_multiple[p][m].fillna(0).iloc[-1] for p in peer_ticker_list]) +
                                                                      metric2peer2coeff[m]['Intercept'])

    df['Alpha Bear Multiple @ Now'] = (
            df['Alpha Implied Multiple @ Now'] * (1 + (df['Premium Bear (%)'] / 100.0))).astype(float)
    df['Alpha PT WIC Multiple @ Now'] = (
            df['Alpha Implied Multiple @ Now'] * (1 + (df['Premium PT WIC (%)'] / 100.0))).astype(float)
    df['Alpha Bull Multiple @ Now'] = (
            df['Alpha Implied Multiple @ Now'] * (1 + (df['Premium Bull (%)'] / 100.0))).astype(float)

    df['Alpha Downside'] = [compute_implied_price_from_multiple(m, mult, alpha_balance_sheet_df_bear) for (m, mult) in
                            zip(df['Metric'], df['Alpha Bear Multiple @ Now'])]
    df['Alpha PT WIC'] = [compute_implied_price_from_multiple(m, mult, alpha_balance_sheet_df_pt) for (m, mult) in
                          zip(df['Metric'], df['Alpha PT WIC Multiple @ Now'])]
    df['Alpha Upside'] = [compute_implied_price_from_multiple(m, mult, alpha_balance_sheet_df_bull) for (m, mult) in
                          zip(df['Metric'], df['Alpha Bull Multiple @ Now'])]

    df['Alpha Downside (Adj,weighted)'] = df['Alpha Downside'] * df['Metric'].apply(lambda m: metric2weight[m]).astype(
        float)
    df['Alpha PT WIC (Adj,weighted)'] = df['Alpha PT WIC'] * df['Metric'].apply(lambda m: metric2weight[m]).astype(
        float)
    df['Alpha Upside (Adj,weighted)'] = df['Alpha Upside'] * df['Metric'].apply(lambda m: metric2weight[m]).astype(
        float)

    return df


def premium_analysis_df(alpha_ticker, peers, as_of_dt, last_price_target_dt, analyst_upside, analyst_downside,
                        analyst_pt_wic, metrics, metric2weight, metric2stat_rel, api_host, adjustments_df_bear=None,
                        adjustments_df_bull=None, adjustments_df_pt=None, bear_flag=None, bull_flag=None, pt_flag=None):
    metric2implied_now = metric2implied_px(alpha_ticker, peers, as_of_dt, metrics, api_host, metric2stat_rel,
                                           fperiod='1BF')
    metric2implied_at_price_tgt_date = metric2implied_px(alpha_ticker, peers, last_price_target_dt, metrics, api_host,
                                                         metric2stat_rel, fperiod='BF')

    df = pd.DataFrame()
    df['Metric'] = metrics
    df['Alpha to Peer historical ratio (mean)'] = df['Metric'].apply(lambda m: metric2stat_rel[m]['Mu'])
    df['Alpha to Peer historical ratio (std)'] = df['Metric'].apply(lambda m: metric2stat_rel[m]['Sigma'])

    df['Peers Composite Multiple @ Price Target Date'] = df['Metric'].apply(
        lambda m: metric2implied_at_price_tgt_date[m]['Peers multiple'])
    df['Peer2Multiple @ Price Target Date'] = df['Metric'].apply(
        lambda m: metric2implied_at_price_tgt_date[m]['Peer2Multiple'])
    df['Alpha Implied Multiple (mean) @ Price Target Date'] = df['Metric'].apply(
        lambda m: metric2implied_at_price_tgt_date[m]['Alpha implied multiple (mean)'])
    df['Alpha Balance Sheet @ Price Target Date'] = df['Metric'].apply(
        lambda m: metric2implied_at_price_tgt_date[m]['Alpha Balance Sheet DataFrame'])
    df['Alpha Unaffected PX @ Price Target Date'] = df['Metric'].apply(
        lambda m: metric2implied_at_price_tgt_date[m]['Alpha Unaffected PX (avg)'])
    alpha_balance_sheet_df_ptd = df['Alpha Balance Sheet @ Price Target Date'][0]

    df['Alpha Upside (analyst)'] = analyst_upside
    df['Alpha Downside (analyst)'] = analyst_downside
    df['Alpha PT WIC (analyst)'] = analyst_pt_wic

    if adjustments_df_bear is None:
        alpha_balance_sheet_df_bear = alpha_balance_sheet_df_ptd
        df['Alpha Balance Sheet DataFrame (Bear Case)'] = [alpha_balance_sheet_df_bear] * len(df)
        df['Alpha Bear Multiple @ Price Target Date'] = [
            compute_multiple_from_price(m, analyst_downside, alpha_balance_sheet_df_bear) for (m, price) in
            zip(df['Metric'], df['Alpha Downside (analyst)'])]
    else:
        if bear_flag is None:
            adjustments = ast.literal_eval(adjustments_df_bear)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bear = alpha_balance_sheet_df_ptd.add(adjustments_df, axis='columns')
            df['Alpha Balance Sheet DataFrame (Bear Case)'] = [alpha_balance_sheet_df_bear] * len(df)
            df['Alpha Bear Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_downside, alpha_balance_sheet_df_bear) for (m, price) in
                zip(df['Metric'], df['Alpha Downside (analyst)'])]
        else:
            adjustments = ast.literal_eval(adjustments_df_bear)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bear = adjustments_df
            df['Alpha Balance Sheet DataFrame (Bear Case)'] = [alpha_balance_sheet_df_bear] * len(df)
            df['Alpha Bear Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_downside, alpha_balance_sheet_df_bear) for (m, price) in
                zip(df['Metric'], df['Alpha Downside (analyst)'])]

    if adjustments_df_bull is None:
        alpha_balance_sheet_df_bull = alpha_balance_sheet_df_ptd
        df['Alpha Balance Sheet DataFrame (Bull Case)'] = [alpha_balance_sheet_df_bull] * len(df)
        df['Alpha Bull Multiple @ Price Target Date'] = [
            compute_multiple_from_price(m, analyst_upside, alpha_balance_sheet_df_bull) for (m, price) in
            zip(df['Metric'], df['Alpha Upside (analyst)'])]
    else:
        if bull_flag is None:
            adjustments = ast.literal_eval(adjustments_df_bull)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bull = alpha_balance_sheet_df_ptd.add(adjustments_df, axis='columns')
            df['Alpha Balance Sheet DataFrame (Bull Case)'] = [alpha_balance_sheet_df_bull] * len(df)
            df['Alpha Bull Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_upside, alpha_balance_sheet_df_bull) for (m, price) in
                zip(df['Metric'], df['Alpha Upside (analyst)'])]
        else:
            adjustments = ast.literal_eval(adjustments_df_bear)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_bull = adjustments_df
            df['Alpha Balance Sheet DataFrame (Bull Case)'] = [alpha_balance_sheet_df_bull] * len(df)
            df['Alpha Bull Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_upside, alpha_balance_sheet_df_bull) for (m, price) in
                zip(df['Metric'], df['Alpha Upside (analyst)'])]

    if adjustments_df_pt is None:
        alpha_balance_sheet_df_pt = alpha_balance_sheet_df_ptd
        df['Alpha Balance Sheet DataFrame (PT WIC Case)'] = [alpha_balance_sheet_df_pt] * len(df)
        df['Alpha PT WIC Multiple @ Price Target Date'] = [
            compute_multiple_from_price(m, analyst_pt_wic, alpha_balance_sheet_df_ptd) for (m, price) in
            zip(df['Metric'], df['Alpha PT WIC (analyst)'])]
    else:
        if pt_flag is None:
            adjustments = ast.literal_eval(adjustments_df_pt)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_pt = alpha_balance_sheet_df_ptd.add(adjustments_df, axis='columns')
            df['Alpha Balance Sheet DataFrame (PT WIC Case)'] = [alpha_balance_sheet_df_pt] * len(df)
            df['Alpha PT WIC Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_pt_wic, alpha_balance_sheet_df_pt) for (m, price) in
                zip(df['Metric'], df['Alpha PT WIC (analyst)'])]
        else:
            adjustments = ast.literal_eval(adjustments_df_pt)[0]
            adjustments_df = pd.DataFrame.from_dict(adjustments, orient='index')
            adjustments_df = adjustments_df.T
            adjustments_df = adjustments_df.drop(columns='Date')
            cols = adjustments_df.columns
            adjustments_df[cols] = adjustments_df[cols].apply(pd.to_numeric)
            alpha_balance_sheet_df_pt = adjustments_df
            df['Alpha Balance Sheet DataFrame (PT WIC Case)'] = [alpha_balance_sheet_df_pt] * len(df)
            df['Alpha PT WIC Multiple @ Price Target Date'] = [
                compute_multiple_from_price(m, analyst_pt_wic, alpha_balance_sheet_df_pt) for (m, price) in
                zip(df['Metric'], df['Alpha PT WIC (analyst)'])]

    df['Peers Composite Multiple @ Now'] = df['Metric'].apply(lambda m: metric2implied_now[m]['Peers multiple'])
    df['Peer2Multiple @ Now'] = df['Metric'].apply(lambda m: metric2implied_now[m]['Peer2Multiple'])
    df['Alpha Implied Multiple (mean) @ Now'] = df['Metric'].apply(
        lambda m: metric2implied_now[m]['Alpha implied multiple (mean)'])

    df['Premium Bear (%)'] = (((df['Alpha Bear Multiple @ Price Target Date'] / df[
        'Alpha Implied Multiple (mean) @ Price Target Date']) * 100.0) - 100.0).astype(float)
    df['Premium PT WIC (%)'] = (((df['Alpha PT WIC Multiple @ Price Target Date'] / df[
        'Alpha Implied Multiple (mean) @ Price Target Date']) * 100.0) - 100.0).astype(float)
    df['Premium Bull (%)'] = (((df['Alpha Bull Multiple @ Price Target Date'] / df[
        'Alpha Implied Multiple (mean) @ Price Target Date']) * 100.0) - 100.0).astype(float)

    df['Alpha Bear Multiple @ Now'] = (
            df['Alpha Implied Multiple (mean) @ Now'] * (1 + (df['Premium Bear (%)'] / 100.0))).astype(float)
    df['Alpha PT WIC Multiple @ Now'] = (
            df['Alpha Implied Multiple (mean) @ Now'] * (1 + (df['Premium PT WIC (%)'] / 100.0))).astype(float)
    df['Alpha Bull Multiple @ Now'] = (
            df['Alpha Implied Multiple (mean) @ Now'] * (1 + (df['Premium Bull (%)'] / 100.0))).astype(float)

    df['Alpha Downside'] = [compute_implied_price_from_multiple(m, mult, alpha_balance_sheet_df_bear) for (m, mult) in
                            zip(df['Metric'], df['Alpha Bear Multiple @ Now'])]
    df['Alpha PT WIC'] = [compute_implied_price_from_multiple(m, mult, alpha_balance_sheet_df_pt) for (m, mult) in
                          zip(df['Metric'], df['Alpha PT WIC Multiple @ Now'])]
    df['Alpha Upside'] = [compute_implied_price_from_multiple(m, mult, alpha_balance_sheet_df_bull) for (m, mult) in
                          zip(df['Metric'], df['Alpha Bull Multiple @ Now'])]

    df['Alpha Downside (Adj,weighted)'] = df['Alpha Downside'] * df['Metric'].apply(lambda m: metric2weight[m]).astype(
        float)
    df['Alpha PT WIC (Adj,weighted)'] = df['Alpha PT WIC'] * df['Metric'].apply(lambda m: metric2weight[m]).astype(
        float)
    df['Alpha Upside (Adj,weighted)'] = df['Alpha Upside'] * df['Metric'].apply(lambda m: metric2weight[m]).astype(
        float)


    return df
