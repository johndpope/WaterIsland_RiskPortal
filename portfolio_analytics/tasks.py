from django.conf import settings
import pandas as pd
from sqlalchemy import create_engine


SLEEVE_DICT = {
    'Equity Special Situations': 'ESS',
    'Merger Arbitrage': 'Arb',
    'Credit Opportunities': 'Credit'
}

def calculate_portfolio_analytics():
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()

    flat_file_df = pd.read_sql('select * from wic.daily_flat_file_db where Flat_file_as_of = (select '
                               'max(Flat_file_as_of) from wic.daily_flat_file_db);', con=con)
    con.close()
    as_of_date = flat_file_df['Flat_file_as_of'].max()
    flat_file_df = flat_file_df[flat_file_df['SecLevelLongShort'] != 'Unfilled']
    flat_file_df = flat_file_df[flat_file_df['DealStatus'] == 'ACTIVE']
    flat_file_df = flat_file_df[~(pd.isna(flat_file_df['CatalystTypeWIC']))]
    deal_universe_df = pd.DataFrame(columns=['deal_name', 'sleeve', 'bucket', 'catalyst_type', 'catalyst_rating', 
                                            'closing_date', 'target_ticker', 'long_short', 'target_last_price',
                                            'upside', 'spread', 'ask_px', 'days', 'gross_ror', 'ann_ror',
                                            'risk_percent', 'ann_risk', 'imp_prob', 'prob_adj_arr', 'return_risk',
                                            'imp_return_risk', 'note', 'last_updated'])

    deal_universe_df['bucket'] = flat_file_df['Bucket']
    deal_universe_df['deal_name'] = flat_file_df['TradeGroup']
    deal_universe_df['target_ticker'] = flat_file_df['Ticker']
    deal_universe_df['catalyst_type'] = flat_file_df['CatalystTypeWIC']
    deal_universe_df['catalyst_rating'] = flat_file_df['CatalystRating']
    deal_universe_df['closing_date'] = flat_file_df['ClosingDate']
    deal_universe_df['long_short'] = flat_file_df['LongShort']
    deal_universe_df['target_last_price'] = flat_file_df['TargetLastPrice']
    deal_universe_df['upside'] = flat_file_df['DealValue']
    return deal_universe_df
