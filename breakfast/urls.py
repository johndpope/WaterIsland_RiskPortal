from django.conf.urls import url
from . import views

urlpatterns = [
    url('submit_breakfast_order',views.submit_breakfast_order, name='submit_breakfast_order'),
]
