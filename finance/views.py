from django.shortcuts import render,redirect,get_object_or_404
from .models import ExpenseRequest
from django.contrib.auth.decorators import login_required
from clubs.models import Membership

# Create your views here.

@login_required
def dashboard(request,club_id):
    membership = get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user,
    )

    finance_requests=get_object_or_404(ExpenseRequest.objects.select_related('submitted_by','reviewed_by'))
    if membership.role==Membership.Role.MEMBER:
        finance_requests=finance_requests.filter(submitted_by=request.user)

    finance_requests=finance_requests.ordered_by("-submitted_at")

    return render(request,'finance_home.html',{"club":membership.club,"membership":membership,'finance_request':finance_requests})

@login_required
def expenses_list(request):
    return None

    


