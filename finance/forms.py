from django import forms
from .models import ExpenseRequest

class FinanceRequestForm(forms.ModelForm):
    class Meta:
        model=ExpenseRequest
        fields=[
            "title",
            "description",
            "amount",
            "expenses_at",
            "receipt",
            "category"
        ]

        widgets={
            "expenses_at": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }