from django.shortcuts import render
import dbutils
from django.http import JsonResponse
import pandas as pd
from .models import DealUniverse

# Create your views here.
def show_current_deal_universe(request):
    #Gather data from db_utils
    universe = DealUniverse.objects.all()

    return render(request,'deal_universe.html', context={'universe':universe})