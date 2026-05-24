import re
import secrets
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect

from accounts.decorators import manager_required
from .models import Plan, Subscription, Payment


# ===== Public pricing page =====

def pricing(request):
    plans = Plan.objects.filter(is_active=True).order_by('sort_order')
    cycle = request.GET.get('cycle', 'monthly')
    return render(request, 'public/pricing.html', {
        'plans': plans, 'cycle': cycle,
    })


# ===== Manager: Billing dashboard =====

def _get_household(request):
    return request.current_user.kitchenmanager.household


def _ensure_subscription(household):
    sub = getattr(household, 'subscription', None)
    if sub:
        return sub
    free_plan = Plan.objects.filter(slug='free').first()
    if not free_plan:
        free_plan = Plan.objects.create(
            name='Free', slug='free',
            tagline='Get started with the basics',
            price_monthly=0, price_yearly=0,
            max_items=50, max_members=1,
            sort_order=1,
        )
    return Subscription.objects.create(
        household=household, plan=free_plan, status='active',
    )


@manager_required
def billing(request):
    h = _get_household(request)
    sub = _ensure_subscription(h)
    payments = Payment.objects.filter(subscription=sub)
    plans = Plan.objects.filter(is_active=True).order_by('sort_order')

    total_paid = sum(p.amount for p in payments.filter(status='success'))

    return render(request, 'manager/billing.html', {
        'page_title': 'Billing & Plans',
        'sub': sub, 'payments': payments, 'plans': plans,
        'total_paid': total_paid,
    })


# ===== Manager: Checkout (demo) =====

@manager_required
def checkout(request, slug):
    h = _get_household(request)
    sub = _ensure_subscription(h)
    plan = get_object_or_404(Plan, slug=slug, is_active=True)

    if plan.is_free:
        # Downgrade to free immediately, no payment
        sub.plan = plan
        sub.status = 'active'
        sub.billing_cycle = 'monthly'
        sub.expires_at = None
        sub.save()
        messages.success(request, '🌿 Switched to the Free plan.')
        return redirect('manager_billing')

    cycle = request.GET.get('cycle', 'monthly')
    if cycle not in ('monthly', 'yearly'):
        cycle = 'monthly'
    amount = plan.price_yearly if cycle == 'yearly' else plan.price_monthly

    return render(request, 'manager/checkout.html', {
        'page_title': f'Upgrade to {plan.name}',
        'plan': plan, 'sub': sub,
        'cycle': cycle, 'amount': amount,
    })


@manager_required
@csrf_protect
def process_payment(request, slug):
    """Demo payment processor. Validates fake card/UPI input and records a Payment."""
    if request.method != 'POST':
        return redirect('subs_checkout', slug=slug)

    h = _get_household(request)
    sub = _ensure_subscription(h)
    plan = get_object_or_404(Plan, slug=slug, is_active=True)

    cycle = request.POST.get('cycle', 'monthly')
    if cycle not in ('monthly', 'yearly'):
        cycle = 'monthly'
    amount = plan.price_yearly if cycle == 'yearly' else plan.price_monthly

    method = request.POST.get('method', 'card')
    masked = ''
    error = None

    # Validate fake input
    if method == 'card':
        card = re.sub(r'\s+', '', request.POST.get('card_number', ''))
        cvv = request.POST.get('cvv', '').strip()
        expiry = request.POST.get('expiry', '').strip()
        if not (card.isdigit() and 13 <= len(card) <= 19):
            error = 'Invalid card number. Use 13-19 digits (any digits work in demo).'
        elif not (cvv.isdigit() and 3 <= len(cvv) <= 4):
            error = 'Invalid CVV. Must be 3-4 digits.'
        elif not re.match(r'^\d{2}/\d{2}$', expiry):
            error = 'Invalid expiry. Use MM/YY format.'
        else:
            masked = '**** **** **** ' + card[-4:]
    elif method == 'upi':
        upi = request.POST.get('upi_id', '').strip()
        if not re.match(r'^[\w.\-]+@[\w]+$', upi):
            error = 'Invalid UPI ID. Use format like username@bank.'
        else:
            masked = upi
    elif method == 'netbanking':
        bank = request.POST.get('bank', '').strip()
        if not bank:
            error = 'Please select a bank.'
        else:
            masked = bank
    elif method == 'wallet':
        wallet = request.POST.get('wallet', '').strip()
        if not wallet:
            error = 'Please select a wallet.'
        else:
            masked = wallet

    if error:
        messages.error(request, error)
        return redirect(f'/manager/billing/checkout/{slug}/?cycle={cycle}')

    # Generate fake transaction id
    txn = 'PN' + secrets.token_hex(10).upper()

    # Record successful payment + activate subscription
    sub.plan = plan
    sub.status = 'active'
    sub.billing_cycle = cycle
    sub.renew(billing_cycle=cycle)

    payment = Payment.objects.create(
        subscription=sub,
        plan=plan,
        amount=amount,
        currency='INR',
        billing_cycle=cycle,
        method=method,
        status='success',
        transaction_id=txn,
        masked_account=masked,
    )

    return redirect('subs_success', payment_id=payment.payment_id)


@manager_required
def payment_success(request, payment_id):
    h = _get_household(request)
    payment = get_object_or_404(
        Payment, payment_id=payment_id, subscription__household=h
    )
    return render(request, 'manager/payment_success.html', {
        'page_title': 'Payment Successful',
        'payment': payment, 'sub': payment.subscription,
    })


@manager_required
def cancel_subscription(request):
    h = _get_household(request)
    sub = _ensure_subscription(h)
    if request.method == 'POST':
        sub.auto_renew = False
        sub.cancelled_at = timezone.now()
        sub.status = 'cancelled' if not sub.expires_at else 'active'
        sub.save()
        messages.warning(request, '⚠️ Auto-renewal cancelled. Your plan stays active until the period ends.')
    return redirect('manager_billing')


@manager_required
def invoice(request, payment_id):
    h = _get_household(request)
    payment = get_object_or_404(
        Payment, payment_id=payment_id, subscription__household=h
    )
    return render(request, 'manager/invoice.html', {
        'page_title': f'Invoice {payment.transaction_id}',
        'payment': payment, 'sub': payment.subscription, 'household': h,
    })
