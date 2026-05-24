from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.http import JsonResponse

from accounts.decorators import admin_required
from accounts.models import Login
from households.models import Household
from inventory.models import Category, PantryItem
from waste.models import WasteLog
from complaints.models import Complaint
from feedback.models import Feedback
from .models import IngredientReference


@admin_required
def dashboard(request):
    today = date.today()
    week_ago = today - timedelta(days=30)

    total_households = Household.objects.count()
    active_items = PantryItem.objects.filter(is_consumed=False).count()
    expiring_today = PantryItem.objects.filter(
        is_consumed=False, expiry_date=today
    ).count()
    total_waste = WasteLog.objects.count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    feedback_count = Feedback.objects.count()

    # Items added per month - last 6 months
    items_chart_labels = []
    items_chart_data = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        count = PantryItem.objects.filter(
            created_at__gte=month_start, created_at__lt=next_month
        ).count()
        items_chart_labels.append(month_start.strftime('%b %Y'))
        items_chart_data.append(count)

    # Categories
    cats = Category.objects.annotate(c=Count('pantryitem')).order_by('-c')
    cat_labels = [c.name for c in cats]
    cat_data = [c.c for c in cats]

    # Waste over time
    waste_labels = []
    waste_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i*5)
        end = d + timedelta(days=5)
        s = WasteLog.objects.filter(logged_at__date__gte=d, logged_at__date__lt=end).count()
        waste_labels.append(d.strftime('%d %b'))
        waste_data.append(s)

    # Complaints per month
    comp_labels = items_chart_labels
    comp_data = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        c = Complaint.objects.filter(
            complaint_date__gte=month_start, complaint_date__lt=next_month
        ).count()
        comp_data.append(c)

    total_kg_saved = round(sum(
        [(item.quantity if item.unit == 'kg' else item.quantity / 1000.0 if item.unit == 'g' else item.quantity * 0.25)
         for item in PantryItem.objects.filter(is_consumed=True)]
    ), 2)

    recent_activities = []
    for item in PantryItem.objects.order_by('-created_at')[:5]:
        recent_activities.append({
            'icon': 'bi-box-seam',
            'text': f'{item.item_name} added to {item.household.household_name}',
            'time': item.created_at,
        })

    ctx = {
        'page_title': 'Admin Dashboard',
        'total_households': total_households,
        'active_items': active_items,
        'expiring_today': expiring_today,
        'total_waste': total_waste,
        'pending_complaints': pending_complaints,
        'feedback_count': feedback_count,
        'items_chart_labels': items_chart_labels,
        'items_chart_data': items_chart_data,
        'cat_labels': cat_labels,
        'cat_data': cat_data,
        'waste_labels': waste_labels,
        'waste_data': waste_data,
        'comp_labels': comp_labels,
        'comp_data': comp_data,
        'total_kg_saved': total_kg_saved,
        'recent_activities': recent_activities,
    }
    return render(request, 'admin/dashboard.html', ctx)


# ===== Ingredients =====

@admin_required
def ingredients(request):
    items = IngredientReference.objects.select_related('category').all()
    cats = Category.objects.all()
    return render(request, 'admin/ingredients.html', {
        'page_title': 'Ingredient References',
        'items': items, 'cats': cats,
    })


@admin_required
def ingredient_save(request):
    if request.method == 'POST':
        ref_id = request.POST.get('ref_id')
        try:
            cat = Category.objects.get(id=request.POST.get('category')) if request.POST.get('category') else None
        except Category.DoesNotExist:
            cat = None
        data = {
            'ingredient_name': request.POST.get('ingredient_name', '').strip(),
            'category': cat,
            'default_shelf_life_days': int(request.POST.get('default_shelf_life_days', 7) or 7),
            'storage_type': request.POST.get('storage_type', 'pantry'),
        }
        if ref_id:
            IngredientReference.objects.filter(ref_id=ref_id).update(
                ingredient_name=data['ingredient_name'],
                category=data['category'],
                default_shelf_life_days=data['default_shelf_life_days'],
                storage_type=data['storage_type'],
            )
            messages.success(request, '🌿 Ingredient updated!')
        else:
            IngredientReference.objects.create(**data)
            messages.success(request, '🌿 Ingredient added!')
    return redirect('admin_ingredients')


@admin_required
def ingredient_delete(request, ref_id):
    IngredientReference.objects.filter(ref_id=ref_id).delete()
    messages.success(request, '♻️ Ingredient deleted.')
    return redirect('admin_ingredients')


# ===== Households =====

@admin_required
def households_list(request):
    items = Household.objects.all()
    return render(request, 'admin/households.html', {
        'page_title': 'Households',
        'items': items,
    })


@admin_required
def household_verify(request, household_id):
    h = get_object_or_404(Household, household_id=household_id)
    h.is_verified = True
    h.is_suspended = False
    h.save()
    messages.success(request, f'✅ {h.household_name} verified.')
    return redirect('admin_households')


@admin_required
def household_suspend(request, household_id):
    h = get_object_or_404(Household, household_id=household_id)
    h.is_suspended = True
    h.save()
    messages.warning(request, f'⚠️ {h.household_name} suspended.')
    return redirect('admin_households')


@admin_required
def household_view(request, household_id):
    h = get_object_or_404(Household, household_id=household_id)
    members = h.familymember_set.all()
    try:
        manager = h.kitchenmanager
    except Exception:
        manager = None
    items_count = h.pantryitem_set.filter(is_consumed=False).count()
    waste_count = h.wastelog_set.count()
    return render(request, 'admin/household_view.html', {
        'page_title': h.household_name,
        'h': h,
        'members': members,
        'manager': manager,
        'items_count': items_count,
        'waste_count': waste_count,
    })


# ===== Telemetry =====

@admin_required
def telemetry(request):
    today = date.today()

    total_items = PantryItem.objects.count()
    total_waste_kg = round(sum(
        [(w.quantity if w.unit == 'kg' else w.quantity / 1000.0 if w.unit == 'g' else w.quantity * 0.25)
         for w in WasteLog.objects.all()]
    ), 2)
    total_categories = Category.objects.count()
    daily_active = Login.objects.filter(is_active=True).count()

    # Daily active users (mock by created_at)
    dau_labels = []
    dau_data = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        c = Login.objects.filter(created_at__date__lte=d, is_active=True).count()
        dau_labels.append(d.strftime('%d %b'))
        dau_data.append(c)

    # Items by category
    cats = Category.objects.annotate(c=Count('pantryitem')).order_by('-c')
    cat_labels = [c.name for c in cats]
    cat_data = [c.c for c in cats]

    # Household types
    htypes = Household.HOUSEHOLD_TYPES
    ht_labels = [t[1] for t in htypes]
    ht_data = [Household.objects.filter(household_type=t[0]).count() for t in htypes]

    # Waste trend
    waste_labels = []
    waste_data = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        s = WasteLog.objects.filter(logged_at__date=d).count()
        waste_labels.append(d.strftime('%d %b'))
        waste_data.append(s)

    return render(request, 'admin/telemetry.html', {
        'page_title': 'System Telemetry',
        'total_items': total_items,
        'total_waste_kg': total_waste_kg,
        'total_categories': total_categories,
        'daily_active': daily_active,
        'dau_labels': dau_labels, 'dau_data': dau_data,
        'cat_labels': cat_labels, 'cat_data': cat_data,
        'ht_labels': ht_labels, 'ht_data': ht_data,
        'waste_labels': waste_labels, 'waste_data': waste_data,
    })


# ===== Complaints =====

@admin_required
def complaints_list(request):
    status = request.GET.get('status', 'all')
    qs = Complaint.objects.select_related('user').all()
    if status in ('pending', 'replied'):
        qs = qs.filter(status=status)
    return render(request, 'admin/complaints.html', {
        'page_title': 'Complaints',
        'items': qs, 'status_filter': status,
    })


@admin_required
def complaint_reply(request, complaint_id):
    c = get_object_or_404(Complaint, complaint_id=complaint_id)
    if request.method == 'POST':
        reply = request.POST.get('reply_text', '').strip()
        if reply:
            c.reply_text = reply
            c.status = 'replied'
            c.save()
            messages.success(request, '🌿 Reply sent.')
    return redirect('admin_complaints')


# ===== Feedback =====

@admin_required
def feedback_list(request):
    items = Feedback.objects.select_related('user').all()
    avg_rating = items.count()  # count for now
    emoji_counts = {}
    for f in items:
        emoji_counts[f.emoji_rating] = emoji_counts.get(f.emoji_rating, 0) + 1
    top_emoji = max(emoji_counts, key=emoji_counts.get) if emoji_counts else '🙂'
    return render(request, 'admin/feedback.html', {
        'page_title': 'Platform Feedback',
        'items': items,
        'total_count': items.count(),
        'top_emoji': top_emoji,
    })
