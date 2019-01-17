# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.views import login,logout
from django.contrib.auth import authenticate
from .forms import SignUpForm,LoginForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import User
from django.views.generic import ListView


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('../login')

    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def LoginView(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.add_message(request,messages.ERROR, 'Invalid Username/Password Combination')
            #redirect('login')

    else:
        form = LoginForm()
    return render(request,'login.html',{'form':form})

@login_required
def logout_view(request):
    #Logout and Redirect
    messages.add_message(request,messages.SUCCESS,'You have successfully logged out. Thank You')
    logout(request)
    return redirect('login')

def password_reset(request):
    return render(request, 'recover-password.html')

class UserList(LoginRequiredMixin, ListView):
    model = User
    template_name = 'user_list.html'
