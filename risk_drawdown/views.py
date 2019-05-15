import pandas as pd
from django.shortcuts import render
from django.db import connection


# Create your views here.
def get_drawdowns(request):
    tradegroup_drawdowns = pd.read_sql_query("SELECT * FROM wic.risk_tradegroup_drawdown WHERE `Date` = "
                                             "(SELECT MAX(`Date`) FROM wic.risk_tradegroup_drawdown)", con=connection)

    sleeve_drawdowns = pd.read_sql_query("SELECT * FROM wic.risk_sleeve_drawdown WHERE `Date` = "
                                         "(SELECT MAX(`Date`) FROM wic.risk_sleeve_drawdown)", con=connection)

    bucket_drawdowns = pd.read_sql_query("SELECT * FROM wic.risk_bucket_drawdown WHERE `Date` = "
                                         "(SELECT MAX(`Date`) FROM wic.risk_bucket_drawdown)", con=connection)

    date_cols = ['Date', 'Last_Date']
    for each_date in date_cols:
        tradegroup_drawdowns[each_date] = tradegroup_drawdowns[each_date].apply(lambda x: x.strftime('%Y-%m-%d'))
        sleeve_drawdowns[each_date] = sleeve_drawdowns[each_date].apply(lambda x: x.strftime('%Y-%m-%d'))
        bucket_drawdowns[each_date] = bucket_drawdowns[each_date].apply(lambda x: x.strftime('%Y-%m-%d'))

    return render(request, 'risk_drawdowns.html', {'tradegroup_drawdowns':
                                                       tradegroup_drawdowns.to_json(orient='records'),
                                                   'sleeve_drawdowns': sleeve_drawdowns.to_json(orient='records'),
                                                   'bucket_drawdowns': bucket_drawdowns.to_json(orient='records')
                                                   })
