from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("expenses/new",views.expenses_create,name='expense_create'),
    path("expense/<int:expense_id>/review/",views.review_expense,name="review_expense")

]


