from django.conf.urls import url
from position_rec.views import (delete_account, delete_ops_file, get_account_details, AccountFundPositionRecView,
    PositionRecAttachmentsView)

app_name = 'position_rec'

urlpatterns = [
    url('view_accounts$', AccountFundPositionRecView.as_view(), name='view_accounts'),
    url('upload_files$', PositionRecAttachmentsView.as_view(), name='upload_files'),
    url('delete_ops_file/', delete_ops_file, name='delete_ops_file'),
    url('get_account_details/', get_account_details, name='get_account_details'),
    url('delete_account/', delete_account, name='delete_account'),
]
