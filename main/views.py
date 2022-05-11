from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
            for _, error in form._errors.items():
                messages.error(request, error)
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
                for field_name, _ in form.errors.items():
                    form.fields[field_name].widget.attrs["class"] += " is-invalid"
        else:
            for field_name, _ in form.errors.items():
                form.fields[field_name].widget.attrs["class"] += " is-invalid"

    return render(request, "home/login.html", {'form': form})


def logout_request(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("/login")


@login_required(login_url='/login')
def account(request):
    curr_user = request.user
    # print(dir(curr_user))
    # print(request.user.get_group_permissions())
    # print('scheduling.view_schedule' in request.user.get_group_permissions())
    # print(request.user.has_perm('scheduling.view_schedule'))
    context = {"curr_user": curr_user}

    return render(request, 'home/account.html', context)
