""" URL Mapping to Controller for Securities App. """
from django.conf.urls import url
from . import views

app_name = 'securities'

urlpatterns = [
    url('securitiy_master$', views.securitiy_master, name='securitiy_master'),
    url('add_new_deal_to_security_master$', views.add_new_deal_to_security_master,
        name='add_new_deal_to_security_master'),
    url('wic_positions$', views.wic_positions,
        name='wic_positions'),
    url('wic_positions_detailed_report_download$', views.wic_positions_detailed_report_download,
        name='wic_positions_detailed_report_download'),

]
