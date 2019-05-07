from django.core.management.base import BaseCommand, CommandError
from wic_news.models import NewsMaster

class Command(BaseCommand):
    help = 'Append `US` to Tickers in NewsMaster table. Use `--dry-run` to print the tickers that needs to be updated.'
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print the tickers which should be updated. No changes to the database will be made.'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        news_master = NewsMaster.objects.all()
        count = 0
        if not dry_run:
            print("Management command execution started. It might take a while. Hold on.")
        for news in news_master:
            news_ticker = news.tickers
            if news_ticker:
                ticker_list = news_ticker.split(',')
                ticker_list = [item.strip() for item in ticker_list]
                for index, ticker in enumerate(ticker_list):
                    ticker = ticker.strip()
                    ticker_split = ticker.split(' ')
                    ticker_split = [item.split() for item in ticker_split]
                    if len(ticker_split) == 1:
                        ticker = ticker.upper() + ' US'
                        ticker_list[index] = ticker
                updated_ticker = ', '.join(ticker for ticker in ticker_list)
                if updated_ticker != news_ticker:
                    count += 1
                    if dry_run:
                        print(news_ticker + ' -> ' + updated_ticker)
                    else:
                        news.tickers = updated_ticker
                        news.save()
        if dry_run:
            print("{count} ticker(s) needs to be updated in NewsMaster table.".format(count=count))
        else:
            print("{count} ticker(s) have been updated in NewsMaster table.".format(count=count))
            print("Successfully updated.")
