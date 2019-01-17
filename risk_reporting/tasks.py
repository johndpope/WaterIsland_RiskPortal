from celery import shared_task
import pandas as pd
from .models import ArbNAVImpacts, DailyNAVImpacts
from bbgclient import bbgclient
from django_slack import slack_message
import numpy as np
from tabulate import tabulate
api_host = bbgclient.get_next_available_host()

@shared_task
def update_merger_arb_nav_impacts():
    from sqlalchemy import create_engine

    engine = create_engine("mysql://root:Mkaymkay1@10.16.1.19/test_wic_db")
    con = engine.connect()
    # Get the Dataframe from models
    nav_impacts_positions_df = pd.DataFrame.from_records(ArbNAVImpacts.objects.all().values())

    #Fetching Latest Prices from Bloomberg.....
    print('Fetching latest prices from Bloomberg....')

    def last_price_cascade_logic(row):
        ''' Takes in a Dataframe row and fetches last price. If bloomberg returns None, revert to original price....'''
        if row['SecType'] == 'EQ': #Only for Equities
            last_px = bbgclient.get_secid2field([row['Underlying']+" Equity"], 'tickers', ['CRNCY_ADJ_PX_LAST'], req_type='refdata',overrides_dict={'EQY_FUND_CRNCY':'USD'}, api_host=api_host)[row['Underlying']+ " Equity"]['CRNCY_ADJ_PX_LAST'][0]
            if last_px is None:
                last_px = row['LastPrice']
        else:
            last_px = row['LastPrice']
        return last_px



    nav_impacts_positions_df['LastPrice'] = nav_impacts_positions_df.apply(last_price_cascade_logic, axis=1)


    float_cols = ['DealTermsCash', 'DealTermsStock', 'DealValue', 'NetMktVal', 'FxFactor', 'Capital',
                  'BaseCaseNavImpact', 'RiskLimit',
                  'OutlierNavImpact', 'QTY', 'NAV', 'PM_BASE_CASE', 'Outlier', 'StrikePrice', 'LastPrice']

    nav_impacts_positions_df[float_cols] = nav_impacts_positions_df[float_cols].astype(float)
    nav_impacts_positions_df['CurrMktVal'] = nav_impacts_positions_df['QTY'] * nav_impacts_positions_df['LastPrice']
    # Calculate the Impacts
    nav_impacts_positions_df['PL_BASE_CASE'] = nav_impacts_positions_df.apply(calculate_pl_base_case, axis=1)
    nav_impacts_positions_df['BASE_CASE_NAV_IMPACT'] = nav_impacts_positions_df.apply(calculate_base_case_nav_impact,
                                                                                      axis=1)
    # Calculate Outlier Impacts
    nav_impacts_positions_df['OUTLIER_PL'] = nav_impacts_positions_df.apply(calculate_outlier_pl, axis=1)
    nav_impacts_positions_df['OUTLIER_NAV_IMPACT'] = nav_impacts_positions_df.apply(calculate_outlier_nav_impact,
                                                                                    axis=1)
    nav_impacts_positions_df.rename(columns={'TG': 'TradeGroup'}, inplace=True)  # Rename to TradeGroup
    # Sum Impacts of Individual Securities for Impacts @ TradeGroup level...
    nav_impacts_positions_df = nav_impacts_positions_df.round({'BASE_CASE_NAV_IMPACT': 2, 'OUTLIER_NAV_IMPACT': 2})
    nav_impacts_positions_df.to_csv('nav_impactsbeforegoruping.csv')
    nav_impacts_sum_df = nav_impacts_positions_df.groupby(['TradeGroup', 'FundCode', 'PM_BASE_CASE', 'RiskLimit']).agg(
        {'BASE_CASE_NAV_IMPACT': 'sum', 'OUTLIER_NAV_IMPACT': 'sum'})



    nav_impacts_sum_df = pd.pivot_table(nav_impacts_sum_df, index=['TradeGroup', 'RiskLimit'], columns='FundCode',aggfunc=np.sum,
                                        fill_value='N/A')

    nav_impacts_sum_df.columns = ["_".join((i, j)) for i, j in nav_impacts_sum_df.columns]
    nav_impacts_sum_df.reset_index(inplace=True)

    #Clear Previous DailyNavImpacts
    DailyNAVImpacts.objects.all().delete()

    #Post new Impacts on Slack Channel



    nav_impacts_sum_df.to_sql(con=con, if_exists='append', index=False, name='risk_reporting_dailynavimpacts',
                              schema='test_wic_db')


    real_time_arb_impacts = pd.read_sql_query('select TradeGroup, RiskLimit, BASE_CASE_NAV_IMPACT_ARB from test_wic_db.risk_reporting_dailynavimpacts where abs(RiskLimit) < abs(BASE_CASE_NAV_IMPACT_ARB) and BASE_CASE_NAV_IMPACT_ARB <> \'N/A\'', con=con)

    slack_message('navinspector.slack', {'impacts': tabulate(real_time_arb_impacts, tablefmt='fancy_grid')})
    con.close()

# Following NAV Impacts Utilities
def calculate_pl_base_case(row):
    if row['SecType'] != 'EXCHOPT':
        return (row['PM_BASE_CASE'] * row['FxFactor'] * row['QTY']) - (row['CurrMktVal'])
    else:
        if row['PutCall'] == 'CALL':
            if row['StrikePrice'] <= row['PM_BASE_CASE']:
                x = (row['PM_BASE_CASE'] - row['StrikePrice']) * (row['QTY']) * row['FxFactor']
            else:
                x = 0
        elif row['PutCall'] == 'PUT':
            if row['StrikePrice'] >= row['PM_BASE_CASE']:
                x = (row['StrikePrice'] - row['PM_BASE_CASE']) * (row['QTY']) * row['FxFactor']
            else:
                x = 0
        return -row['CurrMktVal'] + x


def calculate_base_case_nav_impact(row):
    return ((row['PL_BASE_CASE'] / row['NAV']) * 100)


def calculate_outlier_pl(row):
    if row['SecType'] != 'EXCHOPT':
        return (row['Outlier'] * row['FxFactor'] * row['QTY']) - (row['CurrMktVal'])
    else:
        if row['PutCall'] == 'CALL':
            if row['StrikePrice'] <= row['Outlier']:
                x = (row['Outlier'] - row['StrikePrice']) * (row['QTY']) * row['FxFactor']
            else:
                x = 0
        elif row['PutCall'] == 'PUT':
            if row['StrikePrice'] >= row['Outlier']:
                x = (row['StrikePrice'] - row['Outlier']) * row['QTY'] * row['FxFactor']
            else:
                x = 0

        return -row['CurrMktVal'] + x


def calculate_outlier_nav_impact(row):
    return ((row['OUTLIER_PL'] / row['NAV']) * 100)