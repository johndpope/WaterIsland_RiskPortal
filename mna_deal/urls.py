from django.conf.urls import url, include

from mna_deal import views

app_name = 'mna_deal'

urlpatterns = [
    url('create_mna_deal$', views.CreateMaDealsView.as_view(), name='create_mna_deal'),
]
