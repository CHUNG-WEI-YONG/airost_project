from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .forms import ClubForm,AddMemberForm
from .models import Club , Membership

@login_required
def create_club(request):
    if request.method == "POST":
        form = ClubForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                club = form.save()
                Membership.objects.create(
                    club=club,
                    user=request.user,
                    role=Membership.Role.PRESIDENT,
                )

            return redirect("club_details", club_id=club.id)
    else:
        form = ClubForm()

    return render(request, "clubs/create_club.html", {"form": form})

@login_required
def club_details(request,club_id):
    membership=get_object_or_404(
        Membership.objects.select_related("club"),
        club_id=club_id,
        user=request.user
    )

    members=(Membership.objects.filter(club=membership.club).select_related('user').order_by("user__email"))
    return render(request, "clubs/club_detail.html", {"membership": membership,"members":members})

@login_required
def club_dashboard(request):
    memberships = (
        Membership.objects.filter(user=request.user)
        .select_related("club")
        .order_by("club__name")
    )

    return render(
        request,
        "clubs/club_dashboard.html",
        {"memberships": memberships},
    )

@login_required
def add_member(request,club_id):
    club=get_object_or_404(Club,id=club_id)

    get_object_or_404(Membership,club=club,user=request.user,role=Membership.Role.PRESIDENT)

    form=AddMemberForm(data=request.POST if request.method == "POST" else None,
        club=club,)

    if request.method =='POST' and form.is_valid():
        form.save()
        return redirect("club_details",club_id)

    else:
        return render(request,"clubs/add_member.html",{'form':form,"club":club})

@login_required
def club_expenses(request,club_id):
    membership=get_object_or_404(Membership.objects.select_related("club"),club_id=club_id,user=request.user)
    return render(request,'clubs/expenses.html',{"membership":membership,"club":membership.club})

    



    

# Create your views here.
