import pandas as pd
import ast
import json
import sys
import risk.tasks
import datetime


def populate_new_ess_idea_db_from_old_db():
    import pandas as pd
    from sqlalchemy import create_engine
    engine = create_engine("mysql://root:Mkaymkay1@10.16.1.19/wic")
    wic_con = engine.connect()
    query = 'SELECT ' \
            'A.`dealKey`,' \
            'A.`Created`, ' \
            'A.`Timestamp`,' \
            'A.`VersionNumber`,  ' \
            'A.`CreatedByAnalyst`, ' \
            'A.`Alpha Ticker`,  ' \
            'A.`Definiteness`,  ' \
            'A.`Catalyst`, ' \
            'A.`Catalyst Tier`,  ' \
            'A.`Deal Type`,  ' \
            'A.`Estimated Unaffected Date`,  ' \
            'A.`Estimated Close Date`,  ' \
            'A.`Alpha Upside`,  ' \
            'A.`ALpha Downside`,  ' \
            'A.`Description`,  ' \
            'A.`IsActive`,  ' \
            'A.`ESS_DEAL_JSON`' \
            'FROM  wic.`ess_idea_db` as A where IsActive = 0 and Catalyst is not null'
    old_deals = pd.read_sql_query(query, con=wic_con)

    # Logic ...GO through Each Old Alpha Ticker and Concat a column to the old_deals Dataframe
    final_concat = pd.DataFrame()

    for index, row in old_deals.iterrows():
        # Only take relevant keys from the dictionary....Drop others (eg, FileContainers...)
        original_dictionary = ast.literal_eval(row['ESS_DEAL_JSON'])

        # Remove File Containers from the dictionary
        for key in original_dictionary.copy().keys():
            if key.startswith('FileContainer') or key.startswith('Activists') or key.startswith('event_') \
                    or key.startswith('financing') or key.startswith('news_'):
                del original_dictionary[key]

        to_concat = pd.DataFrame(original_dictionary, index=[index])

        final_concat = pd.concat([final_concat, to_concat])

    # Merge the concatenated with the Old_deals df

    final_concat.dropna(subset=['DealKey'], inplace=True)
    final_concat['DealKey'] = final_concat['DealKey'].apply(lambda x: pd.to_numeric(x.replace("\"", "")))

    old_deals = pd.merge(old_deals, final_concat, how='inner', left_on=['dealKey', 'Alpha Ticker'],
                         right_on=['DealKey', 'alpha_ticker_in_form_textbox'])
    df = pd.read_excel('ess_deals_category.xlsx', header=4)
    df.dropna(subset=['Ticker'], inplace=True)
    df = df[['Ticker', 'Category', 'Deal Type', 'Hedges?', 'Unaffected Date', 'Closing']].reset_index().drop(columns=['index']).rename(
        columns={'Hedges?': 'Hedges'})

    df['Unaffected Date'] = df['Unaffected Date'].apply(lambda x: x.strftime('%Y-%m-%d'))

    df['Closing'] = df['Closing'].apply(
        lambda x: x.strftime('%Y-%m-%d'))

    df['Ticker'] = df['Ticker'].apply(lambda x: x + ' EQUITY')
    old_deals['Alpha Ticker'] = old_deals['Alpha Ticker'].apply(lambda x: x.strip())

    df['Hedges'] = df['Hedges'].apply(lambda x: 'Yes' if x == 'Y' else 'No')

    # old_deals.to_csv('Indpec2.csv')
    merged_df = pd.merge(old_deals, df, how='inner', left_on=['Alpha Ticker'], right_on=['Ticker'])
    merged_df.drop_duplicates(['Alpha Ticker', 'VersionNumber'], keep='last', inplace=True)

    # Create a subset of Relevant  Columns
    cols2consider = ['dealKey', 'Created', 'VersionNumber', 'CreatedByAnalyst', 'Alpha Ticker', 'Catalyst',
                     'Catalyst Tier',
                     'Unaffected Date', 'Closing', 'Alpha Upside', 'ALpha Downside',
                     'textarea', 'alpha_down_price_note_textarea', 'alpha_up_price_note_textarea', 'cix',
                     'peer_ticker_1',
                     'peer_ticker_2', 'peer_ticker_3', 'peer_ticker_4', 'peer_ticker_5', 'peer_ticker_6',
                     'peer_ticker_7',
                     'peer_ticker_8', 'peer_weight_1', 'peer_weight_2', 'peer_weight_3', 'peer_weight_4',
                     'peer_weight_5',
                     'peer_weight_6', 'peer_weight_7', 'peer_weight_8', 'price_target_date', 'status',
                     'val_metric_name_1',
                     'val_metric_name_2', 'val_metric_name_3', 'val_metric_name_4', 'val_metric_name_5',
                     'val_metric_weight_1',
                     'val_metric_weight_2', 'val_metric_weight_3', 'val_metric_weight_4', 'val_metric_weight_5',
                     'Category', 'Deal Type_y', 'Hedges']

    merged_df = merged_df[cols2consider].rename(
        columns={'Deal Type_y': 'Deal Type', 'ALpha Downside': 'Alpha Downside'})

    print('Total deals to be inserted are: '+ str(len(merged_df)))

    print('After removing deals left to process are:  '+ str(len(merged_df)))



    for index, row in merged_df.iterrows():
        # Create Inputs for Celery Task...
        bull_thesis_model_file = None
        our_thesis_model_file = None
        bear_thesis_model_file = None
        update_id = 'false'
        ticker = row['Alpha Ticker']
        situation_overview = row['textarea']
        company_overview = ""
        bull_thesis = row['alpha_up_price_note_textarea']
        our_thesis = ""
        bear_thesis = row['alpha_down_price_note_textarea']
        pt_up = float(row['Alpha Upside'])
        # Assume pt_wic as avg. of upside and downside. Get Value later from the ESS team...
        pt_wic = pt_up - 0.15 * pt_up

        pt_down = float(row['Alpha Downside'])
        unaffected_date = row['Unaffected Date']
        expected_close = row['Closing']
        m_value = 0
        o_value = 0
        s_value = 0
        a_value = 0
        i_value = 0
        c_value = 0
        m_overview = ''
        o_overview = ''
        s_overview = ''
        a_overview = ''
        i_overview = ''
        c_overview = ''

        ticker_hedge = []

        for i in range(1, 9):
            if not pd.isnull(row['peer_ticker_' + str(i)]):
                ticker_hedge.append(
                    {'ticker': row['peer_ticker_' + str(i)], 'hedge': float(row['peer_weight_' + str(i)]) * 100})

        multiples_dictionary = []
        # Repeat for Multiples Dictionary
        for i in range(1, 6):
            if not pd.isnull(row['val_metric_name_' + str(i)]):
                multiples_dictionary.append({row['val_metric_name_' + str(i)]: row['val_metric_weight_' + str(i)]})

        ticker_hedge_length = len(ticker_hedge)

        cix_index = row['cix']
        price_target_date = row['price_target_date']
        multiples = json.dumps(multiples_dictionary)
        category = row['Category']
        catalyst = row['Catalyst']
        deal_type = row['Deal Type']
        catalyst_tier = row['Catalyst Tier']
        hedges = row['Hedges']
        gics_sector = 'Will be populated later!'
        lead_analyst = row['CreatedByAnalyst']
        status = row['status']
        version_number = row['VersionNumber']

        id = int(row['dealKey'])

        price_target_date = datetime.datetime.strptime(price_target_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        tradegroup = ''

        risk.tasks.add_new_idea.delay(bull_thesis_model_file, our_thesis_model_file, bear_thesis_model_file, tradegroup,
                                      update_id, ticker, situation_overview, company_overview, bull_thesis, our_thesis,
                                      bear_thesis, pt_up, pt_wic, pt_down, unaffected_date, expected_close, m_value,
                                      o_value, s_value, a_value, i_value, c_value, m_overview, o_overview, s_overview,
                                      a_overview, i_overview, c_overview, ticker_hedge_length, json.dumps(ticker_hedge),
                                      cix_index, price_target_date, multiples, category, catalyst, deal_type,
                                      catalyst_tier, hedges, gics_sector, lead_analyst, status, version_number, id)


    return None

import time
populate_new_ess_idea_db_from_old_db()
