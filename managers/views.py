from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.http import JsonResponse

from accounts.decorators import manager_required
from inventory.models import PantryItem, Category
from waste.models import WasteLog
from shopping.models import ShoppingList, ShoppingItem
from members.models import FamilyMember
from .models import KitchenManager


def _get_household(request):
    return request.current_user.kitchenmanager.household


def _get_manager(request):
    return request.current_user.kitchenmanager


@manager_required
def dashboard(request):
    h = _get_household(request)
    today = date.today()
    week_end = today + timedelta(days=7)
    month_end = today + timedelta(days=30)

    items = PantryItem.objects.filter(household=h, is_consumed=False)

    total_items = items.count()
    expiring_today = items.filter(expiry_date=today).count()
    expiring_week = items.filter(expiry_date__gt=today, expiry_date__lte=week_end).count()
    out_of_stock = items.filter(quantity__lte=0).count()
    family_count = FamilyMember.objects.filter(household=h).count()
    waste_month = WasteLog.objects.filter(
        household=h, logged_at__date__gte=today.replace(day=1)
    ).count()

    expired_count = items.filter(expiry_date__lt=today).count()
    fresh_count = items.filter(expiry_date__gt=week_end).count()

    cats = Category.objects.annotate(
        c=Count('pantryitem', filter=Q(pantryitem__household=h, pantryitem__is_consumed=False))
    ).order_by('-c')
    cat_labels = [c.name for c in cats if c.c > 0]
    cat_data = [c.c for c in cats if c.c > 0]

    waste_labels = []
    waste_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        c = WasteLog.objects.filter(household=h, logged_at__date=d).count()
        waste_labels.append(d.strftime('%a'))
        waste_data.append(c)

    recent = items.order_by('-created_at')[:5]
    expiring_items = items.filter(expiry_date__lte=week_end).order_by('expiry_date')[:5]

    return render(request, 'manager/dashboard.html', {
        'page_title': 'Dashboard',
        'total_items': total_items,
        'expiring_today': expiring_today,
        'expiring_week': expiring_week,
        'out_of_stock': out_of_stock,
        'family_count': family_count,
        'waste_month': waste_month,
        'expired_count': expired_count,
        'fresh_count': fresh_count,
        'cat_labels': cat_labels,
        'cat_data': cat_data,
        'waste_labels': waste_labels,
        'waste_data': waste_data,
        'recent_items': recent,
        'expiring_items': expiring_items,
    })


# ===== Inventory =====

@manager_required
def inventory_list(request):
    h = _get_household(request)
    qs = PantryItem.objects.filter(household=h, is_consumed=False).select_related('category')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(item_name__icontains=q)
    cat = request.GET.get('category', '')
    if cat:
        qs = qs.filter(category_id=cat)
    status = request.GET.get('status', '')
    today = date.today()
    if status == 'expired':
        qs = qs.filter(expiry_date__lt=today)
    elif status == 'expiring':
        qs = qs.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7))
    elif status == 'fresh':
        qs = qs.filter(expiry_date__gt=today + timedelta(days=7))
    storage = request.GET.get('storage', '')
    if storage:
        qs = qs.filter(storage_location=storage)

    cats = Category.objects.all()

    return render(request, 'manager/inventory.html', {
        'page_title': 'Inventory',
        'items': qs,
        'cats': cats,
        'q': q, 'cat_filter': cat, 'status_filter': status, 'storage_filter': storage,
    })


@manager_required
def inventory_save(request):
    if request.method == 'POST':
        h = _get_household(request)
        item_id = request.POST.get('item_id')
        try:
            cat = Category.objects.get(id=request.POST.get('category')) if request.POST.get('category') else None
        except Category.DoesNotExist:
            cat = None
        data = {
            'household': h,
            'added_by': request.current_user,
            'item_name': request.POST.get('item_name', '').strip(),
            'category': cat,
            'quantity': float(request.POST.get('quantity', 1) or 1),
            'unit': request.POST.get('unit', 'pcs'),
            'purchase_date': request.POST.get('purchase_date') or date.today(),
            'expiry_date': request.POST.get('expiry_date'),
            'storage_location': request.POST.get('storage_location', 'pantry'),
            'barcode': request.POST.get('barcode', ''),
            'notes': request.POST.get('notes', ''),
        }
        if item_id:
            PantryItem.objects.filter(item_id=item_id, household=h).update(
                item_name=data['item_name'],
                category=data['category'],
                quantity=data['quantity'],
                unit=data['unit'],
                purchase_date=data['purchase_date'],
                expiry_date=data['expiry_date'],
                storage_location=data['storage_location'],
                barcode=data['barcode'],
                notes=data['notes'],
            )
            messages.success(request, '🌿 Item updated!')
        else:
            PantryItem.objects.create(**data)
            messages.success(request, '🌿 Item added!')
    return redirect('manager_inventory')


@manager_required
def inventory_delete(request, item_id):
    h = _get_household(request)
    PantryItem.objects.filter(item_id=item_id, household=h).delete()
    messages.success(request, '♻️ Item removed.')
    return redirect('manager_inventory')


@manager_required
def inventory_consume(request, item_id):
    h = _get_household(request)
    item = get_object_or_404(PantryItem, item_id=item_id, household=h)
    item.is_consumed = True
    item.save()
    messages.success(request, f'✅ {item.item_name} marked as consumed.')
    return redirect('manager_inventory')


# ===== Expiry Alerts =====

@manager_required
def expiry_alerts(request):
    h = _get_household(request)
    today = date.today()

    expired = PantryItem.objects.filter(
        household=h, is_consumed=False, expiry_date__lt=today
    )
    expiring_week = PantryItem.objects.filter(
        household=h, is_consumed=False,
        expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7)
    )
    expiring_month = PantryItem.objects.filter(
        household=h, is_consumed=False,
        expiry_date__gt=today + timedelta(days=7),
        expiry_date__lte=today + timedelta(days=30)
    )

    return render(request, 'manager/expiry.html', {
        'page_title': 'Expiry Alerts',
        'expired': expired,
        'expiring_week': expiring_week,
        'expiring_month': expiring_month,
    })


@manager_required
def expiry_log_waste(request, item_id):
    h = _get_household(request)
    item = get_object_or_404(PantryItem, item_id=item_id, household=h)
    WasteLog.objects.create(
        household=h,
        logged_by=request.current_user,
        item_name=item.item_name,
        category=item.category,
        quantity=item.quantity,
        unit=item.unit,
        reason='expired',
        estimated_cost=0,
    )
    item.is_consumed = True
    item.save()
    messages.success(request, '♻️ Waste logged.')
    return redirect('manager_expiry')


# ===== Shopping List =====

@manager_required
def shopping_list(request):
    h = _get_household(request)
    sl, _ = ShoppingList.objects.get_or_create(
        household=h, is_completed=False,
        defaults={'name': 'Active List'}
    )
    items = sl.shoppingitem_set.select_related('category').all()
    cats = Category.objects.all()
    history = ShoppingList.objects.filter(household=h, is_completed=True)[:10]
    return render(request, 'manager/shopping.html', {
        'page_title': 'Shopping List',
        'list_obj': sl, 'items': items, 'cats': cats, 'history': history,
    })


@manager_required
def shopping_add(request):
    if request.method == 'POST':
        h = _get_household(request)
        sl, _ = ShoppingList.objects.get_or_create(
            household=h, is_completed=False,
            defaults={'name': 'Active List'}
        )
        try:
            cat = Category.objects.get(id=request.POST.get('category')) if request.POST.get('category') else None
        except Category.DoesNotExist:
            cat = None
        ShoppingItem.objects.create(
            shopping_list=sl,
            item_name=request.POST.get('item_name', '').strip(),
            quantity=float(request.POST.get('quantity', 1) or 1),
            unit=request.POST.get('unit', 'pcs'),
            category=cat,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, '🌿 Added to shopping list!')
    return redirect('manager_shopping')


@manager_required
def shopping_toggle(request, item_id):
    h = _get_household(request)
    item = get_object_or_404(ShoppingItem, item_id=item_id, shopping_list__household=h)
    item.is_purchased = not item.is_purchased
    item.save()
    return JsonResponse({'success': True, 'purchased': item.is_purchased})


@manager_required
def shopping_delete(request, item_id):
    h = _get_household(request)
    ShoppingItem.objects.filter(item_id=item_id, shopping_list__household=h).delete()
    return redirect('manager_shopping')


@manager_required
def shopping_complete(request, list_id):
    h = _get_household(request)
    sl = get_object_or_404(ShoppingList, list_id=list_id, household=h)
    sl.is_completed = True
    sl.save()
    messages.success(request, '✅ Shopping list completed!')
    return redirect('manager_shopping')


# ===== Waste Log =====

@manager_required
def waste_log(request):
    h = _get_household(request)
    items = WasteLog.objects.filter(household=h).select_related('category')
    cats = Category.objects.all()

    today = date.today()
    month_start = today.replace(day=1)

    month_items = items.filter(logged_at__date__gte=month_start)
    total_month = month_items.count()
    total_cost = sum(w.estimated_cost for w in month_items)
    total_co2 = sum(w.co2_equivalent for w in month_items)

    # Pie: waste by category
    by_cat = {}
    for w in items:
        cn = w.category.name if w.category else 'Other'
        by_cat[cn] = by_cat.get(cn, 0) + 1
    cat_labels = list(by_cat.keys())
    cat_data = list(by_cat.values())

    # Bar: waste by week (last 8 weeks)
    week_labels = []
    week_data = []
    for i in range(7, -1, -1):
        wstart = today - timedelta(days=today.weekday() + 7*i)
        wend = wstart + timedelta(days=7)
        c = items.filter(logged_at__date__gte=wstart, logged_at__date__lt=wend).count()
        week_labels.append(wstart.strftime('%d %b'))
        week_data.append(c)

    # Cost line: last 6 months
    cost_labels = []
    cost_data = []
    for i in range(5, -1, -1):
        mstart = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        mend = (mstart + timedelta(days=32)).replace(day=1)
        s = sum(w.estimated_cost for w in items.filter(
            logged_at__date__gte=mstart, logged_at__date__lt=mend
        ))
        cost_labels.append(mstart.strftime('%b'))
        cost_data.append(round(s, 2))

    tips = [
        '🌿 Plan your meals weekly — check inventory before shopping.',
        '♻️ Store leafy greens in airtight containers with paper towels.',
        '🌱 Freeze ripe fruits for smoothies before they go bad.',
        '🥬 Use the "First In, First Out" rule for fridge stocking.',
        '🍽️ Cook smaller portions — smaller waste, smaller impact.',
    ]

    return render(request, 'manager/waste.html', {
        'page_title': 'Waste Log',
        'items': items, 'cats': cats,
        'total_month': total_month,
        'total_cost': round(total_cost, 2),
        'total_co2': round(total_co2, 2),
        'cat_labels': cat_labels, 'cat_data': cat_data,
        'week_labels': week_labels, 'week_data': week_data,
        'cost_labels': cost_labels, 'cost_data': cost_data,
        'tips': tips,
    })


@manager_required
def waste_save(request):
    if request.method == 'POST':
        h = _get_household(request)
        try:
            cat = Category.objects.get(id=request.POST.get('category')) if request.POST.get('category') else None
        except Category.DoesNotExist:
            cat = None
        WasteLog.objects.create(
            household=h,
            logged_by=request.current_user,
            item_name=request.POST.get('item_name', '').strip(),
            category=cat,
            quantity=float(request.POST.get('quantity', 0) or 0),
            unit=request.POST.get('unit', 'kg'),
            reason=request.POST.get('reason', 'expired'),
            estimated_cost=float(request.POST.get('estimated_cost', 0) or 0),
        )
        messages.success(request, '♻️ Waste logged.')
    return redirect('manager_waste')


@manager_required
def waste_delete(request, waste_id):
    h = _get_household(request)
    WasteLog.objects.filter(waste_id=waste_id, household=h).delete()
    messages.success(request, '🌿 Entry removed.')
    return redirect('manager_waste')


# ===== Analytics =====

@manager_required
def analytics(request):
    h = _get_household(request)
    today = date.today()

    waste_items = WasteLog.objects.filter(household=h)
    pantry_items = PantryItem.objects.filter(household=h)

    total_saved = sum(w.estimated_cost for w in waste_items)
    food_saved_kg = round(sum(
        [(item.quantity if item.unit == 'kg' else item.quantity / 1000.0 if item.unit == 'g' else item.quantity * 0.25)
         for item in pantry_items.filter(is_consumed=True)]
    ), 2)
    co2_reduced = round(food_saved_kg * 2.5, 2)
    waste_reduction = 30  # mock %

    by_cat = {}
    for w in waste_items:
        cn = w.category.name if w.category else 'Other'
        by_cat[cn] = by_cat.get(cn, 0) + 1
    cat_labels = list(by_cat.keys())
    cat_data = list(by_cat.values())

    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        mstart = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        mend = (mstart + timedelta(days=32)).replace(day=1)
        c = pantry_items.filter(created_at__gte=mstart, created_at__lt=mend).count()
        monthly_labels.append(mstart.strftime('%b'))
        monthly_data.append(c)

    consumed_labels = ['Added', 'Consumed', 'Wasted']
    consumed_data = [
        pantry_items.count(),
        pantry_items.filter(is_consumed=True).count(),
        waste_items.count(),
    ]

    cost_labels = []
    cost_data = []
    for i in range(5, -1, -1):
        mstart = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        mend = (mstart + timedelta(days=32)).replace(day=1)
        s = sum(w.estimated_cost for w in waste_items.filter(
            logged_at__date__gte=mstart, logged_at__date__lt=mend
        ))
        cost_labels.append(mstart.strftime('%b'))
        cost_data.append(round(s, 2))

    return render(request, 'manager/analytics.html', {
        'page_title': 'Analytics & Reports',
        'total_saved': round(total_saved, 2),
        'food_saved_kg': food_saved_kg,
        'co2_reduced': co2_reduced,
        'waste_reduction': waste_reduction,
        'cat_labels': cat_labels, 'cat_data': cat_data,
        'monthly_labels': monthly_labels, 'monthly_data': monthly_data,
        'consumed_labels': consumed_labels, 'consumed_data': consumed_data,
        'cost_labels': cost_labels, 'cost_data': cost_data,
    })


# ===== Family Members =====

@manager_required
def family_members(request):
    h = _get_household(request)
    members = FamilyMember.objects.filter(household=h).select_related('login')
    return render(request, 'manager/family.html', {
        'page_title': 'Family Members',
        'members': members,
        'household': h,
    })


@manager_required
def family_remove(request, member_id):
    h = _get_household(request)
    m = get_object_or_404(FamilyMember, member_id=member_id, household=h)
    m.login.delete()  # cascade
    messages.success(request, f'♻️ {m.full_name} removed.')
    return redirect('manager_family')


# ===== Profile =====

@manager_required
def profile(request):
    mgr = _get_manager(request)
    h = mgr.household
    if request.method == 'POST':
        mgr.full_name = request.POST.get('full_name', mgr.full_name)
        mgr.phone = request.POST.get('phone', mgr.phone)
        mgr.save()
        mgr.login.email = request.POST.get('email', mgr.login.email)
        mgr.login.user_phone = mgr.phone
        mgr.login.save()
        h.household_name = request.POST.get('household_name', h.household_name)
        h.address = request.POST.get('address', h.address)
        h.city = request.POST.get('city', h.city)
        h.pin_code = request.POST.get('pin_code', h.pin_code)
        h.save()
        messages.success(request, '🌿 Profile updated!')
        return redirect('manager_profile')
    return render(request, 'manager/profile.html', {
        'page_title': 'Profile',
        'mgr': mgr, 'household': h,
    })
