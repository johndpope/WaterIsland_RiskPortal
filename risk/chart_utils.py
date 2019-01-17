import bbgclient
import pandas as pd

def get_fcf_yield(ticker, start_date_yyyymmdd, end_date_yyyymmdd, fperiod='1BF'):
    ''' Calculates FCF Yield and Returns a Series object '''
    api_host = bbgclient.bbgclient.get_next_available_host()
    px = bbgclient.bbgclient.get_timeseries(ticker, 'PX_LAST', start_date_yyyymmdd, end_date_yyyymmdd,api_host=api_host).reset_index().rename(columns={'index': 'Date', 0: 'PX'})
    best_estimate_fcf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_ESTIMATE_FCF', start_date_yyyymmdd, end_date_yyyymmdd,{'BEST_FPERIOD_OVERRIDE': fperiod}, api_host).reset_index().rename(columns={'index': 'Date', 0: 'BEST_ESTIMATE_FCF'})
    ni = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_NET_INCOME', start_date_yyyymmdd, end_date_yyyymmdd,{'BEST_FPERIOD_OVERRIDE': fperiod}, api_host).reset_index().rename(columns={'index': 'Date', 0: 'NI'})
    eps = bbgclient.bbgclient.get_timeseries(ticker,'BEST_EPS',start_date_yyyymmdd,end_date_yyyymmdd,{'BEST_FPERIOD_OVERRIDE':fperiod},api_host).reset_index().rename(columns={'index':'Date',0:'EPS'})

    fcf = pd.merge(px, best_estimate_fcf, how='left',on=['Date']).ffill().bfill()
    fcf = pd.merge(fcf, ni, how='left', on=['Date']).ffill().bfill()
    fcf = pd.merge(fcf,eps, how='left', on=['Date']).ffill().bfill()
    fcf['FCF'] = (fcf['BEST_ESTIMATE_FCF'])/(fcf['NI']/fcf['EPS'])
    fcf['FCF yield'] = fcf['FCF'] / fcf['PX']
    return fcf[['Date','FCF yield']]

def get_ev_ebitda(ticker, start_date_yyyymmdd, end_date_yyyymmdd, best_fperiod_override, mneumonic='BEST_CUR_EV_TO_EBITDA'):
    api_host = bbgclient.bbgclient.get_next_available_host()
    ev_ebitda_data_points = bbgclient.bbgclient.get_timeseries(ticker, mneumonic, start_date_yyyymmdd, end_date_yyyymmdd, {'BEST_FPERIOD_OVERRIDE': best_fperiod_override}, api_host)
    return '' if len(ev_ebitda_data_points)==0 else ev_ebitda_data_points

def get_pe_ratio(ticker, start_date_yyyymmdd, end_date_yyyymmdd, best_fperiod_override, mneumonic='BEST_PE_RATIO'):
    api_host = bbgclient.bbgclient.get_next_available_host()
    pe_ratio_data_points = bbgclient.bbgclient.get_timeseries(ticker, mneumonic, start_date_yyyymmdd, end_date_yyyymmdd, {'BEST_FPERIOD_OVERRIDE':best_fperiod_override},api_host)
    return '' if len(pe_ratio_data_points) == 0 else pe_ratio_data_points