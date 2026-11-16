from django.shortcuts import get_object_or_404, render,redirect
from .models import ExpenseRequest,MoneyTransaction,FinanceNotification
from .forms import FinanceRequestForm,SetLimitRequest,IncomeSubmissionForm
from django.contrib.auth.decorators import login_required
from clubs.models import Membership
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q,Sum
from django.core.mail import send_mail
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

            return redirect('finance:dashboard',club_id=club_id)

    else:
        form=FinanceRequestForm()

    reviewers=Membership.objects.filter(
        club=membership.club,
        role__in=[
            Membership.Role.PRESIDENT,
            Membership.Role.TREASURER
        ],
    ).select_related("user")

    for reviewer in reviewers:
        if reviewer.id!=request.user.id:
            FinanceNotification.objects.create(
                recipient=reviewer.user,
                expense_request=expense,
                message=f"New expense request: {expense.title}",
                
            )

            if reviewer.user.email:
                send_mail(
                    subject=f"New finance expenses request for {membership.club.name}"
                    message=(f"{request.user.email} submitted {expense.title} for amount of {expense.amount}"
                             "Please Sign In to Review It"),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_ist=[reviewer.user.email]

                            

                )

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
        and expense.amount>=membership.club.transaction_approval_limit):
        messages.error(request,"This request is above your approval limit and needs the president to review it.",)
        return redirect("finance:dashboard",club_id=club_id)

    expense.status=decision
    expense.reviewed_by=request.user
    expense.reviewed_at=timezone.now()
    expense.reviewed_comment=request.POST.get("reviewed_comment","").strip()

    expense.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "reviewed_comment"
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

    messages.success(
        request, 
        f"Expense request #{expense.id} has been {decision.lower()} successfully."
    )

    decision_text=expense.get_status_display()
    FinanceNotification.objects.create(
        recipient=expense.submitted_by,
        expense_request=expense,
        message=f"Your expense request '{expense.title}' was {decision_text.lower()}.",

    )

    if expense.submitted_by.email:
        send_mail(subject=f"Expense request {decision_text.lower()}: {expense.title}",
            message=(
                    f"Your request for {expense.amount} at {expense.club.name} "
                    f"was {decision_text.lower()}."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[expense.submitted_by.email],
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
                   "total_expense":total_expenses,
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

    notifications=get_object_or_404(
        FinanceNotification.objects.filter(
            recipient=request.user,
            expense_request__club=membership.club
        ).select_related("expense_request")
    )

    return render(request,"finance/notifications.html",
                  {"club":membership.club,"membership":membership,"notifications":notifications})



