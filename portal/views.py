from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from django.db import connection
# Create your views here.


def index_view(request):
    aum_df = pd.read_sql_query("SELECT DISTINCT fund, aum FROM "
                               "wic.daily_flat_file_db WHERE "
                               "flat_file_as_of = (SELECT MAX(flat_file_as_of) FROM wic.daily_flat_file_db) AND "
                               "fund NOT IN ('ETF1', 'ETF2', 'INDEX1', 'INDEX2')",
                               con=connection)
    return render(request, 'home.html', {'aum_df': aum_df.to_json(orient='records')})


def handler404(request):
    return render(request, 'coming_soon.html', status=404)


def handler500(request):
    return render(request, 'error.html', status=500)

