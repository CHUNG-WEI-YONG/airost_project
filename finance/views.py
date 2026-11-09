from django.shortcuts import get_object_or_404, render,redirect
from .models import ExpenseRequest
from .forms import FinanceRequestForm
from django.contrib.auth.decorators import login_required
from clubs.models import Membership

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.decorators.http import require_POST

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

    messages.success(
        request, 
        f"Expense request #{expense.id} has been {decision.lower()} successfully."
    )

    return redirect("finance:dashboard",club_id=club_id)



