from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import SecurityMaster
from django.db import connection
import pandas as pd

# Create your views here.


def wic_positions(request):
    # Populate Daily WIC Positions and Historical WIC Positions as of Certain date..
    as_of = "(SELECT MAX(Flat_file_as_of) from wic.daily_flat_file_db)"
    if 'as_of' in request.GET:
        as_of = "'" + request.GET['as_of'] + "'"

    df = SecurityMaster.objects.raw("SELECT 1 as id, flat_file_as_of, fund, Sleeve, Bucket, AlphaHedge, "
                                    "CatalystTypeWIC, CatalystRating, TradeGroup, Ticker, amount, Price, "
                                    "CurrentMktVal, aum, CurrentMktVal_Pct, CCY FROM wic.daily_flat_file_db "
                                    "where Flat_file_as_of = "+as_of)

    return render(request, 'wic_positions.html', {'positions': df, 'as_of': as_of})


def wic_positions_detailed_report_download(request):
    as_of = "'" + request.GET['as_of'] +"'"

    query = "SELECT * FROM wic.daily_flat_file_db where flat_file_as_of = "+as_of
    positions_df = pd.read_sql_query(query, con=connection)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=WicPositions.csv'
    positions_df.to_csv(path_or_buf=response, index=False)
    return response


def securitiy_master(request):
    all_securities = SecurityMaster.objects.all()
    return render(request, 'security_master.html', {'security_master':all_securities})


def add_new_deal_to_security_master(request):
    """ Adds a new deal to SecurityMaster Database """
    response = 'Failed'
    try:
        if request.method == 'POST':
            # First check if Prepopulation_request flag is set.
            if 'prepopulation_request'  in request.POST:
                # Do not add new deal. Only Return existing deal object
                id_to_retrieve = request.POST['deal_id']
                deal_object = list(SecurityMaster.objects.filter(id=id_to_retrieve).values_list())
                return JsonResponse({'deal_object': deal_object})

            # Process the Request
            deal_name = request.POST['deal_name']
            cash_terms = request.POST['cash_terms']
            stock_terms = request.POST['stock_terms']
            number_of_target_dividends = request.POST['number_of_target_dividends']
            number_of_acquirer_dividends = request.POST['number_of_acquirer_dividends']
            target_dividend_rate = request.POST['target_dividend_rate']
            acquirer_dividend_rate = request.POST['acquirer_dividend_rate']
            closing_date = request.POST['closing_date']

            SecurityMaster.objects.update_or_create(deal_name=deal_name,
                                                    defaults={'cash_terms': cash_terms,
                                                              'stock_terms': stock_terms,
                                                              'number_of_target_dividends':
                                                              number_of_target_dividends,
                                                              'number_of_acquirer_dividends':
                                                              number_of_acquirer_dividends,
                                                              'target_dividend_rate':
                                                              target_dividend_rate,
                                                              'acquirer_dividend_rate':
                                                              acquirer_dividend_rate,
                                                              'closing_date': closing_date
                                                              })

            response = 'Success'
    except Exception as err:
        print(err)

    return HttpResponse(response)


