from datetime import datetime
import time

import pandas as pd
from django.conf import settings
from django.db import connection
from django_slack import slack_message
from slack_utils import get_channel_name
from sqlalchemy import create_engine

from risk_reporting.models import CreditDealsUpsideDownside


def update_credit_deals():
    """
    Function should run each morning.
    Adds new credit deals for Credit Deals Upside Downside
    """
    df = pd.read_sql('Select DISTINCT TradeGroup, Ticker, DealValue, Price, Analyst, OriginationDate, RiskLimit, '\
                     'DealUpside, DealDownside, BloombergID from wic.daily_flat_file_db where flat_file_as_of=(select '\
                     'max(Flat_file_as_of) from wic.daily_flat_file_db) and Sleeve="Credit Opportunities" and '\
                     'Amount <> 0 ORDER BY flat_file_as_of, TradeGroup', connection)
    credit_deals_df = pd.DataFrame.from_records(CreditDealsUpsideDownside.objects.all().values())
    credit_deals_df = credit_deals_df[credit_deals_df['tradegroup'].isin(df['TradeGroup']) & credit_deals_df['ticker'].isin(df['Ticker'])]
    credit_deals_merge = pd.merge(credit_deals_df, df, how='outer', left_on=['tradegroup', 'ticker'],
                                  right_on=['TradeGroup', 'Ticker'])
    credit_deals_merge = credit_deals_merge.reset_index().drop(columns=['id']).rename(columns={'index': 'id'})
    credit_deals_merge.drop(columns=['analyst', 'origination_date', 'deal_value', 'tradegroup', 'ticker', 'Price',
                                     'RiskLimit', 'DealUpside', 'DealDownside', 'bloomberg_id'], inplace=True)
    credit_deals_merge.rename(columns={'TradeGroup': 'tradegroup', 'Ticker': 'ticker', 'DealValue': 'deal_value',
                                       'Analyst': 'analyst', 'OriginationDate': 'origination_date',
                                       'BloombergID': 'bloomberg_id'}, inplace=True)
    credit_deals_merge['last_refreshed'] = datetime.now()
    credit_deals_merge['last_updated'] = datetime.now()
    credit_deals_merge['risk_limit'] = credit_deals_merge['risk_limit'].apply(lambda x: 0.0 if pd.isnull(x) else x)
    credit_deals_merge['last_price'] = credit_deals_merge['last_price'].apply(lambda x: 0.0 if pd.isnull(x) else x)
    credit_deals_merge['is_excluded'] = credit_deals_merge['is_excluded'].apply(lambda x: 'No' if pd.isnull(x) else x)
    credit_deals_merge['spread_index'] = credit_deals_merge['spread_index'].apply(lambda x: '' if pd.isnull(x) else x)
    credit_deals_merge['downside_notes'] = credit_deals_merge['downside_notes'].apply(lambda x: '' if pd.isnull(x) else x)
    credit_deals_merge['downside_type'] = credit_deals_merge['downside_type'].apply(lambda x: 'Fundamental Valuation' if pd.isnull(x) else x)
    credit_deals_merge['downside'] = credit_deals_merge['downside'].apply(lambda x: '' if pd.isnull(x) else x)
    credit_deals_merge['upside_notes'] = credit_deals_merge['upside_notes'].apply(lambda x: '' if pd.isnull(x) else x)
    credit_deals_merge['upside_type'] = credit_deals_merge['upside_type'].apply(lambda x: 'Fundamental Valuation' if pd.isnull(x) else x)
    credit_deals_merge['upside'] = credit_deals_merge['upside'].apply(lambda x: '' if pd.isnull(x) else x)
    current_credit_deals_df = pd.DataFrame.from_records(CreditDealsUpsideDownside.objects.all().values())
    try:
        CreditDealsUpsideDownside.objects.all().delete()
        time.sleep(3)
        engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" +
                               settings.WICFUNDS_DATABASE_PASSWORD + "@" + settings.WICFUNDS_DATABASE_HOST + "/" +
                               settings.WICFUNDS_DATABASE_NAME)
        con = engine.connect()
        credit_deals_merge.to_sql(con=con, name='risk_reporting_creditdealsupsidedownside',
                                  schema=settings.CURRENT_DATABASE, if_exists='append', chunksize=10000, index=False)
        slack_message('generic.slack',
                      {'message': 'Credit Deals upside/downside DB update from WIC ran successfully on: ' +
                                  datetime.now().strftime('%B %d, %Y %H:%M')},
                      channel=get_channel_name('realtimenavimpacts'),
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')
    except Exception as e:
        current_credit_deals_df.to_sql(con=con, name='risk_reporting_creditdealsupsidedownside',
                                       schema=settings.CURRENT_DATABASE, if_exists='append', chunksize=10000,
                                       index=False)
        slack_message('generic.slack',
                      {'message': 'ERROR: Credit Deals upside/downside DB populate had an error. The database has ' +
                                  'been restored to the previous data. Exception: ' + str(e)},
                      channel=get_channel_name('realtimenavimpacts'),
                      token=settings.SLACK_TOKEN,
                      name='ESS_IDEA_DB_ERROR_INSPECTOR')
    con.close()
