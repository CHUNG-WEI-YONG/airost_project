from django import forms
from .models import ExpenseRequest, MoneyTransaction,ReceiptDraft
from clubs.models import Club
from django.utils import timezone


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

    def clean_expenses_at(self):
        expense_date=self.cleaned_data.get("expenses_at")
        if expense_date and expense_date>timezone.localdate():
            raise forms.ValidationError( "The expense date cannot be in the future. Choose today or an earlier date.")
        return expense_date

    def clean_amount(self):
        amount=self.cleaned_data["amount"]
        if amount<=0:
            raise forms.ValidationError("Wrong , no zero or negative amount allowed")
        return amount

class SetLimitRequest(forms.ModelForm):
    class Meta:
        model=Club
        fields=["transaction_approval_limit"]
        widgets={
            "transaction_approval_limit":forms.NumberInput(
                attrs={"min":0,"step":"0.01"}
            ),
        }

class IncomeSubmissionForm(forms.ModelForm):
    class Meta:
        model=MoneyTransaction
        fields=["amount","description","transaction_date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "transaction_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_amount(self):
            amount=self.cleaned_data["amount"]
            if amount<=0:
                raise forms.ValidationError("Wrong , no zero or negative amount allowed")
            return amount


class ReceiptDraftUploadForm(forms.ModelForm):
    class Meta:
        model=ReceiptDraft
        fields=["file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp"}
        extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

        if f".{extension}" not in allowed_extensions:
            raise forms.ValidationError(
                "Upload a PDF, JPG, PNG, GIF, or WEBP receipt."
            )

        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("The receipt file must be 10 MB or smaller.")

        return uploaded_file

class ReceiptConfirmForm(FinanceRequestForm):
    class Meta(FinanceRequestForm.Meta):
        # The receipt is already stored on ReceiptDraft.
        # The view will attach it to the final ExpenseRequest.
        fields = [
            "title",
            "description",
            "amount",
            "expenses_at",
            "category",
        ]

