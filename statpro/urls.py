from django.conf.urls import url
from . import views
app_name = 'statpro'

urlpatterns = [
    url('get_attribution/', views.get_attribution, name='get_attribution'),
]