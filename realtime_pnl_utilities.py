""" Utility Module to Update Existing Database with YTD PnL and Live PnL. Live PnL comes from separate module """
import os
import django
import pandas as pd
import dfutils
import dbutils
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
django.setup()
from django.conf import settings
from realtime_pnl_impacts.models import ArbitrageYTDPerformance
from django.db import connection


def daily_update_of_ytd_performance():
    """ Function to update the YTD performance database. Should run via Celery daily(Morning)
        Assumes that tradegroups_snapshot2 tables is updated via daily_calc process (Legacy)
    """
    df = dbutils.Wic.get_tradegroups_snapshot()
    df['EndDate'] = df['EndDate'].apply(lambda x: x if x is None else pd.to_datetime(x).strftime('%m/%d/%y'))
    df['InceptionDate'] = df['InceptionDate'].apply(
        lambda x: x if x is None else pd.to_datetime(x).strftime('%m/%d/%y'))

    # region formatting configuration
    metrics2include = [('P&L($)', 'YTD')]

    metric2display_name = {'P&L($)': ''}
    metric2unit = {'P&L($)': '$'}
    # endregion
    print(df['Fund'].unique())
    funds = ["ARB", "AED", "MACO", "MALT", "CAM", "LG", "LEV", "TACO", "TAQ"]
    fund2chart_tuple_list = []
    ArbitrageYTDPerformance.objects.all().delete()  # Delete current Performance.
    for f in funds:
        f_df = df[df['Fund'] == f].copy()

        if len(f_df) == 0:
            fund2chart_tuple_list.append((f, '<h9>NO DATA</h9>'))
            continue

        # unjsonify metrics, and append columns
        metrics_df = pd.DataFrame([dfutils.json2row(json) for json in f_df['Metrics in NAV JSON']])
        metrics_df.index = f_df.index

        cln2decimal_pts = {}
        colnames_to_sum = [ ]
        display_columns = [ ]
        for (metric, period) in metrics2include:
            unit = metric2unit[ metric ]
            disp_name = metric2display_name[ metric ]
            display_colname = disp_name + ' ' + period + '(' + unit + ')'
            f_df[ display_colname ] = metrics_df[ metric + '|' + period ]
            if unit == '$':
                cln2decimal_pts[ display_colname ] = 0
                colnames_to_sum.append(display_colname)
            if unit == 'bps':
                cln2decimal_pts[ display_colname ] = 1
                colnames_to_sum.append(display_colname)
            if unit == '%':
                cln2decimal_pts[ display_colname ] = 2
            display_columns.append(display_colname)

        del f_df['Metrics in NAV JSON']
        del f_df['Metrics in NAV notes JSON']
        del f_df['Metrics in Bet JSON']
        del f_df['Metrics in Bet notes JSON']
        del f_df['Analyst']

        sleeve2code = {'Merger Arbitrage': 'M&A',
                       'Equity Special Situations': 'ESS',
                       'Opportunistic': 'OPP',
                       'Forwards': 'FWD',
                       'Credit Opportunities': 'CREDIT'}

        f_df['Sleeve'] = f_df['Sleeve'].apply(lambda x: sleeve2code[x] if x in sleeve2code else x)
        f_df = f_df[
            (~pd.isnull(f_df[' YTD($)']))]  # don't show null ytds. i.e. tradegroups closed before year started

        base_cols = ['Fund', 'Sleeve', 'TradeGroup', 'LongShort', 'InceptionDate', 'EndDate', 'Status']
        dollar_cols = [' YTD($)']

        fund_dollar_df = f_df[base_cols + dollar_cols].sort_values(by=' YTD($)')

        fund_dollar_df['InceptionDate'] = fund_dollar_df['InceptionDate'].apply(pd.to_datetime)
        fund_dollar_df['EndDate'] = fund_dollar_df['EndDate'].apply(pd.to_datetime)

        fund_dollar_df.columns = ['fund', 'sleeve', 'tradegroup', 'long_short', 'inception_date', 'end_date', 'status',
                                  'ytd_dollar']

        fund_dollar_df.to_sql(name='realtime_pnl_impacts_arbitrageytdperformance', con=settings.SQLALCHEMY_CONNECTION,
                              if_exists='append',index=False, schema=settings.WICFUNDS_TEST_DATABASE_NAME)

daily_update_of_ytd_performance()