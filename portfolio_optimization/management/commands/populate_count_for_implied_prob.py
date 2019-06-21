import json
import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from sqlalchemy import create_engine

from portfolio_optimization.models import EssUniverseImpliedProbability
from portfolio_optimization.views import get_implied_prob_df

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
        implied_prob_df = pd.DataFrame.from_records(EssUniverseImpliedProbability.objects.all().values())
        count = 0
        errors = False
        if not dry_run:
            print("Management command execution started. It might take a while. Hold on.")
        query = "SELECT DISTINCT flat_file_as_of as `Date`, TradeGroup, Fund, Ticker,Price, LongShort, SecType, " \
                "DealUpside, DealDownside FROM wic.daily_flat_file_db WHERE " \
                "Fund IN ('AED', 'TAQ') and AlphaHedge = 'Alpha' AND LongShort IN ('Long', 'Short') " \
                "AND SecType = 'EQ' AND Sleeve = 'Equity Special Situations' and amount <> 0;"\

        imp_prob_tracker_df = pd.read_sql_query(query, con=connection)
        new_count_df = pd.DataFrame(columns=['id', 'deal_type', 'new_count'])
        for index, row in implied_prob_df.iterrows():
            date = row.Date
            deal_type = row.deal_type
            df = imp_prob_tracker_df[imp_prob_tracker_df['Date'] == date]
            try:
                implied_prob_drilldown_df = get_implied_prob_df(df, date, deal_type, get_df=True)
            except Exception as e:
                print(e)
                errors = True
                implied_prob_drilldown_df = None
            if not implied_prob_drilldown_df.empty:
                df_count = implied_prob_drilldown_df['implied_probability'].count()
            else:
                df_count = 0
            count += 1
            if dry_run:
                print(date, deal_type + ' -> ' + str(df_count))
            else:
                new_count_df.loc[-1] = [row.id, deal_type, df_count]
                new_count_df.index = new_count_df.index + 1
        if dry_run:
            print("{count} deal type(s) needs to be updated in EssUniverseImpliedProbability table.".format(count=count))
        else:
            if not errors:
                merged_df = pd.merge(new_count_df, implied_prob_df, on=['id', 'deal_type'])
                merged_df.drop(columns=['count'], inplace=True)
                merged_df.rename(columns={'new_count': 'count'}, inplace=True)
                EssUniverseImpliedProbability.objects.all().delete()
                try:
                    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" +
                                       settings.WICFUNDS_DATABASE_PASSWORD + "@" + settings.WICFUNDS_DATABASE_HOST +
                                       "/" + settings.WICFUNDS_DATABASE_NAME)

                    con = engine.connect()
                    merged_df.to_sql(con=con, if_exists='append', schema=settings.CURRENT_DATABASE,
                             name='portfolio_optimization_essuniverseimpliedprobability', index=False)
                except Exception as e:
                    print(e)
                    implied_prob_df.to_sql(con=con, if_exists='append', schema=settings.CURRENT_DATABASE,
                                       name='portfolio_optimization_essuniverseimpliedprobability', index=False)
                print("{count} deal(s) have been updated in EssUniverseImpliedProbability table.".format(count=count))
                print("Successfully updated.")
        if errors:
            print('Management command stopped because of error')
