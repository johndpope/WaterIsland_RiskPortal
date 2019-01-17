from django.shortcuts import render
import dbutils
import pandas as pd
from django.http import HttpResponse, JsonResponse
import json
from celery.result import AsyncResult
from celery import shared_task
from django import db
from .tasks import get_statpro_attribution

job_id = 0

def test_statpro():
    pass




def get_attribution(request):
    db.connection.close()
    attribution_list = []

    if request.method == 'POST':
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        fund_name = request.POST['fund_name']
        job = get_statpro_attribution.delay(start_date, end_date, fund_name)
        return HttpResponse(job.get())

    else:
        fund_names = dbutils.Wic.get_distinct_funds_from_statpro()['name']
        # Append TradeGroup Attribution
        for fund in fund_names:
            attribution_list.append(fund)
            attribution_list.append(fund+"- By TradeGroup")

    return render(request, 'statpro_attribution.html',context={'attributions':attribution_list})