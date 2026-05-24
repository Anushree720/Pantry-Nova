from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q

from accounts.decorators import member_required
from inventory.models import PantryItem, Category
from waste.models import WasteLog
from shopping.models import ShoppingList, ShoppingItem
from complaints.models import Complaint
from feedback.models import Feedback


def _get_member(request):
    return request.current_user.familymember


def _get_household(request):
    return _get_member(request).household


@member_required
def dashboard(request):
    h = _get_household(request)
    today = date.today()
    week_end = today + timedelta(days=7)

    items = PantryItem.objects.filter(household=h, is_consumed=False)
    items_available = items.count()
    expiring_soon = items.filter(expiry_date__lte=week_end).count()

    # My consumption this week (proxy: items I marked consumed this week)
    week_start = today - timedelta(days=today.weekday())
    my_consumption = PantryItem.objects.filter(
        household=h, added_by=request.current_user, is_consumed=True,
        created_at__date__gte=week_start
    ).count()

    alerts_pending = items.filter(expiry_date__lt=today).count()

    cats = Category.objects.annotate(
        c=Count('pantryitem', filter=Q(pantryitem__household=h, pantryitem__is_consumed=False))
    ).order_by('-c')

    recent_alerts = items.filter(expiry_date__lte=week_end).order_by('expiry_date')[:5]

    return render(request, 'member/dashboard.html', {
        'page_title': 'Dashboard',
        'items_available': items_available,
        'expiring_soon': expiring_soon,
        'my_consumption': my_consumption,
        'alerts_pending': alerts_pending,
        'cats': cats,
        'recent_alerts': recent_alerts,
    })


# ===== Stock =====

@member_required
def stock(request):
    h = _get_household(request)
    qs = PantryItem.objects.filter(household=h, is_consumed=False).select_related('category').order_by('expiry_date')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(item_name__icontains=q)
    cat = request.GET.get('category', '')
    if cat:
        qs = qs.filter(category_id=cat)
    storage = request.GET.get('storage', '')
    if storage:
        qs = qs.filter(storage_location=storage)

    cats = Category.objects.all()
    return render(request, 'member/stock.html', {
        'page_title': 'Kitchen Stock',
        'items': qs, 'cats': cats,
        'q': q, 'cat_filter': cat, 'storage_filter': storage,
    })


# ===== Log Consumption =====

@member_required
def consumption(request):
    h = _get_household(request)
    items = PantryItem.objects.filter(household=h, is_consumed=False)
    history = PantryItem.objects.filter(
        household=h, added_by=request.current_user, is_consumed=True
    ).order_by('-created_at')[:30]
    frequent = PantryItem.objects.filter(household=h).values('item_name').annotate(
        c=Count('item_id')
    ).order_by('-c')[:5]
    return render(request, 'member/consumption.html', {
        'page_title': 'Log Consumption',
        'items': items, 'history': history, 'frequent': frequent,
    })


@member_required
def consumption_log(request):
    if request.method == 'POST':
        h = _get_household(request)
        item_id = request.POST.get('item_id')
        qty_used = float(request.POST.get('quantity', 0) or 0)
        try:
            item = PantryItem.objects.get(item_id=item_id, household=h)
            if qty_used >= item.quantity:
                item.is_consumed = True
                item.quantity = 0
            else:
                item.quantity -= qty_used
            item.notes = (item.notes or '') + f"\nConsumed {qty_used}{item.unit} by {request.current_user.username} on {date.today()}"
            item.save()
            messages.success(request, f'✅ Logged consumption of {item.item_name}')
        except PantryItem.DoesNotExist:
            messages.error(request, 'Item not found.')
    return redirect('member_consumption')


# ===== Alerts =====

@member_required
def alerts(request):
    h = _get_household(request)
    today = date.today()
    items = PantryItem.objects.filter(household=h, is_consumed=False)
    critical = items.filter(expiry_date__lt=today)
    warning = items.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7))
    info = items.filter(expiry_date__gt=today + timedelta(days=7), expiry_date__lte=today + timedelta(days=30))
    return render(request, 'member/alerts.html', {
        'page_title': 'Alerts',
        'critical': critical, 'warning': warning, 'info': info,
    })


# ===== Shopping View =====

@member_required
def shopping(request):
    h = _get_household(request)
    sl = ShoppingList.objects.filter(household=h, is_completed=False).first()
    items_grouped = {}
    if sl:
        for item in sl.shoppingitem_set.select_related('category').all():
            cn = item.category.name if item.category else 'Uncategorized'
            items_grouped.setdefault(cn, []).append(item)
    return render(request, 'member/shopping.html', {
        'page_title': 'Shopping List',
        'list_obj': sl, 'items_grouped': items_grouped,
    })


# ===== Complaints =====

@member_required
def complaints(request):
    items = Complaint.objects.filter(user=request.current_user)
    if request.method == 'POST':
        text = request.POST.get('complaint_text', '').strip()
        if text:
            Complaint.objects.create(user=request.current_user, complaint_text=text)
            messages.success(request, '🌿 Complaint submitted!')
            return redirect('member_complaints')
    return render(request, 'member/complaints.html', {
        'page_title': 'Complaints',
        'items': items,
    })


# ===== Feedback =====

@member_required
def feedback(request):
    items = Feedback.objects.filter(user=request.current_user)
    if request.method == 'POST':
        text = request.POST.get('feedback_text', '').strip()
        emoji = request.POST.get('emoji_rating', '🙂')
        if text:
            Feedback.objects.create(
                user=request.current_user, feedback_text=text, emoji_rating=emoji
            )
            messages.success(request, '🌿 Thank you for your feedback!')
            return redirect('member_feedback')
    return render(request, 'member/feedback.html', {
        'page_title': 'Feedback',
        'items': items,
    })


# ===== Profile =====

@member_required
def profile(request):
    mem = _get_member(request)
    h = mem.household
    if request.method == 'POST':
        mem.full_name = request.POST.get('full_name', mem.full_name)
        mem.phone = request.POST.get('phone', mem.phone)
        mem.save()
        mem.login.email = request.POST.get('email', mem.login.email)
        mem.login.user_phone = mem.phone
        mem.login.save()
        messages.success(request, '🌿 Profile updated!')
        return redirect('member_profile')
    return render(request, 'member/profile.html', {
        'page_title': 'Profile',
        'mem': mem, 'household': h,
    })
