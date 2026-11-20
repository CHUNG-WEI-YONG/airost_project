from django.db import models
from django.conf import settings
from clubs.models import Club
from django import forms

# Create your models here.

class ExpenseRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    class Category(models.TextChoices):
        FOOD = "food", "Food"
        TRAVEL = "travel", "Travel"
        EQUIPMENT = "equipment", "Equipment"
        VENUE = "venue", "Venue"
        OTHER = "other", "Other"

    club=models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="expense_requests"
    )

    submitted_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_by"
    )

    title=models.CharField(max_length=50)
    description=models.CharField(max_length=2000)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    submitted_at=models.DateTimeField(auto_now_add=True)
    expenses_at=models.DateField()
    category=models.CharField(max_length=50,choices=Category.choices)

    status=models.CharField(max_length=50,choices=Status.choices,default=Status.PENDING)
    reviewed_by =models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_expenses_request"
                                   )
    reviewed_at=models.DateTimeField(blank=True,null=True)
    reviewed_comment = models.TextField(blank=True)
    receipt = models.FileField(upload_to="receipts/%Y/%m/")

    class Meta:
        ordering=["-submitted_at"]

    def __str__(self):
        return f"{self.title} -{self.club.name}"

class MoneyTransaction(models.Model):
    class Type(models.TextChoices):
        INCOME="income","Money In"
        EXPENSE="expense","money out"

    club=models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="money_transaction"
    )

    expense_request=models.OneToOneField(
        ExpenseRequest,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="money_transaction"
    )

    recorded_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_transaction"
    )

    transaction_type=models.TextField(
        max_length=10,
        choices=Type.choices
    )

    amount=models.DecimalField(
        decimal_places=2,
        max_digits=10
    )

    description=models.CharField(max_length=255)
    transaction_date=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=["-transaction_date","-created_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.amount}"


class FinanceNotification(models.Model):
    recipient=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="finance_notifications"
    )

    expense_request=models.ForeignKey(
        ExpenseRequest,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    message=models.CharField(max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)
    is_read=models.BooleanField(default=False)

    class Meta:
        ordering=["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient}"


class FinanceReport(models.Model):
    club=models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="financial_reports"
    )

    created_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_financial_reports"
    )

    period_start=models.DateField()
    period_end=models.DateField()
    pdf_file=models.FileField(upload_to="financial_report/%y/%m/")
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=["-created_at"]

    def __str__(self):
        return f"{self.club.name} report ({self.period_start} to {self.period_end})"

class ReceiptDraft(models.Model):
    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    club=models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="receipt_drafts"
    )

    uploaded_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_receipt_draft"
    )

    file=models.FileField(upload_to="receipt_drafts/%Y/%m/")
    time_uploaded=models.DateTimeField(auto_now_add=True)

    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    extracted_data = models.JSONField(default=dict, blank=True)
    processing_error = models.TextField(blank=True)

    class Meta:
        ordering=["-time_uploaded"]

    def __str__(self):
        return f"File uploaded by {self.uploaded_by} in {self.club}"

    








