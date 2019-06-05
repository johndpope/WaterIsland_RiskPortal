from django.conf.urls import url

from position_rec import views

app_name = 'position_rec'

urlpatterns = [
    url('upload_files$', views.PositionRecAttachmentsView.as_view(), name='upload_files'),
    url('view_accounts$', views.AccountFundPositionRecView.as_view(), name='view_accounts'),
    url('view_breaks$', views.BreaksView.as_view(), name='view_breaks'),
    url('delete_ops_file/', views.delete_ops_file, name='delete_ops_file'),
    url('get_account_details/', views.get_account_details, name='get_account_details'),
    url('delete_account/', views.delete_account, name='delete_account'),
    url('edit_position_rec/', views.edit_position_rec, name='edit_position_rec'),
]
