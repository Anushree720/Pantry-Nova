"""Inject session user, household, and expiry alert counts into templates."""
from datetime import date, timedelta

from .models import Login


def user_session(request):
    user_id = request.session.get('user_id')
    ctx = {
        'session_user': None,
        'session_user_type': None,
        'session_full_name': None,
        'session_household': None,
        'expiry_alert_count': 0,
        'pending_complaints_count': 0,
    }
    if not user_id:
        return ctx
    try:
        user = Login.objects.get(LOGIN_ID=user_id, is_active=True)
    except Login.DoesNotExist:
        return ctx

    ctx['session_user'] = user
    ctx['session_user_type'] = user.user_type

    household = None
    full_name = user.username

    if user.user_type == 'manager':
        try:
            mgr = user.kitchenmanager
            household = mgr.household
            full_name = mgr.full_name
        except Exception:
            pass
    elif user.user_type == 'member':
        try:
            mem = user.familymember
            household = mem.household
            full_name = mem.full_name
        except Exception:
            pass
    elif user.user_type == 'admin':
        full_name = 'Admin'

    ctx['session_household'] = household
    ctx['session_full_name'] = full_name

    # Expiry counts (for manager/member)
    if household:
        from inventory.models import PantryItem
        today = date.today()
        soon = today + timedelta(days=7)
        ctx['expiry_alert_count'] = PantryItem.objects.filter(
            household=household,
            is_consumed=False,
            expiry_date__lte=soon,
        ).count()

    # Admin pending complaints
    if user.user_type == 'admin':
        from complaints.models import Complaint
        ctx['pending_complaints_count'] = Complaint.objects.filter(status='pending').count()

    return ctx
