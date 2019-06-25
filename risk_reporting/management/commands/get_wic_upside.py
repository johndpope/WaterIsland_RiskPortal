from datetime import datetime
import json

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


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
            result[value] = weight
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
            result[value] = weight * 100
    return json.dumps([result])


def extract_status(row):
    ess_json = json.loads(row['ess_deal_json'])
    status = ess_json.get('status', '')
    return status if status else np.nan


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
        wic_df.rename(columns={'Timestamp': 'timestamp', 'VersionNumber': 'version_number',
                               'Alpha Ticker': 'alpha_ticker', 'Catalyst': 'catalyst', 'Catalyst Tier': 'catalyst_tier',
                               'Deal Type': 'deal_type', 'Estimated Unaffected Date': 'unaffected_date',
                               'Estimated Close Date': 'close_date', 'Alpha Upside': 'alpha_upside',
                               'ALpha Downside': 'alpha_downside', 'ESS_DEAL_JSON': 'ess_deal_json'}, inplace=True)
        wic_df['cix'] = wic_df.apply(extract_cix_value, axis=1)
        wic_df['is_complete_checkbox'] = wic_df.apply(extract_is_complete_checkbox_value, axis=1)
        wic_df['price_target_date'] = wic_df.apply(extract_price_target_date, axis=1)
        wic_df['valuation_json'] = wic_df.apply(extract_valuation_json, axis=1)
        wic_df['peer_json'] = wic_df.apply(extract_peer_json, axis=1)
        wic_df['status'] = wic_df.apply(extract_status, axis=1)

        wic_df = wic_df[(wic_df['alpha_ticker'] != '') & ~pd.isna(wic_df['alpha_ticker']) & ~wic_df['alpha_ticker'].isnull()]
        wic_df = wic_df[~pd.isna(wic_df['status']) & ~wic_df['status'].isnull() & (wic_df['status'] != 'Backlogged') & (wic_df['status'] != 'InProgress')]
        wic_df = wic_df[~pd.isna(wic_df['unaffected_date']) & ~pd.isna(wic_df['close_date'])]
        wic_df = wic_df[~wic_df['alpha_upside'].isnull() & ~pd.isna(wic_df['alpha_upside'])]
        wic_df = wic_df[~wic_df['alpha_downside'].isnull() & ~pd.isna(wic_df['alpha_downside'])]
        wic_df = wic_df[~wic_df['price_target_date'].isnull() & ~pd.isna(wic_df['price_target_date'])]
        wic_df.drop(columns=['ess_deal_json'], inplace=True)
        if not dry_run:
            wic_df.to_excel('final_wic_upside.xlsx')
            print("final_wic_upside.xlsx file created.")
        print(str(len(wic_df.alpha_ticker.unique())) + ' unique alpha tickers present.')
        print(str(len(wic_df)) + ' rows will be written to the excel file.')
        print("Successfully completed.")
