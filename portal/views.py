from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.


def index_view(request):
    return render(request, 'home.html')


def handler404(request):
    return render(request, 'coming_soon.html', status=404)


def handler500(request):
    return render(request, 'error.html', status=500)

