from django.shortcuts import get_object_or_404, render,redirect
from .models import (
    ExpenseRequest,
    MoneyTransaction,
    FinanceNotification,
    FinanceReport,
    ReceiptDraft,
    FinanceChatMessage,
)
from .forms import FinanceRequestForm,SetLimitRequest,IncomeSubmissionForm,ReceiptDraftUploadForm,ReceiptConfirmForm
from django.contrib.auth.decorators import login_required
from clubs.models import Membership
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q,Sum,Count
from django.db import transaction
from django.core.mail import send_mail
from datetime import timedelta
from django.http import HttpResponse,JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile
from django.http import FileResponse,Http404
from .service.ai_service import extract_receipt_details
import logging
from .service.chat_service import answer_finance_question



logger = logging.getLogger(__name__)


# Create your views here.

@login_required
def dashboard(request, club_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )

    finance_requests = (
        ExpenseRequest.objects
        .filter(club=membership.club)
        .select_related("submitted_by", "reviewed_by")
    )
    if membership.role == Membership.Role.MEMBER:
        finance_requests = finance_requests.filter(submitted_by=request.user)

    finance_requests = finance_requests.order_by("-submitted_at")

    return render(
        request,
        "finance/finance_home.html",
        {
            "club": membership.club,
            "membership": membership,
            "finance_requests": finance_requests,
        },
    )

@login_required 
def expenses_create(request,club_id):
    membership=get_object_or_404(Membership.objects.select_related('club'),club_id=club_id,user=request.user)

    if request.method=='POST':
        form=FinanceRequestForm(request.POST,request.FILES)

        if form.is_valid():
            expense=form.save(commit=False)
            expense.club=membership.club
            expense.submitted_by=request.user
            expense.save()

            reviewers=Membership.objects.filter(
                    club=membership.club,
                    role__in=[
                        Membership.Role.PRESIDENT,
                        Membership.Role.TREASURER
                    ],
                ).select_related("user")
            
            for reviewer in reviewers:
                if reviewer.user_id == request.user.id:
                    continue

                FinanceNotification.objects.create(
                    recipient=reviewer.user,
                    expense_request=expense,
                    message=f"New expense request: {expense.title}",
                )

                if reviewer.user.email:
                    try:
                        send_mail(
                            subject=f"New finance expense request for {membership.club.name}",
                            message=(
                                f"{request.user.email} submitted {expense.title} "
                                f"for {expense.amount}. Please sign in to review it."
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[reviewer.user.email],
                        )
                    except Exception:
                        logger.exception(
                            "Could not email reviewer for expense %s", expense.id
                        )
            

            return redirect('finance:dashboard',club_id=club_id)

    else:
        form=FinanceRequestForm()

    return render(request,'finance/expense_form.html',{"form":form,"club":membership.club,"membership":membership})



@login_required
@require_POST
def review_expense(request,club_id,expense_id):
    membership=get_object_or_404(Membership.objects.select_related('club'),club_id=club_id,user=request.user)

    if membership.role!=Membership.Role.PRESIDENT and membership.role!=Membership.Role.TREASURER:
        raise PermissionDenied

    expense=get_object_or_404(ExpenseRequest,id=expense_id,club=membership.club,status=ExpenseRequest.Status.PENDING)

    decision=request.POST.get("decision")

    if decision not in(ExpenseRequest.Status.APPROVED , ExpenseRequest.Status.REJECTED):
        raise PermissionDenied

    if (decision==ExpenseRequest.Status.APPROVED and membership.role==Membership.Role.TREASURER 
        and expense.amount>membership.club.transaction_approval_limit):
        messages.error(request,"This request is above your approval limit and needs the president to review it.",)
        return redirect("finance:dashboard",club_id=club_id)

    with transaction.atomic():
        expense.status = decision
        expense.reviewed_by = request.user
        expense.reviewed_at = timezone.now()
        expense.reviewed_comment = request.POST.get("reviewed_comment", "").strip()
        expense.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "reviewed_comment",
            ]
        )

        if decision == ExpenseRequest.Status.APPROVED:
            MoneyTransaction.objects.get_or_create(
                expense_request=expense,
                defaults={
                    "club": expense.club,
                    "recorded_by": request.user,
                    "transaction_type": MoneyTransaction.Type.EXPENSE,
                    "amount": expense.amount,
                    "description": f"Approved: {expense.title}",
                    "transaction_date": expense.expenses_at,
                },
            )

        FinanceNotification.objects.create(
            recipient=expense.submitted_by,
            expense_request=expense,
            message=f"Your expense request '{expense.title}' was {expense.get_status_display().lower()}.",
        )

        messages.success(
            request, 
            f"Expense request #{expense.id} has been {decision.lower()} successfully."
        )

    decision_text = expense.get_status_display()
    if expense.submitted_by.email:
        try:
            send_mail(
                subject=f"Expense request {decision_text.lower()}: {expense.title}",
                message=(
                    f"Your request for {expense.amount} at {expense.club.name} "
                    f"was {decision_text.lower()}."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[expense.submitted_by.email],
            )
        except Exception:
            logger.exception(
                "Could not email submitter for expense %s", expense.id
            )
            messages.warning(
                request,
                "The review decision was saved, but its email notification could not be sent.",
            )


    return redirect("finance:dashboard",club_id=club_id)

@login_required
def approval_limit_request(request,club_id):
    membership=get_object_or_404(Membership.objects.select_related("club"),club_id=club_id,user=request.user)

    if membership.role != Membership.Role.PRESIDENT:
        raise PermissionDenied

    if request.method=="POST":
        form=SetLimitRequest(request.POST,instance=membership.club)

        if form.is_valid():
            form.save()
            messages.success(request,"changing limit approval success")
            return redirect("finance:dashboard",club_id=club_id)

    else:
        form=SetLimitRequest(instance=membership.club)

    return render(request,'finance/approval_limit_form.html',{"form":form,"club":membership.club,"membership":membership})


@login_required
def transaction_history(request,club_id):
    membership=get_object_or_404(Membership.objects.select_related("club"),club_id=club_id,user=request.user)

    transactions=(MoneyTransaction.objects.filter(club=membership.club).select_related("recorded_by","expense_request"))

    if membership.role == Membership.Role.MEMBER:
        transactions = transactions.filter(
            expense_request__submitted_by=request.user,
            transaction_type=MoneyTransaction.Type.EXPENSE,
        )

    total=transactions.aggregate(
        total_income=Sum("amount",filter=Q(transaction_type=MoneyTransaction.Type.INCOME)),
        total_expense=Sum("amount",filter=Q(transaction_type=MoneyTransaction.Type.EXPENSE))
    )

    total_incomes=total["total_income"] or Decimal("0.00")
    total_expenses=total["total_expense"] or Decimal("0.00")


    return render(request,"finance/transactions.html",
                  {"membership":membership,
                   "transactions":transactions,
                   "club":membership.club,
                   "total_income":total_incomes,
                   "total_out":total_expenses,
                   "balance":total_incomes-total_expenses})

@login_required
def record_income(request, club_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )

    if membership.role != Membership.Role.PRESIDENT:
        raise PermissionDenied

    if request.method == "POST":
        form = IncomeSubmissionForm(request.POST)

        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.club = membership.club
            transaction.recorded_by = request.user
            transaction.transaction_type = MoneyTransaction.Type.INCOME
            transaction.save()

            messages.success(request, "Club funds recorded.")
            return redirect("finance:dashboard", club_id=club_id)
    else:
        form = IncomeSubmissionForm()

    return render(
        request,
        "finance/income_form.html",
        {
            "form": form,
            "club": membership.club,
            "membership": membership,
        },
    )

@login_required
@require_POST
def cancel_expense(request,club_id,expense_id):
    relationship=get_object_or_404(Membership.objects.select_related("club"),
                                   club_id=club_id,
                                   user=request.user)

    expense=get_object_or_404(ExpenseRequest,id=expense_id,club=club_id,submitted_by=request.user,
                              status=ExpenseRequest.Status.PENDING)

    expense.status=ExpenseRequest.Status.CANCELLED
    expense.save(update_fields=["status"])

    return redirect("finance:dashboard",club_id=club_id)


@login_required
def notification_list(request,club_id):
    membership=get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user
    )

    notifications=FinanceNotification.objects.filter(
            recipient=request.user,
            expense_request__club=membership.club
        ).select_related("recipient", "expense_request")

    return render(request,"finance/notifications.html",
                  {"club":membership.club,"membership":membership,"notifications":notifications})


@login_required
def financial_report(request, club_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )

    if membership.role == Membership.Role.MEMBER:
        raise PermissionDenied

    period = request.GET.get("period", "month")
    today = timezone.localdate()

    if period == "day":
        start_date = end_date = today
    elif period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "year":
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        period = "month"
        start_date = today.replace(day=1)
        end_date = today

    transactions = (
        MoneyTransaction.objects
        .filter(
            club=membership.club,
            transaction_date__range=(start_date, end_date),
        )
        .select_related("recorded_by", "expense_request")
    )

    period_totals = transactions.aggregate(
        total_income=Sum(
            "amount",
            filter=Q(transaction_type=MoneyTransaction.Type.INCOME),
        ),
        total_out=Sum(
            "amount",
            filter=Q(transaction_type=MoneyTransaction.Type.EXPENSE),
        ),
    )

    total_income = period_totals["total_income"] or Decimal("0.00")
    total_out = period_totals["total_out"] or Decimal("0.00")

    # Calculate the club's current balance using all its transactions.
    all_totals = MoneyTransaction.objects.filter(
        club=membership.club,
    ).aggregate(
        all_income=Sum(
            "amount",
            filter=Q(transaction_type=MoneyTransaction.Type.INCOME),
        ),
        all_out=Sum(
            "amount",
            filter=Q(transaction_type=MoneyTransaction.Type.EXPENSE),
        ),
    )

    current_balance = (
        (all_totals["all_income"] or Decimal("0.00"))
        - (all_totals["all_out"] or Decimal("0.00"))
    )

    approved_requests = ExpenseRequest.objects.filter(
        club=membership.club,
        status=ExpenseRequest.Status.APPROVED,
        expenses_at__range=(start_date, end_date),
    )

    approved_stats = approved_requests.aggregate(
        count=Count("id"),
        total=Sum("amount"),
    )

    category_summary = list(
        approved_requests
        .values("category")
        .annotate(count=Count("id"), total=Sum("amount"))
        .order_by("-total")
    )

    category_labels = dict(ExpenseRequest.Category.choices)
    for row in category_summary:
        row["category_label"] = category_labels.get(
            row["category"],
            row["category"],
        )

    member_summary = (
        approved_requests
        .values("submitted_by__email")
        .annotate(count=Count("id"), total=Sum("amount"))
        .order_by("-total")
    )

    context = {
        "club": membership.club,
        "membership": membership,
        "transactions": transactions,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_income": total_income,
        "total_out": total_out,
        "period_net": total_income - total_out,
        "balance": current_balance,
        "approved_count": approved_stats["count"] or 0,
        "approved_total": approved_stats["total"] or Decimal("0.00"),
        "category_summary": category_summary,
        "member_summary": member_summary,
    }

    if request.GET.get("format")=="pdf":
        html_content=render_to_string(
            "finance/report_pdf.html",
            context=context,
            request=request,

        )

        pdf_file=HTML(
            string=html_content,
            base_url=request.build_absolute_uri("/"),).write_pdf()

        response=HttpResponse(pdf_file,content_type="application/pdf")

        response["Content-Disposition"] = (
            'inline; filename="club-financial-report.pdf"'
        )

        saved_report=FinanceReport(
            club=membership.club,
            created_by=request.user,
            period_start=start_date,
            period_end=end_date
        )

        filename = f"club-{membership.club.id}-{start_date}-{end_date}.pdf"
        saved_report.pdf_file.save(filename, ContentFile(pdf_file), save=True)
        return response
    return render(request,"finance/report_pdf.html",context)


@login_required
def view_receipt(request,club_id,expense_id):
    membership=get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user
    )

    expense=get_object_or_404(
        ExpenseRequest,
        id=expense_id,
        club=membership.club)

    is_manager= membership.role in [Membership.Role.PRESIDENT , Membership.Role.TREASURER]

    if not is_manager and expense.submitted_by_id!=request.user.id:
        raise PermissionDenied

    if not expense.receipt:
        raise Http404("No receipt for this request")

    return FileResponse(
        expense.receipt.open("rb"),
        as_attachment=True,
        filename=expense.receipt.name.rsplit("/", 1)[-1],
    )

@login_required
def receipt_upload(request,club_id):
    membership=get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user
    )

    if request.method == "POST":
        form = ReceiptDraftUploadForm(request.POST, request.FILES)

        if form.is_valid():
            draft = form.save(commit=False)
            draft.club = membership.club
            draft.uploaded_by = request.user
            draft.save()

            messages.success(request, "Receipt uploaded successfully.")
            return redirect(
                "finance:receipt_review",
                club_id=club_id,
                draft_id=draft.id,
            )
    else:
        form = ReceiptDraftUploadForm()

    return render(
        request,
        "finance/receipt_upload.html",
        {
            "form": form,
            "club": membership.club,
            "membership": membership,
        },
    )

@login_required
def receipt_review(request, club_id, draft_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )
    draft = get_object_or_404(
        ReceiptDraft,
        id=draft_id,
        club=membership.club,
        uploaded_by=request.user,
    )

    return render(
        request,
        "finance/receipt_review.html",
        {
            "club": membership.club,
            "membership": membership,
            "draft": draft,
        },
    )


@login_required
@require_POST
def process_receipt(request, club_id, draft_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )
    draft = get_object_or_404(
        ReceiptDraft,
        id=draft_id,
        club=membership.club,
        uploaded_by=request.user,
    )

    # Prevent reprocessing a draft that already has results.
    if draft.processing_status != ReceiptDraft.ProcessingStatus.COMPLETED:
        try:
            details = extract_receipt_details(draft.file)
            draft.extracted_data = details
            draft.processing_status = ReceiptDraft.ProcessingStatus.COMPLETED
            draft.processing_error = ""
        except Exception:
            logger.exception("Receipt extraction failed for draft %s", draft.id)
            draft.processing_status = ReceiptDraft.ProcessingStatus.FAILED
            draft.processing_error = "We couldn't read this receipt. Please try again."

        draft.save(
            update_fields=[
                "extracted_data",
                "processing_status",
                "processing_error",
            ]
        )

    if draft.processing_status == ReceiptDraft.ProcessingStatus.FAILED:
        messages.error(request, draft.processing_error)
    else:
        messages.success(request, "Receipt details are ready for your review.")

    return redirect(
        "finance:receipt_review",
        club_id=club_id,
        draft_id=draft.id,
    )

@login_required
def confirm_receipt(request, club_id, draft_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )
    draft = get_object_or_404(
        ReceiptDraft,
        id=draft_id,
        club=membership.club,
        uploaded_by=request.user,
    )

    if draft.processing_status != ReceiptDraft.ProcessingStatus.COMPLETED:
        messages.error(request, "Read the receipt before confirming it.")
        return redirect(
            "finance:receipt_review",
            club_id=club_id,
            draft_id=draft.id,
        )

    if draft.expense_request_id:
        messages.info(request, "This receipt has already been submitted.")
        return redirect("finance:dashboard", club_id=club_id)

    if request.method == "POST":
        form = ReceiptConfirmForm(request.POST)

        if form.is_valid():
            reviewers = list(
                Membership.objects
                .filter(
                    club=membership.club,
                    role__in=[
                        Membership.Role.PRESIDENT,
                        Membership.Role.TREASURER,
                    ],
                )
                .select_related("user")
            )

            with transaction.atomic():
                expense = form.save(commit=False)
                expense.club = membership.club
                expense.submitted_by = request.user

                # Reuse the receipt file already uploaded with this draft.
                expense.receipt.name = draft.file.name
                expense.save()

                draft.expense_request = expense
                draft.save(update_fields=["expense_request"])

                for reviewer in reviewers:
                    if reviewer.user_id == request.user.id:
                        continue

                    FinanceNotification.objects.create(
                        recipient=reviewer.user,
                        expense_request=expense,
                        message=f"New expense request: {expense.title}",
                    )

            email_failed = False
            for reviewer in reviewers:
                if reviewer.user_id == request.user.id or not reviewer.user.email:
                    continue

                try:
                    send_mail(
                        subject=f"New finance expense request for {membership.club.name}",
                        message=(
                            f"{request.user.email} submitted {expense.title} "
                            f"for {expense.amount}. Please sign in to review it."
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[reviewer.user.email],
                    )
                except Exception:
                    email_failed = True
                    logger.exception(
                        "Could not email reviewer for expense %s",
                        expense.id,
                    )

            if email_failed:
                messages.warning(
                    request,
                    "Your expense request was submitted, but an email notification could not be sent.",
                )
            else:
                messages.success(request, "Expense request submitted for review.")

            return redirect("finance:dashboard", club_id=club_id)
    else:
        extracted = draft.extracted_data or {}
        form = ReceiptConfirmForm(initial={
            "title": extracted.get("merchant") or "",
            "description": "",
            "amount": extracted.get("total_amount") or "",
            "expenses_at": extracted.get("purchase_date") or "",
            "category": ExpenseRequest.Category.OTHER,
        })

    return render(
        request,
        "finance/receipt_confirm.html",
        {
            "club": membership.club,
            "membership": membership,
            "draft": draft,
            "form": form,
        },
    )

@login_required
@require_POST
def ai_chat(request, club_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )

    question = request.POST.get("question", "").strip()

    if not question:
        return JsonResponse({"error": "Enter a question first."}, status=400)

    if len(question) > 1000:
        return JsonResponse(
            {"error": "Keep your question under 1000 characters."},
            status=400,
        )

    previous_messages = list(
        FinanceChatMessage.objects
        .filter(club=membership.club, user=request.user)
        .order_by("-created_at", "-id")[:10]
    )
    previous_messages.reverse()

    # Keep each member's conversation private to this club and account.
    FinanceChatMessage.objects.create(
        club=membership.club,
        user=request.user,
        role=FinanceChatMessage.Role.USER,
        content=question,
    )

    history = [
        {"role": message.role, "content": message.content}
        for message in previous_messages
    ]

    try:
        result = answer_finance_question(question, membership, history=history)
    except Exception:
        logger.exception("Finance chatbot failed for club %s", club_id)
        FinanceChatMessage.objects.create(
            club=membership.club,
            user=request.user,
            role=FinanceChatMessage.Role.ASSISTANT,
            content="The finance assistant is temporarily unavailable. Please try again.",
        )
        return JsonResponse(
            {"error": "The finance assistant is temporarily unavailable. Please try again."},
            status=503,
        )

    FinanceChatMessage.objects.create(
        club=membership.club,
        user=request.user,
        role=FinanceChatMessage.Role.ASSISTANT,
        content=result["answer"],
    )

    return JsonResponse({
        "question": question,
        **result,
    })

@login_required
def ai_chat_page(request,club_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )

    chat_messages = list(
        FinanceChatMessage.objects
        .filter(club=membership.club, user=request.user)
        .order_by("-created_at", "-id")[:100]
    )
    chat_messages.reverse()

    return render(
        request,
        "finance/ai_chat.html",
        {
            "club": membership.club,
            "membership": membership,
            "chat_messages": chat_messages,
        },
    )




