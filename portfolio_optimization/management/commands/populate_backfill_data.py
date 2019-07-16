import datetime
from os import listdir
from os.path import isfile, join
import re 
import json
import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from sqlalchemy import create_engine

from portfolio_optimization.models import EssUniverseImpliedProbability
from portfolio_optimization.views import get_implied_prob_df


MY_PATH = 'C:\\Users\\vagarwal\\Desktop\\Regression files'


class Command(BaseCommand):
    help = 'Populate Count for all deal types in Implied Prob table. Use `--dry-run` to print the deal types and their counts.'
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print the deal types and their counts. No changes to the database will be made.'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        regression_files = [f for f in listdir(MY_PATH) if isfile(join(MY_PATH, f))]
        # unique_ticker_files = set()
        # for regression_file in regression_files:
        #     unique_ticker_files.add(get_file_name_without_version(regression_file))
        # unique_ticker_files = list(unique_ticker_files)
        # for ticker_file in unique_ticker_files:
        #     res = [x for x in regression_files if re.search(ticker_file, x)]
        main_df = pd.DataFrame()
        required_columns = ['Alpha Ticker', 'Expected Close Date', 'Unaffected Date', 'Alpha Last Price',
                            'Alpha Upside', 'Alpha Downside', 'Alpha PT (WIC)', 'Up Price (Regression)',
                            'Down Price (Regression)', 'PT WIC Price (Regression)', 'as_of_date', 'Ann. Return(%)',
                            'CIX', 'Return/Risk']
        for regression_file in regression_files:
            try:
                temp_df = pd.read_excel(MY_PATH + '\\' + regression_file)
                temp_df = temp_df[required_columns]
                temp_df['as_of_date'] = temp_df['as_of_date'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
                temp_df = temp_df[temp_df['as_of_date'] <= datetime.date(2019, 7, 3)]
                temp_df['as_of_date'] = temp_df['as_of_date'].dt.strftime('%Y-%m-%d')
                main_df = main_df.append(temp_df)
            except KeyError:
                print(regression_file)
        import ipdb; ipdb.set_trace()


def get_file_name_without_version(filename):
    return "_".join(i for i in filename.split("_")[:-1])
