from django.conf.urls import url
from . import views

app_name = 'credit_idea'

urlpatterns = [
    url('credit_idea_view$', views.CreditIdeaView.as_view(), name='credit_idea_view'),
    url('get_credit_idea_details/', views.get_credit_idea_details, name='get_credit_idea_details'),
    url('delete_credit_idea/', views.delete_credit_idea, name='delete_credit_idea'),
    url('credit_idea_details', views.CreditIdeaDetailsView.as_view(), name='credit_idea_details'),
]
