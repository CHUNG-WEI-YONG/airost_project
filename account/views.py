from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from .forms import SignUpForm


def sign_up(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("signup_success")

    else:
        form = SignUpForm()
    return render(request, "account/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect("club_dashboard")
    else:
        form = AuthenticationForm(request=request)

    return render(request, "account/login.html", {"form": form})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect("login")


def signup_success(request):
    return render(request, "account/signup_success.html")


def home(request):
    if request.user.is_authenticated:
        return redirect("club_dashboard")
    return render(request, "account/home.html")

        


# Create your views here.
