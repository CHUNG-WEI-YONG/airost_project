from django.db import models
from django.conf import settings
from clubs.models import Club

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