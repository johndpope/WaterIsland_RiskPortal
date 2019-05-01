# coding: utf-8
import datetime
import io
import json
from locale import atof
from math import ceil
import os
import sys
import time

from celery import shared_task
import django
from django.conf import settings
from django_slack import slack_message
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from email_utilities import send_email
from realtime_pnl_impacts import views
from risk_reporting.models import DailyNAVImpacts, PositionLevelNAVImpacts, FormulaeBasedDownsides


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
django.setup()


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
        # Post to Slack
        slack_message('navinspector.slack',
                      {'impacts': 'While Refreshing Impacts: ' + str(e)})

    try:
        api_host = bbgclient.bbgclient.get_next_available_host()
        # Populate all the deals
        nav_impacts_positions_df = pd.read_sql_query(
            'SELECT * FROM '+settings.CURRENT_DATABASE+'.risk_reporting_arbnavimpacts where FundCode not like \'WED\'',
            con=con)
        # Drop the Last Price
        time.sleep(2)
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
                      channel='realtimenavimpacts',
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

        exporters = {'Merger Arb NAV Impacts (' + datetime.datetime.now().date().strftime('%Y-%m-%d') + ').xlsx':
                         export_excel}

        subject = '(Risk Automation) Merger Arb NAV Impacts - ' + datetime.datetime.now().date().strftime('%Y-%m-%d')
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
        time.sleep(3)

        alert_message = ''
        null_risk_limits = downsides_df[(downsides_df['RiskLimit'] == 0) | (pd.isna(downsides_df['RiskLimit']) |
                                                                            (downsides_df['RiskLimit'].astype(str) == ''
                                                                             ))]['TradeGroup'].unique()

        null_base_case_downsides = downsides_df[(downsides_df['base_case'] == 0) | (pd.isna(downsides_df['base_case']))
                                                | (downsides_df['base_case'] == '')]['TradeGroup'].unique()
        null_outlier_downsides = downsides_df[(downsides_df['outlier'] == 0) | (pd.isna(downsides_df['outlier'])
                                              | (downsides_df['outlier'] == ''))]['TradeGroup'].unique()

        if len(null_risk_limits) > 0:
            alert_message += '<strong>Following have Undefined or Zero Risk Limits</strong>: <div class="bg-warning">'+\
                             ' , '.join(null_risk_limits) + "</div>"

        if len(null_base_case_downsides) > 0:
            alert_message += '<strong><br><br> Following have Undefined or Zero Base case</strong>: ' \
                             '<div class="bg-warning">' + ' , '.join(null_base_case_downsides) + "</div>"

        if len(null_outlier_downsides) > 0:
            alert_message += '<strong><br><br> Following have Undefined or Zero Outlier</strong>: ' \
                             '<div class="bg-warning">' + ' , '.join(null_outlier_downsides) + "</div>"

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
                    PFA Daily Backup for Formulae Linked Downsides<br><br>
                    {0}
                  </body>
                </html>
        """.format(alert_message)

        exporters = {'FormulaeLinkedDownsides (' + datetime.datetime.now().date().strftime('%Y-%m-%d') + ').xlsx':
                         export_excel}

        subject = '(Risk Automation) FormulaeLinkedDownsides - ' + datetime.datetime.now().date().strftime('%Y-%m-%d')
        send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
                   recipients=['risk@wicfunds.com', 'rlogan@wicfunds.com'], subject=subject,
                   from_email='dispatch@wicfunds.com', html=html, EXPORTERS=exporters, dataframe=downsides_df)

    except Exception as e:
        print('Error Occured....')
        print(e)


def round_bps(value):
    return round((value/100), 2)


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

    loss_budgets = calculate_pnl_budgets()
    loss_budgets = loss_budgets.drop(columns=['Last Updated'])

    pivoted = pd.pivot_table(loss_budgets, columns=['Fund'], aggfunc=lambda x: x, fill_value='')
    pivoted = pivoted[['ARB', 'MACO', 'MALT', 'AED', 'CAM', 'LG', 'LEV']]
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
                               'YTD Active Deal Losses',
                            ])
    df1 = pivoted.iloc[:8].copy()
    df2 = pivoted.iloc[8:].copy()
    df3 = pd.DataFrame([list(pivoted.columns.values)], columns=list(pivoted.columns.values))
    df1 = df1.append(df3)
    df1.index.values[8] = 'Loss Budgets'
    df1 = df1.append(df2)
    df1.index.values[9] = 'Ann Loss Budget %'
    df1.index.values[0] = 'Investable Assets'
    df1.index.values[4] = 'Time Passed%'
    df1.index.values[11] = 'Time Passed %'
    df1 = df1.replace(np.nan, '', regex=True)

    now_date = datetime.datetime.now().date().strftime('%Y-%m-%d')

    def excel_formatting(row):
        ret = ["color:green" for _ in row.index]

        ret[row.index.get_loc("Sleeve_")] = "color:black"
        ret[row.index.get_loc("TradeGroup_")] = "color:black"
        ret[row.index.get_loc("Catalyst_")] = "color:black"

        if row['Total YTD PnL_AED'] < 0:
            ret[row.index.get_loc("Total YTD PnL_AED")] = "color:red"

        if row['Total YTD PnL_ARB'] < 0:
            ret[row.index.get_loc("Total YTD PnL_ARB")] = "color:red"

        if row['Total YTD PnL_CAM'] < 0:
            ret[row.index.get_loc("Total YTD PnL_CAM")] = "color:red"

        if row['Total YTD PnL_LEV'] < 0:
            ret[row.index.get_loc("Total YTD PnL_LEV")] = "color:red"

        if row['Total YTD PnL_LG'] < 0:
            ret[row.index.get_loc("Total YTD PnL_LG")] = "color:red"

        if row['Total YTD PnL_MACO'] < 0:
            ret[row.index.get_loc("Total YTD PnL_MACO")] = "color:red"

        if row['Total YTD PnL_MALT'] < 0:
            ret[row.index.get_loc("Total YTD PnL_MALT")] = "color:red"

        if row['Total YTD PnL_TACO'] < 0:
            ret[row.index.get_loc("Total YTD PnL_TACO")] = "color:red"

        if row['Total YTD PnL_TAQ'] < 0:
            ret[row.index.get_loc("Total YTD PnL_TAQ")] = "color:red"

        if row['Total YTD PnL_WED'] < 0:
            ret[row.index.get_loc("Total YTD PnL_WED")] = "color:red"

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

    styled_html = (df1.style.apply(style_funds).set_table_styles(styles).set_caption("PL Targets & Loss Budgets (" + now_date + ")"))

    html = """ \
                <html>
                  <head>
                  </head>
                  <body>
                    <p>PL Targets & Loss Budgets ({date})</p>
                    <a href="http://192.168.0.16:8000">Click to visit Realtime PL Targets & Loss Budgets Page</a>
                    <br><br>
                    {table}
                  </body>
                </html>
        """.format(table=styled_html.render(), date=now_date)

    def export_excel(df_list):
        with io.BytesIO() as buffer:
            writer = pd.ExcelWriter(buffer)
            workbook = writer.book
            sheet_names = ['Fund P&L Monitor', 'TradeGroup P&L']
            for i, df in enumerate(df_list):
                sheet_name = sheet_names[i]
                worksheet = workbook.add_worksheet(sheet_name)
                writer.sheets[sheet_name] = worksheet
                df.to_excel(writer, sheet_name=sheet_name, startrow=0, startcol=0)
            writer.save()
            return buffer.getvalue()

    final_live_df, final_daily_pnl, position_level_pnl, last_updated, fund_level_live = views.get_data()
    final_live_df = final_live_df.style.apply(excel_formatting, axis=1)

    exporters = {'PL Targets & Loss Budgets (' + now_date + ').xlsx': export_excel}
    subject = 'PL Targets & Loss Budgets - ' + now_date
    send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
               recipients=['vaggarwal@wicfunds.com', 'kgorde@wicfunds.com', 'cplunkett@wicfunds.com'],
               subject=subject, from_email='dispatch@wicfunds.com', html=html,
               EXPORTERS=exporters, dataframe=[df1, final_live_df])


def push_data_to_table(df):
    df = df.rename(columns={'Fund': 'fund', 'YTD Active Deal Losses': 'ytd_active_deal_losses',
                       'YTD Closed Deal Losses': 'ytd_closed_deal_losses', 'Loss Budget': 'ann_loss_budget_perc',
                       'AUM': 'investable_assets', 'Gross YTD P&L': 'gross_ytd_pnl', 'Time Passed': 'time_passed',
                       'Ann Gross P&L Target %': 'ann_gross_pnl_target_perc', 'Gross YTD Return': 'gross_ytd_return',
                       'Ann Gross P&L Target $': 'ann_gross_pnl_target_dollar', 'YTD P&L % of Target': 'ytd_pnl_perc_target',
                       'Ann Loss Budget $': 'ann_loss_budget_dollar', 'YTD Total Loss % of Budget': 'ytd_total_loss_perc_budget',
                       'Last Updated': 'last_updated'})
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
    sleeve_df = sleeve_df.drop('Metrics in NAV JSON' , axis=1)

    sleeve_df['Gross YTD Return'] = sleeve_df.apply(get_bps_value, axis=1)

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
    return loss_budgets


@shared_task
def calculate_realtime_pnl_budgets():
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()

    pnl_budgets = pd.read_sql('Select * from ' + settings.CURRENT_DATABASE + '.realtime_pnl_impacts_pnlmonitors where '\
                              'last_updated = (Select max(last_updated) from ' + settings.CURRENT_DATABASE +
                              '.realtime_pnl_impacts_pnlmonitors)', con=con)

    if 'id' in pnl_budgets.columns.values:
        pnl_budgets.drop(columns=['id'], inplace=True)

    final_live_df, final_daily_pnl, position_level_pnl, last_updated, fund_level_live = views.get_data()
    fund_daily_pnl = pd.Series([])
    fund_daily_pnl_sum = pd.Series([])
    daily_pnl_df = pd.DataFrame()
    columns = final_daily_pnl.columns.values
    for i, column in enumerate(columns):
        if "Daily" in column:
            fund_daily_pnl[i] = column.split("_")[-1]
            fund_daily_pnl_sum[i] = final_daily_pnl[column].sum()
    daily_pnl_df['fund'] = fund_daily_pnl
    daily_pnl_df['Daily P&L'] = fund_daily_pnl_sum
    realtime_pl_budget_df = pd.merge(pnl_budgets, daily_pnl_df, on=['fund'], how='left')
    realtime_pl_budget_df['gross_ytd_pnl'] = realtime_pl_budget_df['gross_ytd_pnl'].str.replace(',', '').apply(atof)
    realtime_pl_budget_df['gross_ytd_pnl'] = realtime_pl_budget_df['gross_ytd_pnl'] + realtime_pl_budget_df['Daily P&L']
    realtime_pl_budget_df['investable_assets'] = realtime_pl_budget_df['investable_assets'].str.replace(',', '').apply(atof)
    realtime_pl_budget_df['gross_ytd_return'] = realtime_pl_budget_df['gross_ytd_return'].str.replace('%', '').apply(atof)
    realtime_pl_budget_df['gross_ytd_return'] = realtime_pl_budget_df['gross_ytd_pnl']/realtime_pl_budget_df['investable_assets'] * 100
    realtime_pl_budget_df['gross_ytd_return'] = format_with_percentage_decimal(realtime_pl_budget_df, 'gross_ytd_return')
    realtime_pl_budget_df['investable_assets'] = format_with_commas(realtime_pl_budget_df, 'investable_assets')
    realtime_pl_budget_df['gross_ytd_pnl'] = format_with_commas(realtime_pl_budget_df, 'gross_ytd_pnl')
    realtime_pl_budget_df.drop(columns=['Daily P&L'], inplace=True)
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
