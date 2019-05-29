from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd

import dbutils
from portfolio_analytics.models import DealUniverse


def show_current_deal_universe(request):
    #Gather data from db_utils
    universe = DealUniverse.objects.all()

    return render(request,'deal_universe.html', context={'universe':universe})
