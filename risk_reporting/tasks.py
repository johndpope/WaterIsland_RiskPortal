import os
import sys
import time
import datetime
import io
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import django

django.setup()
from celery import shared_task
import pandas as pd
from risk_reporting.models import ArbNAVImpacts, DailyNAVImpacts, PositionLevelNAVImpacts, FormulaeBasedDownsides
from bbgclient import bbgclient
from django_slack import slack_message
import numpy as np

api_host = bbgclient.get_next_available_host()
from django.conf import settings
from sqlalchemy import create_engine
from email_utilities import send_email

@shared_task
def refresh_base_case_and_outlier_downsides():
    ''' Refreshes the base case and outlier downsides every 20 minutes for dynamically linked downsides '''
    import bbgclient
    # Create new Engine and Close Connections here
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                           + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)

    con = engine.connect()

    formulae_based_downsides = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_formulaebaseddownsides',
                                                 con=con)

    time.sleep(3)

    # Update the Last Prices of Each Deal
    api_host = bbgclient.bbgclient.get_next_available_host()
    # formulae_based_downsides['Underlying'] = formulae_based_downsides['Underlying'].apply(lambda x: ' '.join(x.split(' ')[:2]))
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
                    str(row['BaseCaseReferencePrice']) + str(row['BaseCaseOperation']) + str(
                        row['BaseCaseCustomInput']))
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
        FormulaeBasedDownsides.objects.all().delete()
        time.sleep(2)
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
    slack_message('navinspector.slack',
                  {'impacts': 'Base Case and Outlier Downsides refreshed...Working on NAV Impacts'})
    try:
        api_host = bbgclient.bbgclient.get_next_available_host()
        # Populate all the deals
        nav_impacts_positions_df = pd.read_sql_query(
            'SELECT * FROM test_wic_db.risk_reporting_arbnavimpacts where FundCode not like \'WED\'', con=con)
        # Drop the Last Price
        time.sleep(2)
        nav_impacts_positions_df.drop(columns=['LastPrice'], inplace=True)

        ytd_performances = pd.read_sql_query(
            'SELECT DISTINCT tradegroup, fund, pnl_bps FROM test_wic_db.realtime_pnl_impacts_arbitrageytdperformance',
            con=con)
        time.sleep(1)
        ytd_performances.columns = ['TradeGroup', 'FundCode', 'PnL_BPS']
        # Convert Underlying Ticker to format Ticker Equity
        nav_impacts_positions_df['Underlying'] = nav_impacts_positions_df['Underlying'].apply(
            lambda x: x + " EQUITY" if "EQUITY" not in x else x)
        forumale_linked_downsides = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_formulaebaseddownsides',
                                                      con=con)
        time.sleep(2)
        # Filter IsExcluded ones
        forumale_linked_downsides = forumale_linked_downsides[forumale_linked_downsides['IsExcluded'] == 'No']
        forumale_linked_downsides = forumale_linked_downsides[['TradeGroup', 'Underlying', 'base_case', 'outlier',
                                                               'LastUpdate', 'LastPrice']]

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
                return row['QTY'] * float(row['OptionLastPrice'])

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
                                  schema='test_wic_db')

        impacts = DailyNAVImpacts.objects.all()
        impacts_df = pd.DataFrame.from_records(impacts.values())

        def get_last_update_downside(row):
            return forumale_linked_downsides[forumale_linked_downsides['TradeGroup'] == row['TradeGroup']][
                'LastUpdate'].max()

        impacts_df['LastUpdate'] = impacts_df.apply(get_last_update_downside, axis=1)

        # NAV Impacts @ Position Level

        nav_impacts_positions_df = nav_impacts_positions_df.groupby(['FundCode', 'TradeGroup', 'Ticker', 'PM_BASE_CASE',
                                                                     'Outlier', 'LastPrice']).agg({
                                                                                      'BASE_CASE_NAV_IMPACT': 'sum',
                                                                                      'OUTLIER_NAV_IMPACT': 'sum',
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
                                        if_exists='append', index=False, schema='test_wic_db')

        slack_message('generic.slack', {'message': 'NAV Impacts refreshed with Latest Prices'},
                      channel='realtimenavimpacts',
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')
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
        return (row['Outlier'] * row['FxFactor'] * row['QTY']) - (row['CurrMktVal'] * row['FxFactor'])
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


@shared_task
def email_nav_impacts_report():
    """ Daily NAV Impacts Report run at 6.45am """
    try:
        engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                               + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
        con = engine.connect()
        df = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_dailynavimpacts', con=con)
        time.sleep(3)
        downsides_df = pd.read_sql_query(
            'SELECT TradeGroup, base_case, max(LastUpdate) as LastUpdate FROM '
            'test_wic_db.risk_reporting_formulaebaseddownsides where TargetAcquirer = \'Target\' and IsExcluded = \'No\''
            ' group by TradeGroup', con=con)
        time.sleep(3)
        arb_ytd_pnl = pd.read_sql_query(
            'select tradegroup, ytd_dollar from test_wic_db.realtime_pnl_impacts_arbitrageytdperformance where '
            'fund = \'ARB\' group by tradegroup', con=con)
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

        daily_nav_impacts.drop(columns=['id'], inplace=True)

        daily_nav_impacts = daily_nav_impacts[['TradeGroup', 'RiskLimit', 'Base Case (ARB)', 'Base Case (MACO)',
                                               'Base Case (MALT)', 'Base Case (AED)', 'Base Case (CAM)',
                                               'Base Case (LG)', 'Base Case (LEV)', 'Outlier (ARB)', 'Outlier (CAM)',
                                               'Outlier (LEV)', 'Outlier (LG)', 'Outlier (MACO)', 'Outlier (TAQ)',
                                               'Base Case (MALT)', 'Outlier (MALT)']]

        downsides_df.columns = ['TradeGroup', 'Downside Base Case', 'Last Downside Revision']

        df = df[['TradeGroup', 'RiskLimit', 'BASE_CASE_NAV_IMPACT_ARB']]

        df = pd.merge(df, downsides_df, on='TradeGroup')
        df.columns = ['TradeGroup', 'RiskLimit', 'NAV Impact', 'Downside Base Case', 'Last Update']
        df['NAV Impact'] = df['NAV Impact'].apply(lambda x: np.round(float(x), decimals=2))
        downsides_not_updated = df[pd.isna(df['Downside Base Case'])]['TradeGroup'].tolist()
        extra_message = '' if len(downsides_not_updated) == 0 else '<br><br> Please update downsides for these Tradegroups: ' + ', '.join(downsides_not_updated)
        df = df[~(pd.isna(df['Downside Base Case']))]
        df['Downside Base Case'] = df['Downside Base Case'].apply(lambda x: np.round(float(x), decimals=2))

        def get_impact_over_limit(row):
            if abs(row['RiskLimit']) <= abs(row['NAV Impact']):
                return np.round((row['RiskLimit'] - row['NAV Impact']), decimals=2)

            return np.round((row['RiskLimit'] - row['NAV Impact']), decimals=2)

        df['Impact Over Limit'] = df.apply(get_impact_over_limit, axis=1)
        df1 = df.sort_values(by=['Impact Over Limit'], ascending=False)
        df_over_limit = df1[df1['Impact Over Limit'] >= 0]
        df_under_limit = df1[df1['Impact Over Limit'] < 0]
        df_under_limit = df_under_limit.sort_values(by=['Impact Over Limit'], ascending=False)
        df = pd.concat([df_over_limit, df_under_limit])
        df['Impact Over Limit'] = df['Impact Over Limit'].apply(lambda x: str(x) + '%')
        df = pd.merge(df, arb_ytd_pnl, how='left', on='TradeGroup')

        df['(ARB) YTD $ P&L'] = df.apply(lambda x: "{:,}".format(int(x['(ARB) YTD $ P&L'])), axis=1)

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
                color = '#d17d00'

            return 'color: %s' % color

        df = df.style.applymap(color_negative_red, subset=['Impact Over Limit']).set_table_styles([
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
                    <a href="http://192.168.0.16:8000/risk_reporting/merger_arb_risk_attributes">
                    Click to visit Realtime NAV Impacts Page</a>{0}<br><br>
                    {1}
                  </body>
                </html>
        """.format(extra_message, df.hide_index().render(index=False))

        EXPORTERS = {'Merger Arb NAV Impacts (' + datetime.datetime.now().date().strftime('%Y-%m-%d') + ').xlsx':
                         export_excel}

        subject = '(Risk Automation) Merger Arb NAV Impacts - ' + datetime.datetime.now().date().strftime('%Y-%m-%d')
        send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
                   recipients=['risk@wicfunds.com', 'rlogan@wicfunds.com'],
                   subject=subject, from_email='dispatch@wicfunds.com', html=html,
                   EXPORTERS=EXPORTERS, dataframe=daily_nav_impacts)

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
            'SELECT * FROM '
            'test_wic_db.risk_reporting_formulaebaseddownsides ', con=con)
        time.sleep(3)

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
                    PFA Daily Backup for Formulae Linked Downsides
                  </body>
                </html>
        """

        EXPORTERS = {'FormulaeLinkedDownsides (' + datetime.datetime.now().date().strftime('%Y-%m-%d') + ').xlsx':
                         export_excel}

        subject = '(Risk Automation) FormulaeLinkedDownsides - ' + datetime.datetime.now().date().strftime('%Y-%m-%d')
        send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
                   recipients=['risk@wicfunds.com'], subject=subject, from_email='dispatch@wicfunds.com', html=html,
                   EXPORTERS=EXPORTERS, dataframe=downsides_df)

    except Exception as e:
        print('Error Occured....')
        print(e)
