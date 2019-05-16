from django.core.management.base import BaseCommand, CommandError
import pandas as pd

from bbgclient import bbgclient
from risk.models import MA_Deals

class Command(BaseCommand):
    help = """
                Populate Action IDs for MA_Deals by matching the deals from the given file.
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
            help='Print the ma deals which matched with the deals in the given file. Also print the ones which did not match.'
        )

    def handle(self, *args, **options):
        print("Started executing the command...")
        count = 0
        dry_run = options.get('dry_run')
        file_path = options.get('file_path')
        skip_rows = options.get('skip_rows', 0)
        action_id_list = []
        try:
            skip_rows = [i for i in range(skip_rows[0])]
            file_path = file_path[0]
            print("Fetching data from the given file...")
            file_data = pd.read_excel(open(file_path, 'rb'), skiprows=skip_rows)
            print("Fetching MA Deals from the database...")
            ma_deals = MA_Deals.objects.filter(archived=False)
            file_data['Action ID'] = file_data['Action ID'].fillna(0)
            file_data['Action ID'] = file_data['Action ID'].astype(int)
            remaining = []
            if not dry_run:
                print("Updating the MA Deals...")
            for ma_deal in ma_deals:
                deal_name = ma_deal.deal_name
                df_row = file_data[file_data['Deal Name'] == deal_name]
                if not df_row.empty:
                    action_id = df_row['Action ID'].item()
                    if action_id:
                        action_id_list.append(str(action_id) + ' Action')
                        count += 1
                        if dry_run:
                            print('{deal_name} -> {action_id}'.format(deal_name=deal_name, action_id=action_id))
                        else:
                            ma_deal.action_id = action_id
                            ma_deal.save()
                    else:
                        remaining.append(deal_name)
                else:
                    remaining.append(deal_name)
            if not dry_run:
                print('{count} deals out of {total} deals updated.'.format(count=count, total=len(ma_deals)))
            else:
                print('{count} deals out of {total} deals will be updated.'.format(count=count, total=len(ma_deals)))
            if remaining:
                print('Following deals did not have a matching row in the given file.')
                print(remaining)
            # fields = ['CA052', 'CA054', 'CA057']
            # result = bbgclient.get_secid2field(action_id_list, 'tickers', fields, req_type='refdata')
            # if dry_run:
            #     print(result)
            # else:
            #     for ma_deal in ma_deals:
            #         action_id = str(ma_deal.action_id) + ' Action'
            #         if result.get(action):
            #             data = result[action_id]

            print("Successfully completed.")
        except Exception as e:
            print("Error occurred", e)
