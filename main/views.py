from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm  # ,UserCreationForm
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect


from .forms import NewUserForm, LoginForm


def home(request):
    return render(request, 'home/home.html')


def signup(request):

    form = NewUserForm()

    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():

            user = form.save()
            username = form.cleaned_data['email'].replace('@grayson.edu', '')
            messages.success(request, f"New account created for {username}.")
            login(request, user)
            return redirect("/")
        else:
            for code, error in form._errors.items():
                messages.error(request, error)
                # if code in ('email', 'password', 'duplicate'):
                #     messages.error(request, error)
            return render(request, 'home/signup.html', {'form': form})

    return render(request, 'home/signup.html', {'form': form})


def login_request(request):

    form = LoginForm()

    if request.method == "POST":
        form = LoginForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(
                    request, f"You are now logged in as {username}")
                next_url = request.GET.get('next')
                if next_url:
                    return HttpResponseRedirect(next_url)
                return redirect('/')
            else:
                messages.error(request, "Invalid username or passord.")
        else:
            messages.error(request, "Invalid username or passord.")

    return render(request, "home/login.html", {'form': form})


def logout_request(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("/login")


@login_required(login_url='/login')
def account(request):
    curr_user = request.user

    return render(request, 'home/profile.html')
