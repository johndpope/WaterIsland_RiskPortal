from django.conf.urls import url
from . import views

app_name = 'exposures'

urlpatterns = [
    url('exposures_snapshot$',views.get_exposures_snapshot,name='exposures_snapshot'),
]


