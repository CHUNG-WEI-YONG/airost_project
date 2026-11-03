from django.shortcuts import render,redirect
from django.contrib.auth import login , logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from .forms import SignUpForm

def signup(request):
    if request.method=="POST":
        form=SignUpForm(request.POST)

        if form.is_valid():
            user=form.save()
            login(request ,user)
            return redirect("signup_success")

    else:
        form=SignUpForm()
    return render(request,"signup.html",{"form":form})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)

        if form.is_valid():
            user=form.save()
            login(request,user)
            return redirect("signup_success")
        else:
            form=AuthenticationForm(request=request)

        return render(request,'login.html',{'form':form})

def logout(request):
    logout(request)
    return redirect("login")
    

def signup_success(request):
    return render(request,"signup_success.html")


        


# Create your views here.
