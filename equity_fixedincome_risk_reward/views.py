from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import pandas as pd
from django.db import connection
import requests
import datetime
import bbgclient
# Create your views here.

def list_speculated_deals(request):
    ''' Method to list all speculated deals '''
    #Query the Database for the Speculated Deals
    deals_df = pd.read_sql("SELECT * FROM wic.viper_universe where `Deal Status` = 'Proposed' and `Date Loaded` = (Select MAX(`Date Loaded`) from wic.viper_universe)"\
                           "order by `Date Loaded` desc;", connection)

    deals_df = deals_df[['Date Loaded', 'Action Id', 'Announce Date', 'Proposed Date', 'Target Ticker', 'Acquirer Ticker','Current Premium','Announced Premium']]
    deals_df['Date Loaded'] = pd.to_datetime(deals_df['Date Loaded'],unit='s')
    #Send to the Front End
    speculated_deals = deals_df.to_json(orient='records',date_format='iso')

    return render(request, 'speculated_mna_deals.html', context={'speculated_deals_df': speculated_deals})



def compare_equity_bond(request):
    response = ''
    if request.method == 'POST':
        # Get the tickers
        target_ticker = request.POST['target_ticker'] + ' Equity'
        bond_ticker = request.POST['bond_ticker']
        tickers = [target_ticker, bond_ticker]
        proposed_date = request.POST['proposed_date']
        api_host = bbgclient.bbgclient.get_next_available_host()
        if api_host is None: return HttpResponse('No Bloomberg Hosts available!')
        r = requests.get("http://"+api_host+"/wic/api/v1.0/general_histdata",
                             params={'idtype': "tickers", "fields": "PX_LAST,PX_DIRTY_MID",
                                     "tickers": ','.join(tickers),
                                     "override": "", "start_date": datetime.datetime.strptime(proposed_date,"%Y-%m-%d").strftime("%Y%m%d"), "end_date": datetime.datetime.now().strftime('%Y%m%d')},
                             timeout=15)  # Set a 15 secs Timeout

        results = r.json()['results']
        target_ticker_prices = results[0][target_ticker]['fields']['PX_LAST']
        bond_prices = results[1][bond_ticker]['fields']['PX_DIRTY_MID']
        target_ticker_dates = results[0][target_ticker]['fields']['date']
        bond_ticker_dates = results[1][bond_ticker]['fields']['date']

        chart_dictionary = {'target_ticker_prices':target_ticker_prices,'bond_prices':bond_prices,'target_ticker_dates':target_ticker_dates,'bond_dates':bond_ticker_dates}


        return JsonResponse(chart_dictionary, safe=False)

    else:
        #Just collect target ticker and render space for bond ticker
        target_ticker = request.GET['target_ticker']
        proposed_date = request.GET['proposed_date']
        return render(request,'compare_equity_bond.html',context={'target_ticker':target_ticker, 'proposed_date':proposed_date})


    return JsonResponse(response)