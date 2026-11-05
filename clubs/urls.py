from django.urls import path,include
from . import views

urlpatterns = [
    path('new/',views.create_club,name="create_club"),
    path("<int:club_id>/",views.club_details,name="club_details"),
    path('',views.club_dashboard,name="club_dashboard"),
    path('<int:club_id>/members/add/',views.add_member,name="add_member"),
    path('<int:club_id>/expenses',views.club_expenses,name="club_expenses"),
    path('<int:club_id>/finance/',include(("finance.urls",'finance'),namespace="finance"))
]
