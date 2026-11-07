from django.urls import path 
from . import views

app_name="finance"
urlpatterns = [
    path("",views.dashboard,name="dashboard"),
    path("expenses/",views.expenses_list,name="expenses_list")
]
