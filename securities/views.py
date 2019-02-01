from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import SecurityMaster


# Create your views here.


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


