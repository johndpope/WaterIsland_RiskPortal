from datetime import datetime

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from sqlalchemy import create_engine


class Command(BaseCommand):
    help = """
                Populate Account Fund Mapping Table from the given file.
                The management command has 2 positional arguments:
                    1.) File Path          String of entire file path
                    2.) Skip Rows          Integer value indicating number of rows to skip starting from 0.
            """
    def add_arguments(self, parser):
        parser.add_argument('file_path', nargs='+', type=str)
        parser.add_argument('skip_rows', nargs='+', type=int)
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print the account-fund mapping from the given excel file.'
        )

    def handle(self, *args, **options):
        print("Started executing the command...")
        dry_run = options.get('dry_run')
        file_path = options.get('file_path')
        skip_rows = options.get('skip_rows', 0)
        try:
            skip_rows = [i for i in range(skip_rows[0])]
            file_path = file_path[0]
            print("Fetching data from the given file...")
            file_data = pd.read_excel(open(file_path, 'rb'), skiprows=skip_rows)
            file_data['Date Updated'] = datetime.now()
            if 'Options' in file_data.columns.values.tolist():
                file_data.drop(columns=['Options'], inplace=True)
            if dry_run:
                print(file_data)
            else:
                file_data.rename(columns={'Date Updated': 'date_updated', 'Custodian': 'third_party',
                                          'Account Number': 'account_no', 'Mnemonic': 'mnemonic', 'Type': 'type',
                                          'Fund': 'fund', 'Excluded': 'excluded'}, inplace=True)

                engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" +
                                       settings.WICFUNDS_DATABASE_PASSWORD + "@" + settings.WICFUNDS_DATABASE_HOST + "/"
                                       + settings.WICFUNDS_DATABASE_NAME)
                con = engine.connect()
                file_data.to_sql(con=con, name='position_rec_accountfundpositionrec', schema=settings.CURRENT_DATABASE,
                                 if_exists='append', chunksize=10000, index=False)
                con.close()
                print("Data populated.")
                print("Please visit the below link to view Account-Fund Mapping.")
                print("http://192.168.0.16:8000/position_rec/view_accounts")

            print("Successfully completed.")
        except Exception as e:
            print("Error occurred", e)
