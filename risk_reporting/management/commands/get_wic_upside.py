from datetime import datetime, date, timedelta
import json

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

import bbgclient
from ess_function import final_df
from risk.models import ESS_Idea, ESS_Peers


def extract_cix_value(row):
    ess_json = json.loads(row['ess_deal_json'])
    return ess_json.get('cix') if ess_json.get('cix') else np.nan


def extract_is_complete_checkbox_value(row):
    ess_json = json.loads(row['ess_deal_json'])
    is_complete_checkbox = True if ess_json.get('is_complete_checkbox') == 'true' else False
    return is_complete_checkbox


def extract_price_target_date(row):
    ess_json = json.loads(row['ess_deal_json'])
    price_target_date = ess_json.get('price_target_date')
    try:
        return datetime.strptime(price_target_date, '%m/%d/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        return np.nan


def extract_valuation_json(row):
    ess_json = json.loads(row['ess_deal_json'])
    result = {}
    for key, value in ess_json.items():
        if 'val_metric_name_' in key.lower():
            extract_id = key.split('_')[-1]
            weight_key = 'val_metric_weight_' + str(extract_id)
            weight = ess_json.get(weight_key, 0)
            try:
                weight = float(weight)
            except ValueError:
                weight = 0
            result[value.upper()] = weight
    return json.dumps([result])


def extract_peer_json(row):
    ess_json = json.loads(row['ess_deal_json'])
    result = {}
    for key, value in ess_json.items():
        if 'peer_ticker_' in key.lower():
            extract_id = key.split('_')[-1]
            weight_key = 'peer_weight_' + str(extract_id)
            weight = ess_json.get(weight_key, 0)
            try:
                weight = float(weight)
            except ValueError:
                weight = 0
            result[value.upper()] = weight * 100
    return json.dumps([result])


def extract_status(row):
    ess_json = json.loads(row['ess_deal_json'])
    status = ess_json.get('status', '')
    return status if status else np.nan


def custom_group_by(data):
    result = {}
    for row in data.iterrows():
        result[row[1].ticker.upper()] = row[1].hedge_weight
    data['peer_json'] = json.dumps([result])
    return data


from datetime import timedelta, date

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


class Command(BaseCommand):
    help = 'Get upside/downside from WIC database. Use `--dry-run` to print the data'
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print the data. No changes to the database will be made.'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        wic_df = pd.read_sql("SELECT * FROM wic.ess_idea_db;", connection)
        if not dry_run:
            print("Management command execution started. It might take a while. Hold on.")
        wic_df = wic_df[['Timestamp', 'VersionNumber', 'Alpha Ticker', 'Catalyst', 'Catalyst Tier', 'Deal Type',
                         'Estimated Unaffected Date', 'Estimated Close Date', 'Alpha Upside', 'ALpha Downside',
                         'ESS_DEAL_JSON']]
        wic_df.rename(columns={'Timestamp': 'created_on', 'VersionNumber': 'version_number',
                               'Alpha Ticker': 'alpha_ticker', 'Catalyst': 'catalyst', 'Catalyst Tier': 'catalyst_tier',
                               'Deal Type': 'deal_type', 'Estimated Unaffected Date': 'unaffected_date',
                               'Estimated Close Date': 'expected_close', 'Alpha Upside': 'alpha_upside',
                               'ALpha Downside': 'alpha_downside', 'ESS_DEAL_JSON': 'ess_deal_json'}, inplace=True)
        wic_df['cix_index'] = wic_df.apply(extract_cix_value, axis=1)
        wic_df['is_complete_checkbox'] = wic_df.apply(extract_is_complete_checkbox_value, axis=1)
        wic_df['price_target_date'] = wic_df.apply(extract_price_target_date, axis=1)
        wic_df['valuation_json'] = wic_df.apply(extract_valuation_json, axis=1)
        wic_df['peer_json'] = wic_df.apply(extract_peer_json, axis=1)
        wic_df['status'] = wic_df.apply(extract_status, axis=1)

        wic_df = wic_df[(wic_df['alpha_ticker'] != '') & ~pd.isna(wic_df['alpha_ticker']) & ~wic_df['alpha_ticker'].isnull()]
        
        wic_df = wic_df[~pd.isna(wic_df['status']) & ~wic_df['status'].isnull()]
        remove_rows = wic_df[(wic_df['status'] == 'Backlogged') | (wic_df['status'] == 'InProgress')]
        remove_tickers = remove_rows.alpha_ticker.unique()
        for ticker in remove_tickers:
            wic_df = wic_df[wic_df['alpha_ticker'] != ticker]
        wic_df = wic_df[~pd.isna(wic_df['unaffected_date']) & ~pd.isna(wic_df['expected_close'])]
        wic_df = wic_df[~wic_df['alpha_upside'].isnull() & ~pd.isna(wic_df['alpha_upside'])]
        wic_df = wic_df[~wic_df['alpha_downside'].isnull() & ~pd.isna(wic_df['alpha_downside'])]
        wic_df = wic_df[~wic_df['price_target_date'].isnull() & ~pd.isna(wic_df['price_target_date'])]
        wic_df['alpha_wic'] = 0
        wic_df.drop(columns=['ess_deal_json'], inplace=True)
        wic_df['source'] = 'WIC'

        ess_idea_df = pd.DataFrame.from_records(ESS_Idea.objects.all().values('id', 'alpha_ticker', 'unaffected_date',
                                                                              'expected_close', 'price_target_date',
                                                                              'cix_index', 'catalyst', 'catalyst_tier',
                                                                              'status', 'version_number', 'created_on',
                                                                              'multiples_dictionary', 'pt_up',
                                                                              'pt_down', 'pt_wic', 'deal_type'))
        ess_idea_df['is_complete_checkbox'] = False
        ess_idea_df = ess_idea_df[~pd.isna(ess_idea_df['status']) & ~ess_idea_df['status'].isnull()]
        remove_rows = ess_idea_df[(ess_idea_df['status'] == 'Backlogged') | (ess_idea_df['status'] == 'InProgress') | (ess_idea_df['status'] == 'Unallocated')]
        remove_tickers = remove_rows.alpha_ticker.unique()
        for ticker in remove_tickers:
            ess_idea_df = ess_idea_df[ess_idea_df['alpha_ticker'] != ticker]

        ess_peers_df = pd.DataFrame.from_records(ESS_Peers.objects.all().values('ticker', 'hedge_weight', 'ess_idea_id_id'))
        
        ess_peers_df['peer_json'] = ''
        ess_peers_df = ess_peers_df.groupby('ess_idea_id_id').apply(custom_group_by)
        ess_peers_df.drop(columns=['ticker', 'hedge_weight'], inplace=True)
        ess_peers_df = ess_peers_df.drop_duplicates()
        merged_ess_df = pd.merge(ess_idea_df, ess_peers_df, left_on=['id'], right_on=['ess_idea_id_id'], how='left')
        merged_ess_df.drop(columns=['ess_idea_id_id', 'id'], inplace=True)
        merged_ess_df.rename(columns={'multiples_dictionary': 'valuation_json', 'pt_up': 'alpha_upside',
                                      'pt_down': 'alpha_downside', 'pt_wic': 'alpha_wic'}, inplace=True)
        merged_ess_df['source'] = 'PROD'

        big_df = wic_df.append(merged_ess_df)
        big_df = big_df.sort_values(by='created_on')
        big_df['created_on'] = big_df['created_on'].dt.date
        big_df.rename(columns={'version_number': 'old_version'}, inplace=True)

        unique_tickers = big_df.alpha_ticker.unique().tolist()
        new_df = pd.DataFrame()
        for ticker in unique_tickers:
            temp_df = big_df[big_df['alpha_ticker'] == ticker]
            temp_df = temp_df.sort_values(['created_on', 'source'], ascending=[True, False])
            temp_df = temp_df.drop_duplicates(subset=['created_on', 'alpha_ticker'], keep='last')
            temp_df = temp_df.reset_index()
            temp_df['new_version'] = temp_df.index
            temp_df = temp_df.set_index('index')
            del temp_df.index.name
            new_df = new_df.append(temp_df)
        new_df = new_df.reset_index(drop=True)

        df_2017 = new_df[new_df['created_on'] >= date(2017, 1, 1)]
        unique_tickers = df_2017.alpha_ticker.unique().tolist()
        outcome_df = pd.DataFrame()
        for ticker in unique_tickers:
            temp_df = df_2017[df_2017['alpha_ticker'] == ticker]
            api_host = bbgclient.bbgclient.get_next_available_host()
            for i, (index, row) in enumerate(temp_df.iterrows()):
                file_name = "regression_" + ticker + "_" + str(row.new_version) +".xlsx"    
                if i == 0:
                    start_date = row['unaffected_date'] + timedelta(days=1)
                else:
                    start_date = row.created_on
                if (i + 1 == len(temp_df)):
                    if row.is_complete_checkbox:
                        end_date = row.expected_close
                    else:
                        end_date = datetime.today()
                else:
                    next_row = temp_df.iloc[i + 1]
                    end_date = next_row['created_on'] - timedelta(days=1)
                
                for_range = daterange(start_date, end_date)
                for as_of_date in for_range:
                    as_of_date = datetime.combine(as_of_date, datetime.min.time())
                    unaffected_date = row.unaffected_date.strftime('%Y-%m-%d')
                    expected_close = row.expected_close
                    price_target_date = row.price_target_date
                    peer_json = json.loads(row.peer_json)
                    if peer_json and len(peer_json) > 0:
                        peer_json = peer_json[0]
                    else:
                        peer_json = {}
                    val_json = json.loads(row.valuation_json)
                    if val_json and len(val_json) > 0:
                        val_json = val_json[0]
                    else:
                        val_json = {}
                    try:
                        final_df_result = final_df(alpha_ticker=ticker, cix_index=row.cix_index, unaffectedDt=unaffected_date,
                                               expected_close=expected_close, tgtDate=price_target_date,
                                               analyst_upside=row.alpha_upside, analyst_downside=row.alpha_downside,
                                               analyst_pt_wic=row.alpha_wic, peers2weight=peer_json,
                                               metric2weight=val_json, api_host=api_host,
                                               as_of_dt=as_of_date)
                        final_df_series = final_df_result['Final Results']
                        if not final_df_series.empty:
                            final_df_series = final_df_series.set_value('as_of_date', as_of_date.strftime('%Y-%m-%d'))
                            outcome_df = outcome_df.append(final_df_series, ignore_index=True)
                    except Exception as e:
                        print(ticker, row.new_version)
                        continue
            outcome_df.to_csv(file_name)
        import ipdb; ipdb.set_trace()

        if not dry_run:
            columns = ['alpha_ticker', 'deal_type', 'alpha_upside', 'alpha_downside', 'alpha_wic', 'catalyst',
                       'catalyst_tier', 'cix_index', 'unaffected_date', 'is_complete_checkbox', 'created_on',
                       'expected_close', 'price_target_date', 'status', 'old_version', 'new_version', 'source',
                       'peer_json', 'valuation_json']
            new_df.to_excel('wic_prod_data.xlsx', sheet_name='wic_prod_data', columns=columns, index=False)
            outcome_df.to_excel('outcome_df.xlsx', sheet_name='outcome_df', columns=columns, index=False)
            print("wic_prod_data.xlsx file created.")
        print(str(len(new_df.alpha_ticker.unique())) + ' unique alpha tickers present.')
        print(str(len(new_df)) + ' rows will be written to the excel file.')
        print("Successfully completed.")
