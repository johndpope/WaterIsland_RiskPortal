# coding: utf-8
import datetime
import io
import json
from locale import atof
import os
import sys
import time
import bbgclient
from celery import shared_task
import django
from django.conf import settings
from django_slack import slack_message
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from email_utilities import send_email
from risk.mna_deal_bloomberg_utils import get_data_from_bloomberg_by_bg_id
from realtime_pnl_impacts import views
from risk_reporting.update_credit_deals_tasks import update_credit_deals
from risk_reporting.models import (CreditDealsUpsideDownside, DailyNAVImpacts, PositionLevelNAVImpacts,
    FormulaeBasedDownsides)
from .views import get_security_info_dataframe, get_deal_info_dataframe
from slack_utils import get_channel_name


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
django.setup()

SLEEVE_DICT = {
    'Credit Opportunities': 'CREDIT',
    'Equity Special Situations': 'ESS',
    'Merger Arbitrage': 'M&A',
    'Opportunistic': 'OPP',
    'Break': 'UNLISTED/CASH',
}


def get_todays_date_yyyy_mm_dd():
    return datetime.datetime.now().date().strftime('%Y-%m-%d')


@shared_task
def refresh_base_case_and_outlier_downsides():
    """ Refreshes the base case and outlier downsides every 20 minutes for dynamically linked downsides """
    import bbgclient
    # Create new Engine and Close Connections here
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                           + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)

    con = engine.connect()
    formulae_based_downsides = pd.read_sql_query('SELECT * FROM '+settings.CURRENT_DATABASE+'.risk_reporting_formulaebaseddownsides',
                                                 con=con)
    time.sleep(3)
    # Update the Last Prices of Each Deal
    api_host = bbgclient.bbgclient.get_next_available_host()

    all_unique_tickers = list(formulae_based_downsides['Underlying'].unique())
    all_unique_base_case_reference_data_points = list(formulae_based_downsides[
                                                      ~(formulae_based_downsides['BaseCaseReferenceDataPoint'].isin([np.nan, None, '', 'NONE', 'None']))]
                                                      ['BaseCaseReferenceDataPoint'].unique())

    all_unique_outlier_reference_data_points = list(formulae_based_downsides[
                                                        ~(formulae_based_downsides['OutlierReferenceDataPoint'].isin([np.nan, None, '', 'NONE', 'None']))]
                                                    ['OutlierReferenceDataPoint'].unique())

    all_unique_tickers += all_unique_base_case_reference_data_points + all_unique_outlier_reference_data_points

    live_price_df = pd.DataFrame.from_dict(
        bbgclient.bbgclient.get_secid2field(all_unique_tickers, 'tickers', ['PX_LAST'], req_type='refdata',
                                            api_host=api_host), orient='index').reset_index()
    live_price_df['PX_LAST'] = live_price_df['PX_LAST'].apply(lambda x: x[0])
    live_price_df.columns = ['Underlying', 'PX_LAST']

    def adjust_for_london_stock(row):
        if ' LN EQUITY' in row['Underlying']:
            return float(row['PX_LAST']) / 100
        return row['PX_LAST']

    live_price_df['PX_LAST'] = live_price_df.apply(adjust_for_london_stock, axis=1)

    def fill_null_prices(row):
        # Fill Null prices from Flat File Database
        if row['PX_LAST'] == 'None' or pd.isnull(row['PX_LAST']):
            ticker = ' '.join(row['Underlying'].split(' ')[0:2])  # remove 'Equity' part for flat file matching
            # retrieve Last price from db
            query = 'SELECT Price FROM wic.daily_flat_file_db where Flat_file_as_of = (select max(flat_file_as_of) ' \
                    'from wic.daily_flat_file_db) and Ticker like "' + ticker + '" LIMIT 1;'
            rs = con.execute(query)
            last_price = 0
            for price in rs:
                last_price = price[0]

            return last_price

        return row['PX_LAST']

    live_price_df['PX_LAST'] = live_price_df.apply(fill_null_prices, axis=1)
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
        if row['BaseCaseDownsideType'] == 'Last Price':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        if row['BaseCaseDownsideType'] == 'Premium/Discount':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        if row['BaseCaseDownsideType'] == 'Reference Security':
            print(row['BaseCaseReferenceDataPoint'])
            return float(
                live_price_df[live_price_df['Underlying'] == row['BaseCaseReferenceDataPoint']]['PX_LAST'].iloc[0])

        # Else just return the original BaseCaseReferencePrice
        return row['BaseCaseReferencePrice']

    def update_outlier_reference_price(row):
        if row['OutlierDownsideType'] == 'Break Spread':
            return row['DealValue']  # Reference Price should be the deal value
        if row['OutlierDownsideType'] == 'Last Price':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        if row['OutlierDownsideType'] == 'Premium/Discount':
            return row['LastPrice']  # Reference Price is refreshed Last price...

        if row['OutlierDownsideType'] == 'Reference Security':
            return float(
                live_price_df[live_price_df['Underlying'] == row['OutlierReferenceDataPoint']]['PX_LAST'].iloc[0])

        # Else just return the original OutlierReferencePrice
        return row['OutlierReferencePrice']

    def match_base_case(row, base_cln, outlier_cln):
        # Only meant for Outlier
        if row['OutlierDownsideType'] == 'Match Base Case':
            return row[base_cln]
        else:
            return row[outlier_cln]

    formulae_based_downsides['BaseCaseReferencePrice'] = formulae_based_downsides.apply(
        update_base_case_reference_price, axis=1)

    match_base_case_rows = [('BaseCaseReferencePrice','OutlierReferencePrice'),
                            ('BaseCaseReferenceDataPoint', 'OutlierReferenceDataPoint'),
                            ('BaseCaseOperation', 'OutlierOperation'), ('BaseCaseCustomInput', 'OutlierCustomInput'),
                            ('base_case', 'outlier')
                            ]

    for base_column, outlier_column in match_base_case_rows:
        formulae_based_downsides[outlier_column] = formulae_based_downsides.apply(match_base_case, axis=1,
                                                                                  args=(base_column, outlier_column))

    formulae_based_downsides['OutlierReferencePrice'] = formulae_based_downsides.apply(update_outlier_reference_price,
                                                                                       axis=1)

    # Reference Prices are Refreshed now recalculate the Base case and outlier downsides
    def update_base_case_downsides(row):
        try:
            if row['BaseCaseDownsideType'] == 'Fundamental Valuation':
                return row['base_case']
            else:
                return row['BaseCaseReferencePrice'] if row['BaseCaseOperation'] == 'None' else eval(
                    str(row['BaseCaseReferencePrice']) + str(row['BaseCaseOperation']) + str(
                        row['BaseCaseCustomInput']))
        except Exception as e:
            print(e)
            return row['base_case']

    def update_outlier_downsides(row):
        try:
            if row['OutlierDownsideType'] == 'Fundamental Valuation':
                return row['outlier']
            elif row['OutlierDownsideType'] == 'Match Base Case':
                return row['base_case']
            else:
                return row['OutlierReferencePrice'] if row['OutlierOperation'] == 'None' else eval(
                    str(row['OutlierReferencePrice']) + str(row['OutlierOperation']) + str(row['OutlierCustomInput']))
        except Exception as e:
            print(e)
            return row['outlier']

    formulae_based_downsides['base_case'] = formulae_based_downsides.apply(update_base_case_downsides, axis=1)
    formulae_based_downsides['outlier'] = formulae_based_downsides.apply(update_outlier_downsides, axis=1)

    old_formulaes = pd.read_sql_query('SELECT * FROM '+settings.CURRENT_DATABASE+
                                      '.risk_reporting_formulaebaseddownsides', con=con)
    # Base Case and Outliers are now updated! Delete the old table and insert new ones
    try:
        FormulaeBasedDownsides.objects.all().delete()
        time.sleep(2)
        formulae_based_downsides.to_sql(name='risk_reporting_formulaebaseddownsides', con=con, if_exists='append',
                                        index=False, schema=settings.CURRENT_DATABASE)
        print('Refreshed Base Case and Outlier Downsides successfully...')
    except Exception as e:
        print(e)
        print('Some Error occured....Rolling back changes to downsides')
        old_formulaes.to_sql(name='risk_reporting_formulaebaseddownsides', con=con, if_exists='append', index=False,
                             schema=settings.CURRENT_DATABASE)
        print('Restored Downside formulae state to previous...!')

    try:
        api_host = bbgclient.bbgclient.get_next_available_host()
        # Populate all the deals
        nav_impacts_positions_df = pd.read_sql_query(
            'SELECT * FROM '+settings.CURRENT_DATABASE+'.risk_reporting_arbnavimpacts where FundCode not like \'WED\'',
            con=con)
        # Drop the Last Price
        time.sleep(2)

        # Todo Improve this
        nav_impacts_positions_df = nav_impacts_positions_df[~(nav_impacts_positions_df['FundCode'].isin(['INDEX1',
                                                                                                         'INDEX2',
                                                                                                         'ETF1',
                                                                                                         'ETF2',
                                                                                                         'INDEX3',
                                                                                                         'ETF3',
                                                                                                         'WIC']))]

        nav_impacts_positions_df.drop(columns=['LastPrice', 'RiskLimit'], inplace=True)

        ytd_performances = pd.read_sql_query(
            'SELECT DISTINCT tradegroup, fund, pnl_bps FROM '+settings.CURRENT_DATABASE+
            '.realtime_pnl_impacts_arbitrageytdperformance', con=con)
        time.sleep(1)
        ytd_performances.columns = ['TradeGroup', 'FundCode', 'PnL_BPS']
        # Convert Underlying Ticker to format Ticker Equity
        nav_impacts_positions_df['Underlying'] = nav_impacts_positions_df['Underlying'].apply(
            lambda x: x + " EQUITY" if "EQUITY" not in x else x)
        forumale_linked_downsides = pd.read_sql_query('SELECT * FROM '+settings.CURRENT_DATABASE +
                                                      '.risk_reporting_formulaebaseddownsides',
                                                      con=con)
        time.sleep(2)
        # Filter IsExcluded ones
        forumale_linked_downsides = forumale_linked_downsides[forumale_linked_downsides['IsExcluded'] == 'No']
        forumale_linked_downsides = forumale_linked_downsides[['TradeGroup', 'Underlying', 'RiskLimit', 'base_case',
                                                               'outlier', 'LastUpdate', 'LastPrice']]

        # Query Options Last Prices
        options_df = nav_impacts_positions_df[nav_impacts_positions_df['SecType'] == 'EXCHOPT']
        all_unique_tickers = options_df['Ticker'].apply(lambda x: x + " EQUITY").unique()

        options_live_price_df = pd.DataFrame.from_dict(
            bbgclient.bbgclient.get_secid2field(all_unique_tickers, 'tickers', ['PX_LAST'], req_type='refdata',
                                                api_host=api_host), orient='index').reset_index()
        options_live_price_df['PX_LAST'] = options_live_price_df['PX_LAST'].apply(lambda x: x[0])
        options_live_price_df.columns = ['Ticker', 'OptionLastPrice']

        merged_df = pd.merge(nav_impacts_positions_df, forumale_linked_downsides, how='inner',
                             on=['TradeGroup', 'Underlying'])

        # Now merge with Options live Price Dataframe on Ticker
        merged_df['Ticker'] = merged_df['Ticker'].apply(lambda x: x + ' EQUITY')
        merged_df = pd.merge(merged_df, options_live_price_df, how='left', on='Ticker')

        # merged_df = pd.merge(merged_df, ytd_performances, on=['TradeGroup', 'FundCode'], how='left')

        merged_df.drop(columns=['PM_BASE_CASE', 'Outlier'], inplace=True)
        merged_df.rename(columns={'base_case': 'PM_BASE_CASE', 'outlier': 'Outlier'}, inplace=True)
        nav_impacts_positions_df = merged_df.copy()
        nav_impacts_positions_df = nav_impacts_positions_df[
            (nav_impacts_positions_df['PM_BASE_CASE'] != 'None') & (nav_impacts_positions_df['Outlier'] != 'None')]

        float_cols = ['DealTermsCash', 'DealTermsStock', 'DealValue', 'NetMktVal', 'FxFactor', 'Capital',
                      'BaseCaseNavImpact', 'RiskLimit',
                      'OutlierNavImpact', 'QTY', 'NAV', 'PM_BASE_CASE', 'Outlier', 'StrikePrice', 'LastPrice']

        nav_impacts_positions_df[float_cols] = nav_impacts_positions_df[float_cols].fillna(0).astype(float)

        def get_current_mkt_val(row):
            if row['SecType'] != 'EXCHOPT':
                return row['QTY'] * row['LastPrice']
            if row['SecType'] == 'EXCHOPT':
                # print(row['OptionLastPrice'])
                option_price = row['OptionLastPrice']
                return row['QTY'] * float(option_price) if option_price is not None else 0

        nav_impacts_positions_df['CurrMktVal'] = nav_impacts_positions_df.apply(get_current_mkt_val, axis=1)
        # Calculate the Impacts
        nav_impacts_positions_df['PL_BASE_CASE'] = nav_impacts_positions_df.apply(calculate_pl_base_case, axis=1)
        nav_impacts_positions_df['BASE_CASE_NAV_IMPACT'] = nav_impacts_positions_df.apply(
            calculate_base_case_nav_impact,
            axis=1)
        # Calculate Outlier Impacts
        nav_impacts_positions_df['OUTLIER_PL'] = nav_impacts_positions_df.apply(calculate_outlier_pl, axis=1)
        nav_impacts_positions_df['OUTLIER_NAV_IMPACT'] = nav_impacts_positions_df.apply(calculate_outlier_nav_impact,
                                                                                        axis=1)

        def adjust_with_ytd_performance(row, compare_to):
            if row['PnL_BPS'] < 0:
                return row[compare_to] + row['PnL_BPS']
            return row[compare_to]

        nav_impacts_positions_df = nav_impacts_positions_df.round({'BASE_CASE_NAV_IMPACT': 2, 'OUTLIER_NAV_IMPACT': 2})
        nav_impacts_sum_df = nav_impacts_positions_df.groupby(['TradeGroup', 'FundCode', 'RiskLimit']).agg(
            {'BASE_CASE_NAV_IMPACT': 'sum', 'OUTLIER_NAV_IMPACT': 'sum'}).reset_index()

        nav_impacts_sum_df = pd.merge(nav_impacts_sum_df, ytd_performances, how='left', on=['TradeGroup', 'FundCode'])
        nav_impacts_sum_df['BASE_CASE_NAV_IMPACT'] = nav_impacts_sum_df.apply(lambda x:
                                                                              adjust_with_ytd_performance
                                                                              (x, compare_to=
                                                                              'BASE_CASE_NAV_IMPACT'), axis=1)
        nav_impacts_sum_df['OUTLIER_NAV_IMPACT'] = nav_impacts_sum_df.apply(lambda x:
                                                                            adjust_with_ytd_performance
                                                                            (x, compare_to=
                                                                            'OUTLIER_NAV_IMPACT'), axis=1)
        nav_impacts_sum_df.drop(columns='PnL_BPS', inplace=True)

        nav_impacts_sum_df = pd.pivot_table(nav_impacts_sum_df, index=['TradeGroup', 'RiskLimit'], columns='FundCode',
                                            aggfunc=np.sum,
                                            fill_value='')

        nav_impacts_sum_df.columns = ["_".join((i, j)) for i, j in nav_impacts_sum_df.columns]
        nav_impacts_sum_df.reset_index(inplace=True)

        DailyNAVImpacts.objects.all().delete()
        time.sleep(4)

        nav_impacts_sum_df.to_sql(con=con, if_exists='append', index=False, name='risk_reporting_dailynavimpacts',
                                  schema=settings.CURRENT_DATABASE)

        impacts = DailyNAVImpacts.objects.all()
        impacts_df = pd.DataFrame.from_records(impacts.values())

        def get_last_update_downside(row):
            try:
                last_update = forumale_linked_downsides[forumale_linked_downsides['TradeGroup'] ==
                                                        row['TradeGroup']]['LastUpdate'].max()
            except Exception:
                last_update = None
            return last_update

        impacts_df['LastUpdate'] = impacts_df.apply(get_last_update_downside, axis=1)

        # NAV Impacts @ Position Level

        nav_impacts_positions_df = nav_impacts_positions_df.groupby(['FundCode', 'TradeGroup', 'Ticker', 'PM_BASE_CASE',
                                                                     'Outlier', 'LastPrice']).agg({
            'BASE_CASE_NAV_IMPACT'
            : 'sum',
            'OUTLIER_NAV_IMPACT'
            : 'sum',
        })

        nav_impacts_positions_df = pd.pivot_table(nav_impacts_positions_df,
                                                  index=['TradeGroup', 'Ticker', 'PM_BASE_CASE',
                                                         'Outlier', 'LastPrice'], columns=['FundCode'],
                                                  aggfunc=np.sum,
                                                  fill_value='')

        nav_impacts_positions_df.columns = ["_".join((i, j)) for i, j in nav_impacts_positions_df.columns]
        nav_impacts_positions_df.reset_index(inplace=True)
        nav_impacts_positions_df['CALCULATED_ON'] = datetime.datetime.now()
        PositionLevelNAVImpacts.objects.all().delete()
        time.sleep(4)
        nav_impacts_positions_df.to_sql(name='risk_reporting_positionlevelnavimpacts', con=con,
                                        if_exists='append', index=False, schema=settings.CURRENT_DATABASE)

    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        slack_message('generic.slack',
                      {'message': 'ERROR: ' + str(e) + ' : ' + str(exc_type) + ' : ' + str(exc_tb.tb_lineno)},
                      channel=get_channel_name('realtimenavimpacts'),
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')

    con.close()


# Following NAV Impacts Utilities
def calculate_pl_base_case(row):
    if row['SecType'] != 'EXCHOPT':
        return (row['PM_BASE_CASE'] * row['FxFactor'] * row['QTY']) - (row['CurrMktVal'] * row['FxFactor'])

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
    return (row['PL_BASE_CASE'] / row['NAV']) * 100


def calculate_outlier_pl(row):
    if row['SecType'] != 'EXCHOPT':
        return (row['Outlier'] * row['FxFactor'] * row['QTY']) - (row['CurrMktVal'] * row['FxFactor'])

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
    return (row['OUTLIER_PL'] / row['NAV']) * 100


@shared_task
def email_nav_impacts_report():
    """ Daily NAV Impacts Report run at 6.45am """
    try:
        engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                               + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
        con = engine.connect()
        df = pd.read_sql_query('SELECT * FROM '+settings.CURRENT_DATABASE+'.risk_reporting_dailynavimpacts', con=con)
        time.sleep(3)
        downsides_df = pd.read_sql_query(
            'SELECT TradeGroup, base_case,outlier, max(LastUpdate) as LastUpdate FROM '
            + settings.CURRENT_DATABASE+'.risk_reporting_formulaebaseddownsides WHERE IsExcluded = \'No\''
            ' GROUP BY TradeGroup', con=con)
        time.sleep(3)
        arb_ytd_pnl = pd.read_sql_query(
            'SELECT tradegroup, ytd_dollar FROM '+settings.CURRENT_DATABASE+'.realtime_pnl_impacts_arbitrageytdperformance WHERE '
            'fund = \'ARB\' GROUP BY tradegroup', con=con)

        time.sleep(3)
        arb_ytd_pnl.columns = ['TradeGroup', '(ARB) YTD $ P&L']
        con.close()
        daily_nav_impacts = df.copy()
        daily_nav_impacts.columns = ['id', 'TradeGroup', 'RiskLimit', 'Base Case (AED)', 'Base Case (ARB)',
                                     'Base Case (CAM)', 'Base Case (LEV)', 'Base Case (LG)', 'Base Case (MACO)',
                                     'Base Case (TAQ)', 'Outlier (AED)', 'Outlier (ARB)', 'Outlier (CAM)',
                                     'Outlier (LEV)', 'Outlier (LG)', 'Outlier (MACO)', 'Outlier (TAQ)',
                                     'Base Case (MALT)', 'Outlier (MALT)', 'Last Update', 'Base Case (WED)',
                                     'Base Case (WIC)', 'Outlier (WED)', 'Outlier (WIC)']

        daily_nav_impacts = daily_nav_impacts[
            ['id', 'TradeGroup', 'RiskLimit', 'Base Case (AED)', 'Base Case (ARB)', 'Base Case (CAM)',
             'Base Case (LEV)', 'Base Case (LG)', 'Base Case (MACO)', 'Base Case (TAQ)', 'Outlier (AED)',
             'Outlier (ARB)', 'Outlier (CAM)', 'Outlier (LEV)', 'Outlier (LG)', 'Outlier (MACO)', 'Outlier (TAQ)',
             'Base Case (MALT)', 'Outlier (MALT)',
             ]]

        precision_cols = ['Base Case (AED)', 'Base Case (ARB)', 'Base Case (CAM)', 'Base Case (LEV)',
                          'Base Case (LG)', 'Base Case (MACO)', 'Base Case (TAQ)', 'Outlier (AED)', 'Outlier (ARB)',
                          'Outlier (CAM)', 'Outlier (LEV)', 'Outlier (LG)', 'Outlier (MACO)', 'Outlier (TAQ)',
                          'Base Case (MALT)', 'Outlier (MALT)']

        def round_df(val):
            try:
                return np.round(float(val), decimals=2) if val is not None else val
            except ValueError:
                return val

        for col in precision_cols:
            daily_nav_impacts[col] = daily_nav_impacts[col].apply(round_df)
            daily_nav_impacts[col] = daily_nav_impacts[col].apply(pd.to_numeric)

        daily_nav_impacts = daily_nav_impacts[['TradeGroup', 'RiskLimit', 'Base Case (ARB)', 'Base Case (MACO)',
                                               'Base Case (MALT)', 'Base Case (AED)', 'Base Case (CAM)',
                                               'Base Case (LG)', 'Base Case (LEV)', 'Outlier (ARB)',
                                               'Outlier (MACO)', 'Outlier (MALT)', 'Outlier (AED)',
                                               'Outlier (CAM)', 'Outlier (LG)', 'Outlier (LEV)']]

        def excel_formatting(row):
            ret = ["color:green" for _ in row.index]
            # Color Risk Limit and TradeGroup
            ret[row.index.get_loc("RiskLimit")] = "color:red"
            ret[row.index.get_loc("TradeGroup")] = "color:black"

            if abs(row['RiskLimit']) <= abs(row['Base Case (ARB)']):
                ret[row.index.get_loc("Base Case (ARB)")] = "color:red"

            if abs(row['RiskLimit']) <= abs(row['Base Case (MACO)']):
                ret[row.index.get_loc("Base Case (MACO)")] = "color:red"

            if abs(row['RiskLimit']) <= abs(row['Base Case (MALT)']):
                ret[row.index.get_loc("Base Case (MALT)")] = "color:red"

            if abs(row['RiskLimit']) <= abs(row['Outlier (ARB)']):
                ret[row.index.get_loc("Outlier (ARB)")] = "color:red"

            if abs(row['RiskLimit']) <= abs(row['Outlier (MACO)']):
                ret[row.index.get_loc("Outlier (MACO)")] = "color:red"

            if abs(row['RiskLimit']) <= abs(row['Outlier (MALT)']):
                ret[row.index.get_loc("Outlier (MALT)")] = "color:red"

            # Multi Strat is 2x Risk
            if abs(row['RiskLimit']) <= 2 * abs(row['Base Case (AED)']):
                ret[row.index.get_loc("Base Case (AED)")] = "color:red"

            if abs(row['RiskLimit']) <= 2 * abs(row['Base Case (CAM)']):
                ret[row.index.get_loc("Base Case (CAM)")] = "color:red"

            if abs(row['RiskLimit']) <= 2 * abs(row['Base Case (LG)']):
                ret[row.index.get_loc("Base Case (LG)")] = "color:red"

            if abs(row['RiskLimit']) <= 2 * abs(row['Outlier (AED)']):
                ret[row.index.get_loc("Outlier (AED)")] = "color:red"

            if abs(row['RiskLimit']) <= 2 * abs(row['Outlier (CAM)']):
                ret[row.index.get_loc("Outlier (CAM)")] = "color:red"

            if abs(row['RiskLimit']) <= 2 * abs(row['Outlier (LG)']):
                ret[row.index.get_loc("Outlier (LG)")] = "color:red"

            # Leveraged is 3x Risk
            if abs(row['RiskLimit']) <= 3 * abs(row['Base Case (LEV)']):
                ret[row.index.get_loc("Base Case (LEV)")] = "color:red"

            if abs(row['RiskLimit']) <= 3 * abs(row['Outlier (LEV)']):
                ret[row.index.get_loc("Outlier (LEV)")] = "color:red"

            return ret

        daily_nav_impacts = daily_nav_impacts.style.apply(excel_formatting, axis=1)

        downsides_df.columns = ['TradeGroup', 'Downside Base Case','Outlier', 'Last Downside Revision']

        df = df[['TradeGroup', 'RiskLimit', 'BASE_CASE_NAV_IMPACT_ARB', 'OUTLIER_NAV_IMPACT_ARB']]

        df = pd.merge(df, downsides_df, on='TradeGroup')

        df.columns = ['TradeGroup', 'RiskLimit', '(Base Case) NAV Impact', '(Outlier) NAV Impact',
                      'Downside Base Case', 'Outlier', 'Last Update']

        df = df[df['(Base Case) NAV Impact'] != '']
        df['(Base Case) NAV Impact'] = df['(Base Case) NAV Impact'].apply(lambda x: np.round(float(x), decimals=2))

        df = df[df['(Outlier) NAV Impact'] != '']
        df['(Outlier) NAV Impact'] = df['(Outlier) NAV Impact'].apply(lambda x: np.round(float(x), decimals=2))

        downsides_not_updated = df[pd.isna(df['Downside Base Case'])]['TradeGroup'].tolist()
        extra_message = '' if len(downsides_not_updated) == 0 else \
            '<br><br> Please update downsides for these Tradegroups: ' + ', '.join(downsides_not_updated)
        df = df[~(pd.isna(df['Downside Base Case']))]
        df = df[~(pd.isna(df['Outlier']))]
        df['Downside Base Case'] = df['Downside Base Case'].apply(lambda x: np.round(float(x), decimals=2))
        df['Outlier'] = df['Outlier'].apply(lambda x: np.round(float(x), decimals=2))

        def get_base_case_impact_over_limit(row):
            if abs(row['RiskLimit']) <= abs(row['(Base Case) NAV Impact']):
                return np.round((row['RiskLimit'] - row['(Base Case) NAV Impact']), decimals=2)

            return np.round((row['RiskLimit'] - row['(Base Case) NAV Impact']), decimals=2)

        def get_outlier_impact_over_limit(row):
            if abs(row['RiskLimit']) <= abs(row['(Outlier) NAV Impact']):
                return np.round((row['RiskLimit'] - row['(Outlier) NAV Impact']), decimals=2)

            return np.round((row['RiskLimit'] - row['(Outlier) NAV Impact']), decimals=2)

        df['(BaseCase)Impact Over Limit'] = df.apply(get_base_case_impact_over_limit, axis=1)
        df['(Outlier)Impact Over Limit'] = df.apply(get_outlier_impact_over_limit, axis=1)

        df1 = df.sort_values(by=['(Outlier)Impact Over Limit'], ascending=False)
        df_over_limit = df1[df1['(Outlier)Impact Over Limit'] >= 0]
        df_under_limit = df1[df1['(Outlier)Impact Over Limit'] < 0]
        df_under_limit = df_under_limit.sort_values(by=['(Outlier)Impact Over Limit'], ascending=False)
        df = pd.concat([df_over_limit, df_under_limit])
        df['(Outlier)Impact Over Limit'] = df['(Outlier)Impact Over Limit'].apply(lambda x: str(x) + '%')
        df['(BaseCase)Impact Over Limit'] = df['(BaseCase)Impact Over Limit'].apply(lambda x: str(x) + '%')
        df = pd.merge(df, arb_ytd_pnl, how='left', on='TradeGroup')

        df['(ARB) YTD $ P&L'] = format_with_commas(df, '(ARB) YTD $ P&L')

        # Get last Synced time
        last_calculated_on = PositionLevelNAVImpacts.objects.latest('CALCULATED_ON').CALCULATED_ON

        def export_excel(df):
            with io.BytesIO() as buffer:
                writer = pd.ExcelWriter(buffer)
                df.to_excel(writer)
                writer.save()
                return buffer.getvalue()

        def color_negative_red(val):
            value = float(val.split('%')[0])
            if value >= 0:
                color = 'red'
            else:
                color = 'black'

            return 'color: %s' % color

        del df['Downside Base Case']
        del df['Outlier']
        df = df[['TradeGroup', 'RiskLimit', '(Outlier) NAV Impact', '(Outlier)Impact Over Limit',
                 '(Base Case) NAV Impact', '(BaseCase)Impact Over Limit','Last Update', '(ARB) YTD $ P&L']]

        df = df.style.applymap(color_negative_red,
                               subset=['(Outlier)Impact Over Limit', '(BaseCase)Impact Over Limit']).set_table_styles([
            {'selector': 'tr:hover td', 'props': [('background-color', 'yellow')]},
            {'selector': 'th, td', 'props': [('border', '1px solid black'),
                                             ('padding', '4px'),
                                             ('text-align', 'center')]},
            {'selector': 'th', 'props': [('font-weight', 'bold')]},
            {'selector': '', 'props': [('border-collapse', 'collapse'),
                                       ('border', '1px solid black')]}
        ])

        html = """ \
                <html>
                  <head>
                  </head>
                  <body>
                    <p>Synchronization Timestamp: {0}</p>
                    <a href="http://192.168.0.16:8000/risk_reporting/merger_arb_risk_attributes">
                    Click to visit Realtime NAV Impacts Page</a>{1}<br><br>
                    {2}
                  </body>
                </html>
        """.format(last_calculated_on, extra_message, df.hide_index().render(index=False))

        exporters = {'Merger Arb NAV Impacts (' + get_todays_date_yyyy_mm_dd() + ').xlsx':
                         export_excel}

        subject = '(Risk Automation) Merger Arb NAV Impacts - ' + get_todays_date_yyyy_mm_dd()
        send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
                   recipients=['iteam@wicfunds.com'],
                   subject=subject, from_email='dispatch@wicfunds.com', html=html,
                   EXPORTERS=exporters, dataframe=daily_nav_impacts
                   )

    except Exception as e:
        print('Error Occured....')
        print(e)


@shared_task
def email_daily_formulae_linked_downsides():
    """ Daily Formulae Reports run at 7pm """
    try:
        engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                               + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
        con = engine.connect()
        downsides_df = pd.read_sql_query(
            'SELECT * FROM ' + settings.CURRENT_DATABASE+'.risk_reporting_formulaebaseddownsides ', con=con)
        credit_deals_up_down_df = pd.DataFrame.from_records(CreditDealsUpsideDownside.objects.all().values())
        time.sleep(3)

        alert_message = ''
        downsides_df = downsides_df[downsides_df['IsExcluded'] == 'No']
        null_risk_limits = downsides_df[(downsides_df['RiskLimit'] == 0) | (pd.isna(downsides_df['RiskLimit']) |
                                                                            (downsides_df['RiskLimit'].astype(str) == ''
                                                                             ))]['TradeGroup'].unique()

        null_base_case_downsides = downsides_df[(downsides_df['base_case'] == 0) | (pd.isna(downsides_df['base_case']))
                                                | (downsides_df['base_case'] == '')]['TradeGroup'].unique()
        null_outlier_downsides = downsides_df[(downsides_df['outlier'] == 0) | (pd.isna(downsides_df['outlier'])
                                              | (downsides_df['outlier'] == ''))]['TradeGroup'].unique()
        credit_deals_null_up_downside = credit_deals_up_down_df[((credit_deals_up_down_df['downside'] == '') |
                                                                 (credit_deals_up_down_df['upside'] == ''))]
        credit_deals_null_downside_tradegroups = credit_deals_null_up_downside['tradegroup'].unique()

        if len(null_risk_limits) > 0:
            alert_message += '<strong>Following have Undefined or Zero Risk Limits</strong>: <div class="bg-warning">'+\
                             ' , '.join(null_risk_limits) + "</div>"

        if len(null_base_case_downsides) > 0:
            alert_message += '<strong><br><br> Following have Undefined or Zero Base case</strong>: ' \
                             '<div class="bg-warning">' + ' , '.join(null_base_case_downsides) + "</div>"

        if len(null_outlier_downsides) > 0:
            alert_message += '<strong><br><br> Following have Undefined or Zero Outlier</strong>: ' \
                             '<div class="bg-warning">' + ' , '.join(null_outlier_downsides) + "</div>"

        if len(credit_deals_null_downside_tradegroups) > 0:
            alert_message += '<strong><br><br>CREDIT DEALS</strong><br>' \
                             '<strong>Following Credit Deals TradeGroups have NULL upside/downside</strong>:' \
                             '<div class="bg-warning">' + ' , '.join(credit_deals_null_downside_tradegroups) + "</div>"

        def export_excel(df):
            with io.BytesIO() as buffer:
                writer = pd.ExcelWriter(buffer)
                df.to_excel(writer)
                writer.save()
                return buffer.getvalue()

        html = """ \
                <html>
                  <head>
                  </head>
                  <body>
                    PFA Daily Backup for Formulae Linked Downsides and Credit Deals<br><br>
                    {0}
                  </body>
                </html>
        """.format(alert_message)

        exporters = {'FormulaeLinkedDownsides (' + get_todays_date_yyyy_mm_dd() + ').xlsx': export_excel,
                     'CreditDealsUpsideDownsides (' + get_todays_date_yyyy_mm_dd() + ').xlsx': export_excel}

        subject = '(Risk Automation) FormulaeLinkedDownsides & Credit Deals - ' + get_todays_date_yyyy_mm_dd()
        send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
                   recipients=['risk@wicfunds.com', 'rlogan@wicfunds.com', 'bmoore@wicfunds.com'], subject=subject,
                   from_email='dispatch@wicfunds.com', html=html, EXPORTERS=exporters,
                   dataframe=[downsides_df, credit_deals_up_down_df], multiple=True)

    except Exception as e:
        print('Error Occured....')
        print(e)


def round_bps(value):
    return float(value * 0.01)


def get_ytd_key(period_dict):
    if period_dict:
        for key in period_dict.keys():
            if period_dict.get(key) == 'YTD':
                return key
    return None


def get_bps_value(row):
    return row['P&L(bps)'].get(get_ytd_key(row['Period']))


def hover(hover_color="#ffff99"):
    return dict(selector="tr:hover",
                props=[("background-color", "%s" % hover_color)])


def style_funds(x):
    return ['font-size: 125%; font-weight: bold; border: 1px solid black' if v == 'Loss Budgets' else '' for v in x.index]


def calculate_status(row):
    if row['max_amount'] == 0 and row['min_amount'] == 0:
        row['status'] = 'CLOSED'
    else:
        row['status'] = 'ACTIVE'
    return row


@shared_task
def email_pl_target_loss_budgets():

    loss_budgets, ytd_return_sleeve_df, ytd_dollar_sleeve_df = calculate_pnl_budgets()
    loss_budgets = loss_budgets.drop(columns=['Last Updated'])
    ytd_dollar_sleeve_df['Sleeve'] = ytd_dollar_sleeve_df['Sleeve'].fillna('UNLISTED')

    pivoted = pd.pivot_table(loss_budgets, columns=['Fund'], aggfunc=lambda x: x, fill_value='')
    pivoted = pivoted[['ARB', 'MACO', 'MALT', 'AED', 'CAM', 'LG', 'LEV', 'TACO', 'TAQ']]
    pivoted = pivoted.reindex(['AUM',
                               'Ann Gross P&L Target %',
                               'Gross YTD Return',
                               'YTD P&L % of Target',
                               'Time Passed',
                               'Ann Gross P&L Target $',
                               'Gross YTD P&L',
                               '',
                               'Loss Budget',
                               'YTD Total Loss % of Budget',
                               'Time Passed',
                               'Ann Loss Budget $',
                               'YTD Closed Deal Losses',
                               'YTD Active Deal Losses',])
    df1 = pivoted.iloc[:8].copy()
    df2 = pivoted.iloc[8:].copy()
    df3 = pd.DataFrame([list(pivoted.columns.values)], columns=list(pivoted.columns.values))
    df1 = df1.append(df3)
    df1.index.values[5] = '* Ann Gross P&L Target $'
    df1.index.values[8] = 'Loss Budgets'
    df1 = df1.append(df2)
    df1.index.values[9] = 'Ann Loss Budget %'
    df1.index.values[0] = 'Investable Assets'
    df1.index.values[4] = 'Time Passed%'
    df1.index.values[11] = 'Time Passed %'
    df1.index.values[12] = '* Ann Loss Budget $'
    df1 = df1.replace(np.nan, '', regex=True)

    def excel_formatting(row):
        bold = False
        if row.index.contains('Sleeve_'):
            if row['Sleeve_'] == 'Total' or row['Sleeve_'] == 'Sleeve_':
                bold = True
        if bold:
            ret = ["color:green; font-weight:bold" for _ in row.index]
        else:
            ret = ["color:green" for _ in row.index]
        if row.index.contains('Sleeve_'):
            if bold:
                ret[row.index.get_loc("Sleeve_")] = "color:black; font-weight:bold"
            else:
                ret[row.index.get_loc("Sleeve_")] = "color:black"
        if row.index.contains('TradeGroup_'):
            ret[row.index.get_loc("TradeGroup_")] = "color:black"
        if row.index.contains('Catalyst_'):
            ret[row.index.get_loc("Catalyst_")] = "color:black"

        columns = ['Total YTD PnL_ARB', 'Total YTD PnL_MACO', 'Total YTD PnL_MALT', 'Total YTD PnL_LEV',
                   'Total YTD PnL_AED', 'Total YTD PnL_CAM', 'Total YTD PnL_LG', 'Total YTD PnL_WED',
                   'Total YTD PnL_TACO']

        for column in columns:
            if isinstance(row[column], (int, float)) and row[column] < 0:
                if bold:
                    ret[row.index.get_loc(column)] = "color:red; font-weight:bold"
                else:
                    ret[row.index.get_loc(column)] = "color:red"
            elif isinstance(row[column], (str)) and row[column] == column:
                ret[row.index.get_loc(column)] = "color:black; font-weight:bold"

        return ret

    def sleeve_excel_formatting(row):
        bold = False
        if row.index.contains('Sleeve'):
            if row['Sleeve'] == 'Total':
                bold = True
        if bold:
            ret = ["color:green; font-weight:bold" for _ in row.index]
        else:
            ret = ["color:green" for _ in row.index]
        columns = row.index.tolist()
        for column in columns:
            if row.index.contains(column):
                if column == 'Sleeve':
                    ret[row.index.get_loc("Sleeve")] = "color:black; font-weight:bold"
                elif isinstance(row[column], (int, float)) and row[column] < 0:
                    if bold:
                        ret[row.index.get_loc(column)] = "color:red; font-weight:bold"
                    else:
                        ret[row.index.get_loc(column)] = "color:red"
                elif isinstance(row[column], (str)) and row[column] == column:
                    ret[row.index.get_loc(column)] = "color:black; font-weight:bold"
                elif isinstance(row[column], (str)) and row[column].find("%") > -1:
                    value = row[column]
                    value = float(value.replace("%", ""))
                    if value >= 0:
                        if bold:
                            ret[row.index.get_loc(column)] = "color:green; font-weight:bold"
                        else:
                            ret[row.index.get_loc(column)] = "color:green"
                    else:
                        if bold:
                            ret[row.index.get_loc(column)] = "color:red; font-weight:bold"
                        else:
                            ret[row.index.get_loc(column)] = "color:red"


        return ret


    styles = [
        hover(),
        dict(selector="th", props=[("font-size", "125%"), ("text-align", "center")]),
        dict(selector="tr", props=[("text-align", "center")]),
        dict(selector="caption", props=[("caption-side", "bottom")]),
        {'selector': 'tr:hover td', 'props': [('background-color', 'green')]},
        {'selector': 'th, td', 'props': [('border', '1px solid black'), ('padding', '4px'), ('text-align', 'center')]},
        {'selector': 'th', 'props': [('font-weight', 'bold')]},
        {'selector': '', 'props': [('border-collapse', 'collapse'), ('border', '1px solid black'), ('text-align',
                                                                                                    'center')]}
    ]
    df1.drop(columns=['TAQ'], inplace=True)
    styled_html = (df1.style.apply(style_funds).set_table_styles(styles).set_caption("PL Targets & Loss Budgets (" + get_todays_date_yyyy_mm_dd() + ")"))

    def export_excel(df_list):
        with io.BytesIO() as buffer:
            writer = pd.ExcelWriter(buffer)
            workbook = writer.book
            sheet_names = ['TradeGroup P&L', 'Sleeve P&L %', 'Sleeve P&L $', 'Fund P&L Monitor']
            for i, df in enumerate(df_list):
                sheet_name = sheet_names[i]
                worksheet = workbook.add_worksheet(sheet_name)
                writer.sheets[sheet_name] = worksheet
                if sheet_name == 'Fund P&L Monitor':
                    df.to_excel(writer, sheet_name=sheet_name, startrow=0, startcol=0, index=True)
                elif sheet_name == 'Sleeve P&L %':
                    worksheet.write(0, 0, 'Profit PL % Breakdown by Sleeves')
                    df[0].to_excel(writer, sheet_name=sheet_name, startrow=1, startcol=0, index=False)
                    worksheet.write(10, 0, 'Loss PL % Breakdown by Sleeves')
                    df[1].to_excel(writer, sheet_name=sheet_name, startrow=11, startcol=0, index=False)
                elif sheet_name == 'Sleeve P&L $':
                    worksheet.write(0, 0, 'Profit PL $ Breakdown by Sleeves')
                    df[0].to_excel(writer, sheet_name=sheet_name, startrow=1, startcol=0, index=False)
                    worksheet.write(12, 0, 'Loss PL $ Breakdown by Sleeves')
                    df[1].to_excel(writer, sheet_name=sheet_name, startrow=13, startcol=0, index=False)
                else:
                    df.to_excel(writer, sheet_name=sheet_name, startrow=0, startcol=0, index=False)
                worksheet.set_column('A:L', 20)
            format1 = workbook.add_format({'num_format': '#,###'})
            worksheet = writer.sheets['TradeGroup P&L']
            worksheet.set_column('A:C', 20)
            worksheet.set_column('D:M', 20, format1)
            writer.save()
            return buffer.getvalue()

    final_live_df, final_daily_pnl, position_level_pnl, last_updated, fund_level_live, final_position_level_ytd_pnl, \
    fund_drilldown_details = views.get_data()
    final_live_df = final_live_df[['TradeGroup_', 'Sleeve_', 'Catalyst_', 'Total YTD PnL_ARB', 'Total YTD PnL_MACO',
                                   'Total YTD PnL_MALT', 'Total YTD PnL_LEV', 'Total YTD PnL_AED', 'Total YTD PnL_CAM',
                                   'Total YTD PnL_LG', 'Total YTD PnL_WED', 'Total YTD PnL_TACO']]
    final_live_df_columns = list(final_live_df.columns.values)
    final_live_df_columns.remove('TradeGroup_')
    final_live_df_columns.remove('Sleeve_')
    final_live_df_columns.remove('Catalyst_')
    fund_list = []
    for column in final_live_df_columns:
        fund = column.split("_")[1]
        fund_list.append(fund)
    final_live_df.reset_index(inplace=True)
    cash_index = final_live_df[final_live_df['TradeGroup_'] == 'CASH'].index
    if not cash_index.empty:
        # Change Sleeve for CASH TradeGroup to CASH
        final_live_df.at[cash_index, 'Sleeve_'] = 'CASH'
    unique_sleeves = final_live_df['Sleeve_'].unique()
    ytd_return_unique_funds = ytd_return_sleeve_df.Fund.unique().tolist()
    ytd_return_unique_sleeves = ytd_return_sleeve_df.Sleeve.unique().tolist()
    ytd_dollar_unique_sleeves = ytd_dollar_sleeve_df.Sleeve.unique().tolist()
    if 'Risk' in ytd_return_unique_sleeves:
        ytd_return_unique_sleeves.remove('Risk')
    if 'Forwards' in ytd_return_unique_sleeves:
        ytd_return_unique_sleeves.remove('Forwards')

    profit_sleeve_ytd = pd.DataFrame(columns=['Sleeve'] + fund_list)
    loss_sleeve_ytd = pd.DataFrame(columns=['Sleeve'] + fund_list)
    profit_sleeve_ytd_perc = pd.DataFrame(columns=['Sleeve'] + ytd_return_unique_funds)
    loss_sleeve_ytd_perc = pd.DataFrame(columns=['Sleeve'] + ytd_return_unique_funds)
    profit_dollar_sleeve_df = ytd_dollar_sleeve_df[ytd_dollar_sleeve_df['Gross YTD Dollar'] > 0].\
        groupby(['Fund', 'Sleeve']).agg('sum').reset_index()
    loss_dollar_sleeve_df = ytd_dollar_sleeve_df[ytd_dollar_sleeve_df['Gross YTD Dollar'] < 0].\
        groupby(['Fund', 'Sleeve']).agg('sum').reset_index()

    for sleeve in ytd_return_unique_sleeves:
        new_sleeve = SLEEVE_DICT.get(sleeve, sleeve)
        profit_row_perc_dict = {'Sleeve': new_sleeve}
        for fund in ytd_return_unique_funds:
            gross_ytd_return_index = ytd_return_sleeve_df[(ytd_return_sleeve_df['Fund'] == fund) & (ytd_return_sleeve_df['Sleeve'] == sleeve)].index
            if not gross_ytd_return_index.empty:
                gross_ytd_return_index = gross_ytd_return_index[0]
                gross_ytd_return = ytd_return_sleeve_df.at[gross_ytd_return_index, 'Gross YTD Return']
                if not np.isnan(gross_ytd_return):
                    loss_budget_row_index = loss_budgets[loss_budgets['Fund'] == fund].index
                    if not loss_budget_row_index.empty:
                        loss_budget_row_index = loss_budget_row_index[0]
                        ann_gross_pl_target_perc = float(float(loss_budgets.at[loss_budget_row_index, 'Ann Gross P&L Target %'].replace("%", "")) * 0.01)
                        ytd_sleeve_perc_target = float(gross_ytd_return / ann_gross_pl_target_perc)
                else:
                    ytd_sleeve_perc_target = 0.00
            else:
                ytd_sleeve_perc_target = 0.00

            profit_row_perc_dict[fund] = float(ytd_sleeve_perc_target * 0.01)
        profit_sleeve_ytd_perc = profit_sleeve_ytd_perc.append(profit_row_perc_dict, ignore_index=True)

    for sleeve in ytd_dollar_unique_sleeves:
        new_sleeve = SLEEVE_DICT.get(sleeve, sleeve)
        profit_row_dollar_dict = {'Sleeve': new_sleeve}
        loss_row_perc_dict = {'Sleeve': new_sleeve}
        loss_row_dollar_dict = {'Sleeve': new_sleeve}
        for fund in ytd_return_unique_funds:
            profit_dollar_sleeve_index = profit_dollar_sleeve_df[(profit_dollar_sleeve_df['Fund'] == fund) & (profit_dollar_sleeve_df['Sleeve'] == new_sleeve)].index
            if not profit_dollar_sleeve_index.empty:
                profit_dollar_sleeve_index = profit_dollar_sleeve_index[0]
                profit_dollar = profit_dollar_sleeve_df.at[profit_dollar_sleeve_index, 'Gross YTD Dollar']
                if np.isnan(profit_dollar):
                    profit_dollar = 0.00
            else:
                profit_dollar = 0.00

            loss_dollar_sleeve_index = loss_dollar_sleeve_df[(loss_dollar_sleeve_df['Fund'] == fund) & (loss_dollar_sleeve_df['Sleeve'] == new_sleeve)].index
            if not loss_dollar_sleeve_index.empty:
                loss_dollar_sleeve_index = loss_dollar_sleeve_index[0]
                loss_dollar = loss_dollar_sleeve_df.at[loss_dollar_sleeve_index, 'Gross YTD Dollar']
                if not np.isnan(loss_dollar):
                    loss_budget_row_index = loss_budgets[loss_budgets['Fund'] == fund].index
                    if not loss_budget_row_index.empty:
                        loss_budget_row_index = loss_budget_row_index[0]
                        ann_loss_budget_dollar = int(loss_budgets.at[loss_budget_row_index, 'Ann Loss Budget $'].replace(",", ""))
                        loss_row_perc_dict[fund] = float((loss_dollar / ann_loss_budget_dollar) * 100)
                else:
                    loss_dollar = 0.00
                    loss_row_perc_dict[fund] = 0.00
            else:
                loss_dollar = 0.00
                loss_row_perc_dict[fund] = 0.00

            profit_row_dollar_dict[fund] = int(profit_dollar)
            loss_row_dollar_dict[fund] = int(loss_dollar)
        profit_sleeve_ytd = profit_sleeve_ytd.append(profit_row_dollar_dict, ignore_index=True)
        loss_sleeve_ytd = loss_sleeve_ytd.append(loss_row_dollar_dict, ignore_index=True)
        loss_sleeve_ytd_perc = loss_sleeve_ytd_perc.append(loss_row_perc_dict, ignore_index=True)

    # Calculate total of the columns in all dataframes
    total_profit_dict = {'Sleeve': 'Total'}
    total_loss_dict = {'Sleeve': 'Total'}
    total_loss_perc_dict = {'Sleeve': 'Total'}
    for fund in fund_list:
        total_profit_dict[fund] = profit_sleeve_ytd[fund].sum()
        total_loss_dict[fund] = loss_sleeve_ytd[fund].sum()
        total_loss_perc_dict[fund] = str(round(loss_sleeve_ytd_perc[fund].sum(), 2)) + "%"
        loss_sleeve_ytd_perc[fund] = format_with_percentage_decimal(loss_sleeve_ytd_perc, fund)
    profit_sleeve_ytd = profit_sleeve_ytd.append(total_profit_dict, ignore_index=True)
    loss_sleeve_ytd = loss_sleeve_ytd.append(total_loss_dict, ignore_index=True)
    loss_sleeve_ytd_perc = loss_sleeve_ytd_perc.append(total_loss_perc_dict, ignore_index=True)

    total_profit_perc_dict = {'Sleeve': 'Total'}
    for fund in ytd_return_unique_funds:
        total_profit_perc_dict[fund] = str(round(profit_sleeve_ytd_perc[fund].sum(), 2)) + "%"
        profit_sleeve_ytd_perc[fund] = format_with_percentage_decimal(profit_sleeve_ytd_perc, fund)
    profit_sleeve_ytd_perc = profit_sleeve_ytd_perc.append(total_profit_perc_dict, ignore_index=True)

    # Display in the following Fund order
    column_order = ['Sleeve', 'ARB', 'MACO', 'MALT', 'AED', 'CAM', 'LG', 'LEV', 'TACO']
    loss_sleeve_ytd_perc = loss_sleeve_ytd_perc[column_order]
    profit_sleeve_ytd_perc = profit_sleeve_ytd_perc[column_order]
    loss_sleeve_ytd = loss_sleeve_ytd[column_order]
    profit_sleeve_ytd = profit_sleeve_ytd[column_order]

    # Sort according to the ['M&A', 'CREDIT', 'ESS', 'OPP'] sleeve order
    profit_sleeve_ytd = sort_by_sleeve(profit_sleeve_ytd, 'Sleeve')
    loss_sleeve_ytd = sort_by_sleeve(loss_sleeve_ytd, 'Sleeve')
    profit_sleeve_ytd_perc = sort_by_sleeve(profit_sleeve_ytd_perc, 'Sleeve')
    loss_sleeve_ytd_perc = sort_by_sleeve(loss_sleeve_ytd_perc, 'Sleeve')

    # Revert the changing of Sleeve name for CASH TradeGroup
    final_live_df.at[cash_index, 'Sleeve_'] = 0
    final_live_df.drop(columns=['index'], inplace=True)

    # Sort the dataframe according to Sleeve followed by TradeGroup in alphabetical order
    sleeve_sorting = ['M&A', 'CREDIT', 'ESS', 'OPP']
    for sleeve in final_live_df.Sleeve_.unique():
        if isinstance(sleeve, str):
            sleeve = sleeve.strip()
        if sleeve not in sleeve_sorting:
            sleeve_sorting.append(sleeve)
    final_live_df['Sleeve_'] = pd.Categorical(final_live_df['Sleeve_'], sleeve_sorting)
    final_live_df = final_live_df.sort_values(by=['Sleeve_', 'TradeGroup_'], ascending=[True, True])

    # Replace '0' with '-' and convert all numbers to int
    for column in final_live_df_columns:
        final_live_df[column] = final_live_df[column].astype(int)
        final_live_df = final_live_df.replace({column: 0}, '-')

    final_live_df = final_live_df.style.apply(excel_formatting, axis=1)
    profit_sleeve_ytd = profit_sleeve_ytd.style.apply(sleeve_excel_formatting, axis=1)
    loss_sleeve_ytd = loss_sleeve_ytd.style.apply(sleeve_excel_formatting, axis=1)
    profit_sleeve_ytd_perc = profit_sleeve_ytd_perc.style.apply(sleeve_excel_formatting, axis=1)
    loss_sleeve_ytd_perc = loss_sleeve_ytd_perc.style.apply(sleeve_excel_formatting, axis=1)

    exporters = {'PL Targets & Loss Budgets (' + get_todays_date_yyyy_mm_dd() + ').xlsx': export_excel}
    subject = 'PL Targets & Loss Budgets - ' + get_todays_date_yyyy_mm_dd()

    # Send MStrat Drawdowns
    styled_ess_mstrat_df, original_ess_mstrat_df = ess_multistrat_drawdown_monitor()
    html = """ \
                <html>
                  <head>
                  </head>
                  <body>
                    <p>PL Targets & Loss Budgets ({date})</p>
                    <a href="http://192.168.0.16:8000">Click to visit Realtime PL Targets & Loss Budgets Page</a>
                    <br>
                    <a href="http://192.168.0.16:8000/realtime_pnl_impacts/live_tradegroup_pnl">
                        Click to visit Realtime TradeGroup PL Page
                    </a>
                    <br><br>
                    {table}
                    <br>
                    <p>* Above data has been calculated using Average YTD Investable Assets</p>
                    <br><br>
                    <p>ESS Multistrat Drawdown Monitor</p>
                    {essmstratdrawdown}
                  </body>
                </html>
        """.format(table=styled_html.render(), date=get_todays_date_yyyy_mm_dd(),
                   essmstratdrawdown=styled_ess_mstrat_df.hide_index().render(index=False))

    send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
               recipients=['iteam@wicfunds.com'],
               subject=subject, from_email='dispatch@wicfunds.com', html=html,
               EXPORTERS=exporters,
               dataframe=[final_live_df, [profit_sleeve_ytd_perc, loss_sleeve_ytd_perc],
                          [profit_sleeve_ytd, loss_sleeve_ytd], df1])


def push_data_to_table(df):
    df = df.rename(columns={'Fund': 'fund', 'YTD Active Deal Losses': 'ytd_active_deal_losses',
                            'YTD Closed Deal Losses': 'ytd_closed_deal_losses', 'Loss Budget': 'ann_loss_budget_perc',
                            'AUM': 'investable_assets', 'Gross YTD P&L': 'gross_ytd_pnl', 'Time Passed': 'time_passed',
                            'Ann Gross P&L Target %': 'ann_gross_pnl_target_perc', 'Last Updated': 'last_updated',
                            'Ann Gross P&L Target $': 'ann_gross_pnl_target_dollar', 'YTD P&L % of Target': 'ytd_pnl_perc_target',
                            'Ann Loss Budget $': 'ann_loss_budget_dollar', 'Gross YTD Return': 'gross_ytd_return',
                            'YTD Total Loss % of Budget': 'ytd_total_loss_perc_budget'})
    df = df.applymap(str)
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()
    df.to_sql(con=con, name='realtime_pnl_impacts_pnlmonitors', schema=settings.CURRENT_DATABASE,
              if_exists='append', chunksize=10000, index=False)
    con.close()


def calculate_pnl_budgets():
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()

    raw_df = pd.read_sql('Select * from ' + settings.CURRENT_DATABASE + '.realtime_pnl_impacts_arbitrageytdperformance',
                         con=con)
    flat_file_df = pd.read_sql('select TradeGroup as tradegroup, Fund as fund, LongShort as long_short, max(amount) '
                               'as max_amount, min(amount) as min_amount from wic.daily_flat_file_db where '
                               'Flat_file_as_of = (select max(Flat_file_as_of) from wic.daily_flat_file_db) '
                               'group by TradeGroup, Fund, LongShort;', con=con)

    sleeve_df = pd.read_sql('Select * from wic.sleeves_snapshot', con=con)
    return_targets_df = pd.read_sql('SELECT DISTINCT t.fund as Fund, t.profit_target FROM ' + settings.CURRENT_DATABASE+
                                    '.realtime_pnl_impacts_pnlprofittarget t INNER JOIN (SELECT fund, MAX(last_updated)'
                                    ' AS Max_last_updated FROM ' + settings.CURRENT_DATABASE +
                                    '.realtime_pnl_impacts_pnlprofittarget GROUP BY fund) groupedt ON t.fund = '
                                    'groupedt.fund AND t.last_updated = groupedt.Max_last_updated;', con=con)

    loss_budget_df = pd.read_sql('SELECT DISTINCT t.fund as Fund, t.loss_budget as `Loss Budget` FROM ' +
                                 settings.CURRENT_DATABASE + '.realtime_pnl_impacts_pnllossbudget t INNER JOIN (SELECT '
                                 'fund, MAX(last_updated) AS Max_last_updated FROM ' + settings.CURRENT_DATABASE +
                                 '.realtime_pnl_impacts_pnllossbudget GROUP BY fund) groupedt ON t.fund = groupedt.fund'
                                 ' AND t.last_updated = groupedt.Max_last_updated;', con=con)
    con.close()
    return_targets_df.rename(columns={'profit_target': 'Ann Gross P&L Target %'}, inplace=True)

    raw_df.drop(columns=['id'], inplace=True)

    flat_file_df = flat_file_df.apply(calculate_status, axis=1)
    df_active_null = raw_df[(raw_df['status'] == 'ACTIVE') | (raw_df['status'].isnull())]
    df_closed = raw_df[raw_df['status'] == 'CLOSED']
    df_active_null = df_active_null.drop(columns=['status'])

    new_status_df = pd.merge(df_active_null, flat_file_df[['tradegroup', 'fund', 'long_short', 'status']],
                             on=['tradegroup', 'fund', 'long_short'], how='left')
    df = df_closed.append(new_status_df, ignore_index=True)
    df["status"] = df["status"].fillna('CLOSED')

    c_load = sleeve_df['Metrics in NAV JSON'].apply(json.loads)
    c_list = list(c_load)
    c_dat = json.dumps(c_list)
    sleeve_df = sleeve_df.join(pd.read_json(c_dat))
    sleeve_df = sleeve_df.drop('Metrics in NAV JSON', axis=1)

    sleeve_df['Gross YTD Return'] = sleeve_df.apply(get_bps_value, axis=1)

    gross_ytd_return_sleeve_df = sleeve_df[['Fund', 'Sleeve', 'Gross YTD Return']].copy()
    gross_ytd_dollar_sleeve_df = df[['fund', 'sleeve', 'tradegroup', 'ytd_dollar']].copy()
    cash_index = gross_ytd_dollar_sleeve_df[gross_ytd_dollar_sleeve_df['tradegroup'] == 'CASH'].index
    if not cash_index.empty:
        for index in cash_index:
            gross_ytd_dollar_sleeve_df.at[index, 'sleeve'] = 'CASH'
    gross_ytd_dollar_sleeve_df.drop(columns=['tradegroup'], inplace=True)
    gross_ytd_dollar_sleeve_df.rename(columns={'fund': 'Fund', 'sleeve': 'Sleeve', 'ytd_dollar': 'Gross YTD Dollar'},
                                      inplace=True)
    new_sleeve_df = sleeve_df[['Fund', 'Gross YTD Return']].copy()

    new_sleeve_df = new_sleeve_df.groupby(['Fund']).sum()

    new_sleeve_df['Gross YTD Return'] = new_sleeve_df['Gross YTD Return'].apply(round_bps)
    new_sleeve_df = new_sleeve_df.reset_index()

    pd.set_option('float_format', '{:2}'.format)
    active_tradegroups = df[df['status'] == 'ACTIVE']
    closed_tradegroups = df[df['status'] == 'CLOSED']
    fund_active_losers = active_tradegroups[active_tradegroups['ytd_dollar'] < 0][['fund', 'ytd_dollar']].\
        groupby(['fund']).agg('sum').reset_index()
    fund_active_losers.columns = ['Fund', 'YTD Active Deal Losses']
    investable_assets_df = df[['fund', 'fund_aum']].drop_duplicates()
    investable_assets_df.columns = ['Fund', 'AUM']
    fund_realized_losses = closed_tradegroups[closed_tradegroups['ytd_dollar'] < 0][['fund', 'ytd_dollar']].\
        groupby(['fund']).agg('sum').reset_index()
    fund_realized_losses.columns = ['Fund', 'YTD Closed Deal Losses']
    fund_pnl = pd.merge(fund_active_losers, fund_realized_losses, on=['Fund'])

    merged_df = pd.merge(fund_pnl, loss_budget_df, on=['Fund'])
    merged_df = pd.merge(merged_df, return_targets_df, on=['Fund'])
    merged_df = pd.merge(merged_df, investable_assets_df, on=['Fund'])
    average_aum_df = get_average_ytd_aum()
    merged_df = pd.merge(merged_df, average_aum_df, on=['Fund'], how='left')
    float_cols = ['YTD Active Deal Losses', 'YTD Closed Deal Losses', 'Loss Budget', 'Ann Gross P&L Target %', 'AUM']
    merged_df[float_cols] = merged_df[float_cols].astype(float)
    merged_df['Ann Gross P&L Target $'] = merged_df['Ann Gross P&L Target %'] * merged_df['Average YTD AUM'] * 0.01
    gross_ytd_pnl = df[['fund', 'ytd_dollar']].groupby('fund').agg('sum').reset_index()
    gross_ytd_pnl.columns = ['Fund', 'Gross YTD P&L']
    merged_df = pd.merge(merged_df, gross_ytd_pnl, on='Fund')
    merged_df = pd.merge(merged_df, new_sleeve_df, on='Fund', how='left')
    merged_df['YTD P&L % of Target'] = (merged_df['Gross YTD Return']/merged_df['Ann Gross P&L Target %'])*100

    loss_budgets = merged_df[['Fund', 'YTD Active Deal Losses', 'YTD Closed Deal Losses', 'Loss Budget', 'AUM',
                              'Gross YTD P&L', 'Ann Gross P&L Target %', 'Gross YTD Return',
                              'Ann Gross P&L Target $', 'YTD P&L % of Target', 'Average YTD AUM']]

    loss_budgets['Ann Loss Budget $'] = loss_budgets['Loss Budget'] * loss_budgets['Average YTD AUM'] * 0.01

    current_year = datetime.date.today().year
    ytd = datetime.date(current_year, 1, 1)
    now = datetime.datetime.today().date()
    days_passed = (now - ytd).days
    time_passed_in_percentage = np.round((days_passed/365.0), decimals=2)*100
    loss_budgets['Time Passed'] = "{:.2f}%".format(time_passed_in_percentage)

    loss_budgets['Ann Gross P&L Target %'] = format_with_percentage_decimal(loss_budgets, 'Ann Gross P&L Target %')
    loss_budgets['Loss Budget'] = format_with_percentage_decimal(loss_budgets, 'Loss Budget')
    loss_budgets['YTD Total Loss % of Budget'] = ((loss_budgets['YTD Active Deal Losses'] +
                                                   loss_budgets['YTD Closed Deal Losses']) /
                                                  loss_budgets['Ann Loss Budget $']) * 100

    # Rounding off to 2 decimal places for % values
    loss_budgets['YTD Active Deal Losses'] = format_with_commas(loss_budgets, 'YTD Active Deal Losses')
    loss_budgets['YTD Closed Deal Losses'] = format_with_commas(loss_budgets, 'YTD Closed Deal Losses')
    loss_budgets['AUM'] = format_with_commas(loss_budgets, 'AUM')
    loss_budgets['Gross YTD Return'] = format_with_percentage_decimal(loss_budgets, 'Gross YTD Return')
    loss_budgets['YTD P&L % of Target'] = format_with_percentage_decimal(loss_budgets, 'YTD P&L % of Target')
    loss_budgets['Ann Loss Budget $'] = format_with_commas(loss_budgets, 'Ann Loss Budget $')
    loss_budgets['YTD Total Loss % of Budget'] = format_with_percentage_decimal(loss_budgets, 'YTD Total Loss % of Budget')
    loss_budgets['Gross YTD P&L'] = format_with_commas(loss_budgets, 'Gross YTD P&L')
    loss_budgets['Ann Gross P&L Target $'] = format_with_commas(loss_budgets, 'Ann Gross P&L Target $')
    loss_budgets['Last Updated'] = datetime.datetime.now()
    loss_budgets.drop(columns=['Average YTD AUM'], inplace=True)
    push_data = loss_budgets
    push_data_to_table(push_data)
    return loss_budgets, gross_ytd_return_sleeve_df, gross_ytd_dollar_sleeve_df


@shared_task
def calculate_realtime_pnl_budgets():
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()

    pnl_budgets = pd.read_sql('Select * from ' + settings.CURRENT_DATABASE + '.realtime_pnl_impacts_pnlmonitors where '\
                              'last_updated = (Select max(last_updated) from ' + settings.CURRENT_DATABASE +
                              '.realtime_pnl_impacts_pnlmonitors)', con=con)
    gross_ytd_return_df = pd.read_sql('select fund, gross_ytd_return from ' + settings.CURRENT_DATABASE + \
                                      '.realtime_pnl_impacts_pnlmonitors where DATE(last_updated) = '\
                                      '(select DATE(max(last_updated)) from ' + settings.CURRENT_DATABASE + \
                                      '.realtime_pnl_impacts_pnlmonitors) and HOUR(last_updated) = 8;', con=con)
    con.close()
    if gross_ytd_return_df.empty:
        slack_message('generic.slack',
                      {'message': 'ERROR: Realtime Loss Budgets (Dashboard) did NOT run at 8 am.'},
                      channel=get_channel_name('realtimenavimpacts'),
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')
    
    if not gross_ytd_return_df.empty:

        if 'id' in pnl_budgets.columns.values:
            pnl_budgets.drop(columns=['id'], inplace=True)

        final_live_df, final_daily_pnl, position_level_pnl, last_updated, fund_level_live, final_position_level_ytd_pnl, \
        fund_drilldown_details = views.get_data()
        fund_level_df = views.calculate_roc_nav_fund_level_live(fund_level_live)
        fund_level_df = fund_level_df[['Fund', 'Contribution_to_NAV']]
        fund_level_df = fund_level_df.groupby(['Fund']).sum()
        fund_level_df['fund'] = fund_level_df.index
        fund_level_df.reset_index(drop=True, inplace=True)
        fund_level_df['Contribution_to_NAV'] = fund_level_df['Contribution_to_NAV'] * 0.01
        ytd_return_merge = pd.merge(gross_ytd_return_df, fund_level_df, on='fund', how='left')
        ytd_return_merge['gross_ytd_return'] = ytd_return_merge['gross_ytd_return'].str.replace('%', '').apply(atof)
        ytd_return_merge['gross_ytd_return'] = ytd_return_merge['gross_ytd_return'] + ytd_return_merge['Contribution_to_NAV']
        ytd_return_merge.rename(columns={'gross_ytd_return': 'new_ytd_return'}, inplace=True)
        ytd_return_merge.drop(columns=['Contribution_to_NAV'], inplace=True)

        live_ytd_pnl = pd.Series([])
        ytd_live_pnl_sum = pd.Series([])
        ytd_pnl_df = pd.DataFrame()
        columns = final_live_df.columns.values
        for i, column in enumerate(columns):
            if "Total YTD PnL_" in column:
                live_ytd_pnl[i] = column.split("_")[-1]
                ytd_live_pnl_sum[i] = final_live_df[column].sum()
        ytd_pnl_df['fund'] = live_ytd_pnl
        ytd_pnl_df['Live P&L'] = ytd_live_pnl_sum
        realtime_pl_budget_df = pd.merge(pnl_budgets, ytd_pnl_df, on=['fund'], how='left')
        realtime_pl_budget_df['gross_ytd_pnl'] = realtime_pl_budget_df['Live P&L']
        realtime_pl_budget_df['investable_assets'] = realtime_pl_budget_df['investable_assets'].str.replace(',', '').apply(atof)
        realtime_pl_budget_df = pd.merge(realtime_pl_budget_df, ytd_return_merge, on='fund', how='left')
        realtime_pl_budget_df.drop(columns=['gross_ytd_return'], inplace=True)
        realtime_pl_budget_df.rename(columns={'new_ytd_return': 'gross_ytd_return'}, inplace=True)
        realtime_pl_budget_df['ann_gross_pnl_target_perc'] = realtime_pl_budget_df['ann_gross_pnl_target_perc'].str.replace('%', '').apply(atof)
        realtime_pl_budget_df['ytd_pnl_perc_target'] = realtime_pl_budget_df['gross_ytd_return'] / realtime_pl_budget_df['ann_gross_pnl_target_perc'] * 100
        realtime_pl_budget_df['gross_ytd_return'] = format_with_percentage_decimal(realtime_pl_budget_df, 'gross_ytd_return')
        realtime_pl_budget_df['investable_assets'] = format_with_commas(realtime_pl_budget_df, 'investable_assets')
        realtime_pl_budget_df['gross_ytd_pnl'] = format_with_commas(realtime_pl_budget_df, 'gross_ytd_pnl')
        realtime_pl_budget_df['ann_gross_pnl_target_perc'] = format_with_percentage_decimal(realtime_pl_budget_df, 'ann_gross_pnl_target_perc')
        realtime_pl_budget_df['ytd_pnl_perc_target'] = format_with_percentage_decimal(realtime_pl_budget_df, 'ytd_pnl_perc_target')
        realtime_pl_budget_df.drop(columns=['Live P&L'], inplace=True)
        realtime_pl_budget_df['last_updated'] = datetime.datetime.now()
        push_data = realtime_pl_budget_df
        push_data_to_table(push_data)


def format_with_commas(df, column):
    try:
        return df.apply(lambda x: "{:,}".format(int(x[column])) if (np.all(pd.notnull(x))) else x, axis=1)
    except ValueError:
        return df.apply(lambda x: "{:,}".format(x[column]), axis=1)


def format_with_percentage_decimal(df, column):
    return df.apply(lambda x: "{:,.2f}%".format(x[column]), axis=1)


def get_average_ytd_aum():
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()
    average_aum_df = pd.read_sql('select fund as Fund, avg(aum) as `Average YTD AUM` from wic.daily_flat_file_db '
                                 'where year(Flat_file_as_of) >= YEAR(CURDATE()) group by fund order by fund', con=con)
    con.close()
    return average_aum_df


def sort_by_sleeve(given_df, sleeve_column):
    sleeve_sorting = ['M&A', 'CREDIT', 'ESS', 'OPP']
    for sleeve in given_df[sleeve_column].unique():
        if isinstance(sleeve, str):
            sleeve = sleeve.strip()
        if sleeve not in sleeve_sorting:
            sleeve_sorting.append(sleeve)
    given_df['Sleeve'] = pd.Categorical(given_df['Sleeve'], sleeve_sorting)
    given_df = given_df.sort_values(by=['Sleeve'])
    return given_df


@shared_task
def refresh_credit_deals_upside_downside():
    try:
        credit_deals_df = pd.DataFrame.from_records(CreditDealsUpsideDownside.objects.all().values())
        formuale_df = pd.DataFrame.from_records(FormulaeBasedDownsides.objects.all().values('Underlying', 'outlier', 'DealValue'))
        spread_index_list = credit_deals_df[credit_deals_df['upside_type'] == 'Calculate from SIX']['spread_index'].tolist()
        bloomberg_id_list = credit_deals_df['bloomberg_id'].tolist()
        ticker_bbg_id_list = list(spread_index_list + bloomberg_id_list)
        fields = ['PX_LAST']
        result = get_data_from_bloomberg_by_bg_id(ticker_bbg_id_list, fields)
        credit_deals_df['last_price'] = credit_deals_df['bloomberg_id'].map(result)
        credit_deals_df['last_price'] = credit_deals_df['last_price'].apply(get_px_last_value)
        credit_deals_df['last_price'] = credit_deals_df['last_price'].fillna(0.0)
        credit_deals_df['spread_px_last'] = credit_deals_df['spread_index'].map(result)
        credit_deals_df['spread_px_last'] = credit_deals_df['spread_px_last'].apply(get_px_last_value)
        credit_deals_df['spread_px_last'] = credit_deals_df['spread_px_last'].fillna(0.0)
        credit_deals_df['equity_ticker'] = credit_deals_df.apply(lambda row: row['ticker'] + ' EQUITY' if 'equity' not in \
                                                                row['ticker'].lower() else row['ticker'].upper(), axis=1)
        credit_deals_df = pd.merge(credit_deals_df, formuale_df, left_on='equity_ticker', right_on='Underlying', how='left')

        credit_deals_df['upside'] = credit_deals_df.apply(lambda row: float(row['last_price']) + \
                                                        float(row['spread_px_last']) if row['upside_type'] == \
                                                        'Calculate from SIX' else row['upside'], axis=1)
        credit_deals_df['upside'] = credit_deals_df.apply(lambda row: float(row['last_price']) if row['upside_type'] == \
                                                        'Last Price' else row['upside'], axis=1)
        credit_deals_df['upside'] = credit_deals_df.apply(lambda row: row['DealValue'] if row['upside_type'] == \
                                                        'Match ARB' else row['upside'], axis=1)

        credit_deals_df['downside'] = credit_deals_df.apply(lambda row: float(row['last_price']) if row['downside_type'] ==\
                                                            'Last Price' else row['downside'], axis=1)
        credit_deals_df['downside'] = credit_deals_df.apply(lambda row: row['outlier'] if row['downside_type'] == \
                                                            'Match ARB' else row['downside'], axis=1)
        credit_deals_df['deal_value'] = credit_deals_df.apply(lambda row: row['DealValue'] if row['downside_type'] == \
                                                            'Match ARB' or row['upside_type'] == 'Match ARB' else \
                                                            row['deal_value'], axis=1)

        credit_deals_df['last_refreshed'] = datetime.datetime.now()
        credit_deals_df.drop(columns=['id'], inplace=True)
        credit_deals_df.reset_index(inplace=True)
        credit_deals_df.rename(columns={'index': 'id'}, inplace=True)
        credit_deals_df.drop(columns=['equity_ticker', 'spread_px_last', 'Underlying', 'outlier', 'DealValue'],
                             inplace=True)
        current_credit_deals_df = pd.DataFrame.from_records(CreditDealsUpsideDownside.objects.all().values())
        try:
            CreditDealsUpsideDownside.objects.all().delete()
            time.sleep(3)
            engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" +
                                   settings.WICFUNDS_DATABASE_PASSWORD + "@" + settings.WICFUNDS_DATABASE_HOST + "/" +
                                   settings.WICFUNDS_DATABASE_NAME)
            con = engine.connect()
            credit_deals_df.to_sql(con=con, name='risk_reporting_creditdealsupsidedownside',
                                   schema=settings.CURRENT_DATABASE, if_exists='append', chunksize=10000, index=False)
        except Exception as e:
            current_credit_deals_df.to_sql(con=con, name='risk_reporting_creditdealsupsidedownside',
                                           schema=settings.CURRENT_DATABASE, if_exists='append', chunksize=10000,
                                           index=False)
            slack_message('generic.slack',
                          {'message': 'ERROR: Credit Deals upside/downside DB Refresh (every 29 minutes) had an error.'+
                                      'The database has been restored to the previous data. Exception: ' + str(e)},
                          channel=get_channel_name('realtimenavimpacts'), token=settings.SLACK_TOKEN,
                          name='ESS_IDEA_DB_ERROR_INSPECTOR')
        con.close()
    except Exception as e:
        print('Credit Deals Upside/Downside Update failed', e)
        slack_message('generic.slack',
                      {'message': 'ERROR: Credit Deals up/downside refresh (every 29 minutes) had an error.' + str(e)},
                      channel=get_channel_name('realtimenavimpacts'),
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')


def get_px_last_value(value):
    try:
        return value['PX_LAST'][0]
    except Exception as e:
        return value


@shared_task
def update_credit_deals_upside_downside_once_daily():
    update_credit_deals()


# Automated File Dropping to EZE
@shared_task
def drop_arb_downsides_to_eze():
    """ Runs at 6pm Mon-Fri """
    try:
        path = settings.DEAL_INFO_EZE_UPLOAD_PATH
        deal_info_df = get_deal_info_dataframe()
        deal_info_df.to_csv(path, index=False)
        success = '_(Risk Automation)_ *Successfully Uploaded DealInfo.csv to Eze Uploads (Eze/Upload Files/)*'
        error = "."
    except Exception as e:
        error = '_(Risk Automation)_ *Error in Uploading DealInfo.csv* -> ' + str(e)
        success = 'ERROR! Please upload files manually'
    slack_message('eze_uploads.slack', {'success': success, 'error': error},
                                             channel=get_channel_name('portal_downsides'),
                                             token=settings.SLACK_TOKEN)

    # Now process for SecurityInfo.csv
    try:
        path = settings.SECURITY_INFO_EZE_UPLOAD_PATH
        security_info_df = get_security_info_dataframe()
        security_info_df.to_csv(path, index=False)
        success = '_(Risk Automation)_ *Successfully Uploaded SecurityInfo.csv to Eze Uploads (Eze/Upload Files/)*'
        error = "."
    except Exception as e:
        error = '_(Risk Automation)_ *Error in Uploading SecurityInfo.csv* -> ' + str(e)
        success = "ERROR! Please upload files manually"
    slack_message('eze_uploads.slack', {'success': success, 'error': error},
                                             channel=get_channel_name('portal_downsides'),
                                             token=settings.SLACK_TOKEN)

@shared_task
def post_alert_before_eze_upload():
    """ Task should run at 4pm Mon-Fri """

    downsides_df = pd.DataFrame.from_records(FormulaeBasedDownsides.objects.all().filter(IsExcluded__exact='No').
                                             values())

    null_risk_limits = downsides_df[(downsides_df['RiskLimit'] == 0) | (pd.isna(downsides_df['RiskLimit']) |
                                                                        (downsides_df['RiskLimit'].astype(str) == ''
                                                                         ))]['TradeGroup'].unique()

    null_base_case_downsides = downsides_df[(downsides_df['base_case'] == 0) | (pd.isna(downsides_df['base_case']))
                                            | (downsides_df['base_case'] == '')]['TradeGroup'].unique()
    null_outlier_downsides = downsides_df[(downsides_df['outlier'] == 0) | (pd.isna(downsides_df['outlier'])
                                          | (downsides_df['outlier'] == ''))]['TradeGroup'].unique()

    null_risk_limits = ', '.join(null_risk_limits)
    null_base_case_downsides = ', '.join(null_base_case_downsides)
    null_outlier_downsides = ', '.join(null_outlier_downsides)

    risk_limits_alert = '_(Risk Automation)_ Following have NULL/0 Risk Limits *' + null_risk_limits + "*" \
        if null_risk_limits else "_(Risk Automation)_ All Risk Limits ready for Eze Upload (at 6pm)"
    base_case_alert = '_(Risk Automation)_ Following have NULL/0 Base Case *' + null_base_case_downsides + "*" \
        if null_base_case_downsides else "_(Risk Automation)_ All base case downsides ready for Eze Upload (at 6pm)"
    outlier_alert = '_(Risk Automation)_ Following have NULL/0 Outlier *' + null_outlier_downsides + "*" \
        if null_outlier_downsides else "_(Risk Automation)_ All outlier downsides ready for Upload (at 6pm)"

    slack_message('eze_uploads.slack', {'null_risk_limits': str(risk_limits_alert),
                                        'null_base_case': str(base_case_alert),
                                        'null_outlier': str(outlier_alert)},
                                         channel=get_channel_name('portal_downsides'),
                                         token=settings.SLACK_TOKEN
                  )


@shared_task
def ess_multistrat_drawdown_monitor():
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()
    print('Now Processing: ESS Multi-Strat Drawdown Monitor')
    df, final_df = None, None
    try:
        api_host = bbgclient.bbgclient.get_next_available_host()
        ess_drawdown_query = "SELECT TradeGroup, Ticker, AlphaHedge, RiskLimit, CurrentMktVal_Pct, DealDownside, SecType, "\
                             "LongShort, (amount*factor) as QTY, CurrentMktVal, FXCurrentLocalToBase as FxFactor, aum, "\
                             "PutCall, Strike as StrikePrice, DealUpside FROM "\
                             "wic.daily_flat_file_db WHERE Flat_file_as_of = "\
                             "(SELECT MAX(Flat_file_as_of) FROM wic.daily_flat_file_db) "\
                             "AND AlphaHedge IN ('Alpha', 'Alpha Hedge') AND amount<>0 AND Fund LIKE 'AED' "\
                             "AND Sleeve = 'Equity Special Situations'"

        today = datetime.datetime.now().date().strftime('%Y-%m-%d')
        ess_tg_performance_query = "SELECT TradeGroup, ROMC_YTD_bps, YTD_Dollar, 5D_bps,5D_Dollar, 1D_bps, 1D_Dollar "\
                                   "FROM wic.tradegroup_performance_over_own_capital WHERE Sleeve = 'ESS' "\
                                   "AND Fund LIKE 'AED' AND `Date` = '"+today+"'AND `Status` = 'ACTIVE'"
        ess_drawdown_df = pd.read_sql_query(ess_drawdown_query, con=con)
        ess_tg_perf_df = pd.read_sql_query(ess_tg_performance_query, con=con)
        # Exclude tradgroups (manually)
        ess_drawdown_df = ess_drawdown_df[~(ess_drawdown_df['TradeGroup'] == 'AVYA R/R')]
        ess_drawdown_df[['RiskLimit', 'CurrentMktVal_Pct', 'DealDownside', 'QTY', 'aum', 'StrikePrice', 'DealUpside']].astype(float)
        # if Risk Limit is 0 or NULL assume 30 basis point Risk limit
        ess_drawdown_df.loc[ess_drawdown_df.RiskLimit == 0, "RiskLimit" ] = 0.30
        ess_drawdown_df['RiskLimit'] = ess_drawdown_df['RiskLimit'].apply(lambda x: -x if x > 0 else x)
        ess_drawdown_df.rename(columns={'CurrentMktVal_Pct': 'aed_aum_pct'}, inplace=True)

        def calculate_break_pl(row):
            if row['AlphaHedge'] == 'Alpha':
                if row['SecType'] == 'EQ' and row['LongShort'] == 'Short':
                    return (row['DealUpside'] * row['QTY']) - (row['CurrentMktVal'] / row['FxFactor'])

                return (row['DealDownside'] * row['QTY']) - (row['CurrentMktVal'] / row['FxFactor'])
            #Todo Add logic for Options where LongShort = Short

            if row['PutCall'] == 'CALL':
                if row['StrikePrice'] <= row['DealDownside']:
                    x = (row['DealDownside'] - row['StrikePrice']) * (row['QTY'])
                else:
                    x = 0
            elif row['PutCall'] == 'PUT':
                if row['StrikePrice'] >= row['DealDownside']:
                    x = (row['StrikePrice'] - row['DealDownside']) * (row['QTY'])
                else:
                    x = 0
            return -row['CurrentMktVal'] + x

        ess_drawdown_df['Break PL'] = ess_drawdown_df.apply(calculate_break_pl, axis=1)
        ess_drawdown_df['NAV Risk'] = 1e2*ess_drawdown_df['Break PL']/ess_drawdown_df['aum']

        nav_risk_df = ess_drawdown_df[['TradeGroup','NAV Risk']].groupby(['TradeGroup']).sum().reset_index()
        ess_drawdown_df_equity = ess_drawdown_df[ess_drawdown_df['SecType'] == 'EQ']

        ess_drawdown_df_equity = ess_drawdown_df_equity[['TradeGroup', 'Ticker', 'AlphaHedge', 'RiskLimit',
                                                         'aed_aum_pct', 'DealDownside', 'SecType', 'LongShort',
                                                         'QTY', 'CurrentMktVal', 'aum']]
        ess_df_nav_risk = pd.merge(ess_drawdown_df_equity, nav_risk_df, on='TradeGroup')
        ess_df_nav_risk['pct_of_limit'] = 1e2*ess_df_nav_risk['NAV Risk']/ess_df_nav_risk['RiskLimit']
        ess_df_nav_risk['pct_aum_at_max_risk'] = 1e2*ess_df_nav_risk['aed_aum_pct']/ess_df_nav_risk['pct_of_limit']

        ess_df_nav_risk['Ticker'] = ess_df_nav_risk['Ticker'].apply(lambda x: x+" EQUITY" if 'equity' not in x.lower() else x)
        vol_series = ['VOLATILITY_260D','VOLATILITY_180D','VOLATILITY_90D','VOLATILITY_60D','VOLATILITY_30D','VOLATILITY_10D']
        tradegroup_volatility_dictionary = bbgclient.bbgclient.get_secid2field(list(ess_df_nav_risk['Ticker'].unique()),'tickers',vol_series,req_type='refdata',api_host=api_host)

        def volatility_cascade_logic(ticker):
            assumed_vol = 0.30  # 30% volatility (Assumed if nothing found in Bloomberg)
            for vol in vol_series:
                current_vol = tradegroup_volatility_dictionary[ticker][vol][0]
                if current_vol is not None:
                    return float(current_vol)

            return assumed_vol

        ess_df_nav_risk['Ann Vol'] = ess_df_nav_risk['Ticker'].apply(volatility_cascade_logic)
        ess_df_nav_risk['Ann Vol'] = ess_df_nav_risk['Ann Vol'].astype(float)

        ess_df_nav_risk['33% of Vol'] = ess_df_nav_risk['Ann Vol']*0.33
        ess_df_nav_risk['50% of Vol'] = ess_df_nav_risk['Ann Vol']*0.50
        final_df = pd.merge(ess_df_nav_risk, ess_tg_perf_df, how='left', on='TradeGroup')
        # Year-to-Date
        final_df['YTD ROMC'] = final_df['ROMC_YTD_bps']/100
        final_df['YTD NAV Cont'] = 1e2*final_df['YTD_Dollar']/final_df['aum']
        final_df['% of NAV Loss Limit'] = final_df.apply(lambda x: 0 if x['YTD NAV Cont'] > 0 else 1e2*x['YTD NAV Cont']/x['RiskLimit'], axis=1)

        # 5 Day
        final_df['5D ROC'] = final_df['5D_bps']/100
        final_df['5D NAV Cont'] = 1e2*final_df['5D_Dollar']/final_df['aum']

        # 1 Day
        final_df['1D ROC'] = final_df['1D_bps']/100
        final_df['1D NAV Cont'] = 1e2*final_df['1D_Dollar']/final_df['aum']

        final_df = final_df[['TradeGroup', 'Ticker', 'AlphaHedge', 'RiskLimit', 'aed_aum_pct', 'NAV Risk',
                             'pct_of_limit', 'pct_aum_at_max_risk', 'Ann Vol', '33% of Vol', '50% of Vol',
                             'YTD ROMC', 'YTD NAV Cont', '% of NAV Loss Limit', '5D ROC', '5D NAV Cont',
                             '1D ROC', '1D NAV Cont']]

        final_df.columns = ['TradeGroup', 'Alpha', 'AlphaHedge', 'RiskLimit', '% AUM (AED)', 'NAV Risk (%)', '% of Limit',
                            '% AUM @ Max Risk', 'Ann Vol (%)', '33% of Vol (%)', '50% of Vol (%)', 'YTD ROMC (%)',
                            'YTD NAV Cont (%)', '% of NAV Loss Limit', '5D ROC (%)', '5D NAV Cont (%)',
                            '1D ROC (%)', '1D NAV Cont (%)']

        def define_color(row, column):
            color = 'black'
            ytd_romc = abs(row['YTD ROMC (%)'])
            risk_limit = abs(row['RiskLimit'])
            vol_tt_pct = abs(row['33% of Vol (%)'])
            vol_fifty_pct = abs(row['50% of Vol (%)'])
            ytd_nav_cont = abs(row['YTD NAV Cont (%)'])

            if column == 'ROMC':
                if (ytd_romc > vol_tt_pct) and (ytd_romc < vol_fifty_pct):
                    color = 'orange'
                if ytd_romc >= vol_fifty_pct:
                    color = 'red'
            else:
                if (ytd_nav_cont > 0.50*risk_limit) and (ytd_nav_cont < 0.90*risk_limit):
                    color = 'orange'
                if ytd_nav_cont >= 0.90*risk_limit:
                    color = 'red'

            # No colors for Positive PnL names...
            if row['YTD ROMC (%)'] > 0:
                color = 'black'
            if row['YTD NAV Cont (%)'] > 0:
                color = 'black'

            return color

        final_df['YTD ROMC Color'] = final_df.apply(lambda x: define_color(x, 'ROMC'), axis=1)
        final_df['NAV Cont Color'] = final_df.apply(lambda x: define_color(x, 'NAV'), axis=1)

        colors_df = final_df[['TradeGroup', 'YTD ROMC Color', 'NAV Cont Color']].copy()
        del final_df['YTD ROMC Color']
        del final_df['NAV Cont Color']

        # Round to 2 decimals
        cols_precision = ['% AUM (AED)', 'NAV Risk (%)', '% of Limit', '% AUM @ Max Risk', 'Ann Vol (%)', '33% of Vol (%)',
                          '50% of Vol (%)', 'YTD ROMC (%)', 'YTD NAV Cont (%)', '% of NAV Loss Limit', '5D ROC (%)',
                          '5D NAV Cont (%)', '1D ROC (%)','1D NAV Cont (%)']
        final_df[cols_precision] = final_df[cols_precision].round(decimals=2)

        def highlight_breaches(row):
            tradegroup = row['TradeGroup']
            romc_color = colors_df[colors_df['TradeGroup'] == tradegroup]['YTD ROMC Color'].iloc[0]
            nav_color = colors_df[colors_df['TradeGroup'] == tradegroup]['NAV Cont Color'].iloc[0]

            ret = ["color:black" for _ in row.index]
            # Color Risk Limit and TradeGroup
            ytd_romc_color = romc_color if not romc_color == 'black' else romc_color
            nav_cont_color = nav_color if not nav_color == 'black' else nav_color

            ret[row.index.get_loc("YTD ROMC (%)")] = "color:white;background-color:"+ytd_romc_color if not ytd_romc_color == 'black' else "color:black"
            ret[row.index.get_loc("YTD NAV Cont (%)")] = "color:white;background-color:"+nav_cont_color if not nav_cont_color == 'black' else "color:black"
            ret[row.index.get_loc("TradeGroup")] = "color:white;background-color:"+ytd_romc_color if not ytd_romc_color == 'black' else "color:black"

            return ret

        del final_df['% AUM @ Max Risk']   # Temporarily hiding this column

        df = final_df.style.apply(highlight_breaches,axis=1).set_table_styles([
                    {'selector': 'tr:hover td', 'props': [('background-color', 'beige')]},
                    {'selector': 'th, td', 'props': [('border', '1px solid black'),
                                                     ('padding', '4px'),
                                                     ('text-align', 'center')]},
                    {'selector': 'th', 'props': [('font-weight', 'bold')]},
                    {'selector': '', 'props': [('border-collapse', 'collapse'),
                                               ('border', '1px solid black')]}
                ])

    except Exception as e:
        print(e)
        slack_message('generic.slack',
                      {'message': 'ESS Multi-Strat DrawDown Monitor -- > ERROR: ' + str(e)},
                      channel=get_channel_name('realtimenavimpacts'),
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')
    finally:
        print('Closing Connection to Relational Database Service....')
        con.close()

    return df, final_df

