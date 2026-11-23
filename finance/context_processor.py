from clubs.models import Membership
from .models import FinanceNotification

def finance_sidebar(request):
    if not request.user.is_authenticated:
        return {}

    match=getattr(request,"resolver_match",None)
    club_id=match.kwargs.get("club_id") if match else None

    if club_id is None:
        return {}

    is_member=Membership.objects.filter(user=request.user,club_id=club_id).exists()

    if not is_member:
        return {}

    unread_count=FinanceNotification.objects.filter(recipient=request.user,expense_request__club_id=club_id,is_read=False).count()
    return {"unread_notification_count":unread_count}

