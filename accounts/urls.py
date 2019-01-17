from django.urls import path
from . import views
from django.contrib.auth.views import password_reset,password_reset_done,password_reset_complete,password_reset_confirm,PasswordResetDoneView
from django.conf.urls import url
from .forms import CustomizedPasswordResetForm, SetNewPasswordForm

app_name = 'accounts'
urlpatterns = [
    url('signup/',views.signup,name='signup'),
    url('login/', views.LoginView, name='login'),
    url('logout/', views.logout_view, name='logout'),
    url('reset_password_done/', password_reset_done, {'template_name':'password_reset_done.html'},name='reset_password_done'),
    url('reset_password/', password_reset, {'template_name':'recover-password.html','password_reset_form':CustomizedPasswordResetForm,'html_email_template_name':'password_reset_email.html','post_reset_redirect':'accounts:reset_password_done'},name='reset_password'),
    url('reset_password_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm, {'template_name':'password_reset_confirm.html','set_password_form':SetNewPasswordForm,'post_reset_redirect':'accounts:password_reset_complete'},name='reset_password_confirm'),
    url('password_reset_complete/', PasswordResetDoneView.as_view(), {'template_name':'password_reset_complete.html'},name='password_reset_complete'),
    url('get_user_list',views.UserList.as_view(),name='get_user_list')
]