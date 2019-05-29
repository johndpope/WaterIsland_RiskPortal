from django.conf import settings
import pandas as pd
from sqlalchemy import create_engine


SLEEVE_DICT = {
    'Equity Special Situations': 'ESS',
    'Merger Arbitrage': 'Arb',
    'Credit Opportunities': 'Credit'
}

def calculate_portfolio_optimization():
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
    flat_file_df = flat_file_df[flat_file_df['Sleeve'] != 'Opportunistic']
    unique_catalyst_type = ['HARD', 'SOFT']
    unique_catalyst_rating = [1, 2, 3]
    sleeve = 'Merger Arbitrage'
    unique_long_short = flat_file_df.LongShort.unique().tolist()
    df_soft = pd.DataFrame(columns=['Catalyst', 'Tier', 'Sleeve', 'Strategy', 'CurrentLongs', 'CurrentAUMLongs', 'CurrentShorts', 'CurrentAUMShorts'])
    df_hard = pd.DataFrame(columns=['Catalyst', 'Tier', 'Sleeve', 'Strategy', 'CurrentLongs', 'CurrentAUMLongs', 'CurrentShorts', 'CurrentAUMShorts'])

    for catalyst_type in unique_catalyst_type:
        for catalyst_rating in unique_catalyst_rating:
            row_dict = {'Catalyst': catalyst_type, 'Tier': catalyst_rating, 'Sleeve': SLEEVE_DICT.get(sleeve), 'Strategy': catalyst_type + "-" + str(catalyst_rating) + " Equity"}
            for long_short in unique_long_short:
                df = flat_file_df[(flat_file_df['Fund'] == 'AED') & (flat_file_df['Sleeve'] == sleeve) & (flat_file_df['CatalystTypeWIC'] == catalyst_type) & (flat_file_df['CatalystRating'] == catalyst_rating) & (flat_file_df['LongShort'] == long_short) & (flat_file_df['AlphaHedge'] == 'Alpha')]
                sum_pct_sleeve_current = df['PctOfSleeveCurrent'].sum()
                count = len(df['TradeGroup'].unique())
                if long_short == 'Long':
                    row_dict.update({'CurrentLongs': count, 'CurrentAUMLongs': sum_pct_sleeve_current})
                elif long_short == 'Short':
                    row_dict.update({'CurrentShorts': count, 'CurrentAUMShorts': sum_pct_sleeve_current})
            if row_dict.get('CurrentLongs') and row_dict.get('CurrentLongs') > 0 or row_dict.get('CurrentShorts') and row_dict.get('CurrentShorts') > 0:
                if catalyst_type == 'HARD':
                    df_hard = df_hard.append(row_dict, ignore_index=True)
                elif catalyst_type == 'SOFT':
                    df_soft = df_soft.append(row_dict, ignore_index=True)
            row_dict = {}

    sleeves = ['Equity Special Situations', 'Credit Opportunities']
    for catalyst_type in unique_catalyst_type:
        for sleeve in sleeves:
            row_dict = {'Catalyst': catalyst_type, 'Tier': '-', 'Sleeve': SLEEVE_DICT.get(sleeve), 'Strategy': catalyst_type + " " + SLEEVE_DICT.get(sleeve)}
            for long_short in unique_long_short:
                df = flat_file_df[(flat_file_df['Fund'] == 'AED') & (flat_file_df['Sleeve'] == sleeve) & (flat_file_df['CatalystTypeWIC'] == catalyst_type) & (flat_file_df['LongShort'] == long_short) & (flat_file_df['AlphaHedge'] == 'Alpha')]
                sum_pct_sleeve_current = df['PctOfSleeveCurrent'].sum()
                count = len(df['TradeGroup'].unique())
                
                if long_short == 'Long':
                    row_dict.update({'CurrentLongs': count, 'CurrentAUMLongs': sum_pct_sleeve_current})
                elif long_short == 'Short':
                    row_dict.update({'CurrentShorts': count, 'CurrentAUMShorts': sum_pct_sleeve_current})
            if row_dict.get('CurrentLongs') and row_dict.get('CurrentLongs') > 0 or row_dict.get('CurrentShorts') and row_dict.get('CurrentShorts') > 0:
                if catalyst_type == 'HARD':
                    df_hard = df_hard.append(row_dict, ignore_index=True)
                elif catalyst_type == 'SOFT':
                    df_soft = df_soft.append(row_dict, ignore_index=True)
    return df_hard, df_soft, as_of_date
