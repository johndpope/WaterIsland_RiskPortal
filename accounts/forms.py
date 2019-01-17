from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm,SetPasswordForm
from .models import User

class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=30, required=True,widget=forms.TextInput(attrs={'class': 'form-control input-lg', 'placeholder': 'Create a UserName','required':'required'}))
    first_name = forms.CharField(max_length=30, required=True,widget=forms.TextInput(attrs={'class':'form-control input-lg','placeholder':'First Name','required':'required'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class':'form-control input-lg','placeholder':'Last Name','required':'required'}))
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.',widget=forms.EmailInput(attrs={'class':'form-control input-lg','placeholder':'Email','required':'required'}))
    phone_number = forms.CharField(max_length=10, help_text='Required. Inform a valid phone number.',widget=forms.TextInput(attrs={'class': 'form-control input-lg', 'placeholder': 'Phone Number','required':'required'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control input-lg','placeholder':'Password','required':'required'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control input-lg', 'placeholder': 'Retype Password','required':'required'}))

    class Meta:
        model = User
        fields = ('username','first_name', 'last_name', 'email','phone_number','password1','password2')

class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=30, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control input-lg', 'placeholder': 'Enter you username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control input-lg','placeholder':'Password'}))

    class Meta:
        model = User
        fields = ('username','password')

class CustomizedPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.',widget=forms.EmailInput(attrs={'class':'form-control form-control-lg input-lg','placeholder':'Your Email Address','required':'true'}))

class SetNewPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control input-lg','placeholder':'Type New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control input-lg', 'placeholder': 'Retype your New Password'}))