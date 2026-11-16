from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("expenses/new/",views.expenses_create,name='expense_create'),
    path("expense/<int:expense_id>/review/",views.review_expense,name="review_expense"),
    path("approval_limit/",views.approval_limit_request,name='approval_limit'),
    path("transactions/",views.transaction_history,name="transaction"),
    path("income/new/", views.record_income, name="record_income"),
    path("expense/<int:expense_id>/cancellation",views.cancel_expense,name="cancel_expense"),
    path("notifications",views.notification_list,name="notifications")
    

]


