import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import django
django.setup()
from celery import shared_task
from django.db import connection
import pandas as pd
from risk_reporting.models import ArbNAVImpacts, DailyNAVImpacts
from bbgclient import bbgclient
from django_slack import slack_message
import numpy as np
from tabulate import tabulate
api_host = bbgclient.get_next_available_host()
from django.conf import settings
from sqlalchemy.exc import OperationalError
import time
@shared_task
def refresh_base_case_and_outlier_downsides():
    ''' Refreshes the base case and outlier downsides every 20 minutes for dynamically linked downsides '''
    import pandas as pd
    import bbgclient

    con = settings.SQLALCHEMY_CONNECTION
    try:
        con.execute('Select 1 as is_alive')  # Check to see if Database is alive
    except OperationalError as oe:
        print(oe)
        print('Reestablishing connection...')
        con = settings.engine.connect()
        print('Connection Established!')


    formulae_based_downsides = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_formulaebaseddownsides',
                                                 con=con)
    # Update the Last Prices of Each Deal
    api_host = bbgclient.bbgclient.get_next_available_host()
    # formulae_based_downsides['Underlying'] = formulae_based_downsides['Underlying'].apply(lambda x: ' '.join(x.split(' ')[:2]))
    all_unique_tickers = list(formulae_based_downsides['Underlying'].unique())
    live_price_df = pd.DataFrame.from_dict(
        bbgclient.bbgclient.get_secid2field(all_unique_tickers, 'tickers', ['PX_LAST'], req_type='refdata',
                                             api_host=api_host), orient='index').reset_index()
    live_price_df['PX_LAST'] = live_price_df['PX_LAST'].apply(lambda x: x[0])
    live_price_df.columns = ['Underlying', 'PX_LAST']

    # Merge Live Price Df
    formulae_based_downsides = pd.merge(formulae_based_downsides, live_price_df, how='left', on=['Underlying'])

    def populate_last_prices(row):
        if pd.isnull(row['PX_LAST']) or row['PX_LAST'] is None or row['PX_LAST'] == 'None':
            return row['LastPrice']  # Return the Last Price fetched from the OMS

        return row['PX_LAST']

    formulae_based_downsides['PX_LAST'] = formulae_based_downsides.apply(populate_last_prices, axis=1)

    # Delete the old LastPrice
    del formulae_based_downsides['LastPrice']

    formulae_based_downsides.rename(columns={'PX_LAST': 'LastPrice'}, inplace=True)

    # Got the Latest Last Prices now iterate and refresh the ReferenceDataPoint based on DownsideType
    def update_base_case_reference_price(row):
        if row['BaseCaseDownsideType'] == 'Break Spread':
            return row['DealValue']  # Reference Price should be the deal value
        elif row['BaseCaseDownsideType'] == 'Last Price':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        elif row['BaseCaseDownsideType'] == 'Premium/Discount':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        elif row['BaseCaseDownsideType'] == 'Reference Security':
            return float(
                live_price_df[live_price_df['Underlying'] == row['BaseCaseReferenceDataPoint']]['PX_LAST'].iloc[0])

        # Else just return the original BaseCaseReferencePrice
        return row['BaseCaseReferencePrice']

    def update_outlier_reference_price(row):
        if row['OutlierDownsideType'] == 'Break Spread':
            return row['DealValue']  # Reference Price should be the deal value
        elif row['OutlierDownsideType'] == 'Last Price':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        elif row['OutlierDownsideType'] == 'Premium/Discount':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        elif row['OutlierDownsideType'] == 'Reference Security':
            return float(
                live_price_df[live_price_df['Underlying'] == row['OutlierReferenceDataPoint']]['PX_LAST'].iloc[0])

        # Else just return the original BaseCaseReferencePrice
        return row['OutlierReferencePrice']

    formulae_based_downsides['BaseCaseReferencePrice'] = formulae_based_downsides.apply(
        update_base_case_reference_price, axis=1)
    formulae_based_downsides['OutlierReferencePrice'] = formulae_based_downsides.apply(update_outlier_reference_price,
                                                                                       axis=1)

    # Reference Prices are Refreshed now recalculate the Base case and outlier downsides
    def update_base_case_downsides(row):
        try:
            if row['BaseCaseDownsideType'] == 'Fundamental Valuation':
                return row['base_case']
            else:
                return row['BaseCaseReferencePrice'] if row['BaseCaseOperation'] == 'None' else eval(
                    str(row['BaseCaseReferencePrice']) + str(row['BaseCaseOperation']) + str(row['BaseCaseCustomInput']))
        except Exception as e:
            print(e)
            return row['base_case']

    def update_outlier_downsides(row):
        try:
            if row['OutlierDownsideType'] == 'Fundamental Valuation':
                return row['outlier']
            else:
                return row['OutlierReferencePrice'] if row['OutlierOperation'] == 'None' else eval(
                    str(row['OutlierReferencePrice']) + str(row['OutlierOperation']) + str(row['OutlierCustomInput']))
        except Exception as e:
            print(e)
            return row['outlier']

    formulae_based_downsides['base_case'] = formulae_based_downsides.apply(update_base_case_downsides, axis=1)
    formulae_based_downsides['outlier'] = formulae_based_downsides.apply(update_outlier_downsides, axis=1)

    old_formulaes = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_formulaebaseddownsides', con=con)
    # Base Case and Outliers are now updated! Delete the old table and insert new ones
    try:
        con.execute('TRUNCATE TABLE test_wic_db.risk_reporting_formulaebaseddownsides')
        time.sleep(1)
        formulae_based_downsides.to_sql(name='risk_reporting_formulaebaseddownsides', con=con, if_exists='append',
                                        index=False, schema='test_wic_db')
        print('Refreshed Base Case and Outlier Downsides successfully...')
    except Exception as e:
        print(e)
        print('Some Error occured....Rolling back changes to downsides')
        old_formulaes.to_sql(name='risk_reporting_formulaebaseddownsides', con=con, if_exists='append', index=False,
                             schema='test_wic_db')
        print('Restored Downside formulae state to previous...!')

    # Post to Slack
    slack_message('navinspector.slack', {'impacts': 'Base Case and Outlier Downsides refreshed...'})



def update_merger_arb_nav_impacts():
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

    print('Updated with Latest Prices..')
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

    nav_impacts_sum_df = nav_impacts_positions_df.groupby(['TradeGroup', 'FundCode', 'PM_BASE_CASE', 'RiskLimit']).agg(
        {'BASE_CASE_NAV_IMPACT': 'sum', 'OUTLIER_NAV_IMPACT': 'sum'})



    nav_impacts_sum_df = pd.pivot_table(nav_impacts_sum_df, index=['TradeGroup', 'RiskLimit'], columns='FundCode',aggfunc=np.sum,
                                        fill_value='N/A')

    nav_impacts_sum_df.columns = ["_".join((i, j)) for i, j in nav_impacts_sum_df.columns]
    nav_impacts_sum_df.reset_index(inplace=True)

    del nav_impacts_sum_df['BASE_CASE_NAV_IMPACT_MALT']
    del nav_impacts_sum_df['OUTLIER_NAV_IMPACT_MALT']

    #Clear Previous DailyNavImpacts
    DailyNAVImpacts.objects.all().delete()

    #Post new Impacts on Slack Channel


    nav_impacts_sum_df.to_sql(con=settings.SQLALCHEMY_CONNECTION, if_exists='append', index=False, name='risk_reporting_dailynavimpacts',
                              schema='test_wic_db')


    real_time_arb_impacts = pd.read_sql_query('select TradeGroup, RiskLimit, BASE_CASE_NAV_IMPACT_ARB from test_wic_db.risk_reporting_dailynavimpacts where abs(RiskLimit) < abs(BASE_CASE_NAV_IMPACT_ARB) and BASE_CASE_NAV_IMPACT_ARB <> \'N/A\'', con=connection)

    slack_message('navinspector.slack', {'impacts': tabulate(real_time_arb_impacts, tablefmt='fancy_grid')})


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


#update_merger_arb_nav_impacts()