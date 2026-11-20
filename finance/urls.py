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
    path("notifications",views.notification_list,name="notifications"),
    path("reports/",views.financial_report,name="financial_report"),
    path("expense/<int:expense_id>/receipt/",views.view_receipt,name="view_receipt"),
    path("receipts/upload/",views.receipt_upload,name="receipt_upload"),
    path(
        "receipts/<int:draft_id>/review/",
        views.receipt_review,
        name="receipt_review",
    ),
    path(
        "receipts/<int:draft_id>/process/",
        views.process_receipt,
        name="process_receipt",
    ),
    
    

]


