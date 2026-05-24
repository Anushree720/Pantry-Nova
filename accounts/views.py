from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse

from .models import Login, PasswordResetOTP
from .forms import ManagerRegisterForm, MemberRegisterForm, LoginForm
from pantrynova.utils import generate_join_code, generate_otp


# ==================== PUBLIC ====================

def landing(request):
    return render(request, 'public/landing.html')


def page_not_found(request, exception=None):
    return render(request, '404.html', status=404)


# ==================== REGISTRATION ====================

def manager_register(request):
    if request.method == 'POST':
        form = ManagerRegisterForm(request.POST)
        if form.is_valid():
            from households.models import Household
            from managers.models import KitchenManager

            with transaction.atomic():
                # Generate unique join code
                code = generate_join_code()
                while Household.objects.filter(join_code=code).exists():
                    code = generate_join_code()

                household = Household.objects.create(
                    household_name=form.cleaned_data['household_name'],
                    household_type=form.cleaned_data['household_type'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                    pin_code=form.cleaned_data['pin_code'],
                    join_code=code,
                    is_verified=False,
                )

                login_obj = Login(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    user_type='manager',
                    user_phone=form.cleaned_data['phone'],
                )
                login_obj.set_password(form.cleaned_data['password'])
                login_obj.save()

                KitchenManager.objects.create(
                    login=login_obj,
                    household=household,
                    full_name=form.cleaned_data['full_name'],
                    phone=form.cleaned_data['phone'],
                )

            messages.success(
                request,
                f'Account created! Your household join code is {code}. Save it to invite family members.'
            )
            return redirect('manager_login')
    else:
        form = ManagerRegisterForm()
    return render(request, 'auth/manager_register.html', {'form': form})


def member_register(request):
    if request.method == 'POST':
        form = MemberRegisterForm(request.POST)
        if form.is_valid():
            from households.models import Household
            from members.models import FamilyMember

            with transaction.atomic():
                household = Household.objects.get(join_code=form.cleaned_data['join_code'])

                login_obj = Login(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    user_type='member',
                    user_phone=form.cleaned_data['phone'],
                )
                login_obj.set_password(form.cleaned_data['password'])
                login_obj.save()

                FamilyMember.objects.create(
                    login=login_obj,
                    household=household,
                    full_name=form.cleaned_data['full_name'],
                    phone=form.cleaned_data['phone'],
                )

            messages.success(request, f'Welcome to {household.household_name}! Please log in.')
            return redirect('member_login')
    else:
        form = MemberRegisterForm()
    return render(request, 'auth/member_register.html', {'form': form})


# ==================== LOGIN ====================

def _do_login(request, expected_type, redirect_url, template):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                user = Login.objects.get(
                    username=form.cleaned_data['username'],
                    user_type=expected_type,
                    is_active=True,
                )
                if user.check_password(form.cleaned_data['password']):
                    request.session['user_id'] = user.LOGIN_ID
                    request.session['user_type'] = user.user_type
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect(redirect_url)
                else:
                    messages.error(request, 'Invalid credentials.')
            except Login.DoesNotExist:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    return render(request, template, {'form': form})


def manager_login(request):
    return _do_login(request, 'manager', 'manager_dashboard', 'auth/manager_login.html')


def member_login(request):
    return _do_login(request, 'member', 'member_dashboard', 'auth/member_login.html')


def admin_login(request):
    return _do_login(request, 'admin', 'admin_dashboard', 'auth/admin_login.html')


def logout_view(request):
    request.session.flush()
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


# ==================== PASSWORD RESET ====================

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = Login.objects.get(email=email, is_active=True)
            otp_code = generate_otp()
            PasswordResetOTP.objects.create(
                user=user,
                otp_code=otp_code,
                expires_at=timezone.now() + timedelta(minutes=10),
            )
            try:
                send_mail(
                    subject='Pantry Nova — Password Reset Code',
                    message=(
                        f'Hi {user.username},\n\n'
                        f'Your Pantry Nova password reset code is: {otp_code}\n'
                        'This code expires in 10 minutes.\n\n'
                        '— The Pantry Nova Team'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
            request.session['reset_email'] = email
            messages.success(request, f'OTP sent to {email}. Check your inbox.')
            return redirect('password_reset_verify')
        except Login.DoesNotExist:
            messages.error(request, 'No account found for this email.')
    return render(request, 'auth/password_reset.html')


def password_reset_verify(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('password_reset')
    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        try:
            user = Login.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(
                user=user, otp_code=otp, is_used=False,
            ).order_by('-created_at').first()
            if otp_obj and otp_obj.expires_at > timezone.now():
                request.session['reset_otp_id'] = otp_obj.id
                return redirect('password_reset_new')
            messages.error(request, 'Invalid or expired OTP.')
        except Login.DoesNotExist:
            messages.error(request, 'Account not found.')
    return render(request, 'auth/password_reset_verify.html', {'email': email})


def password_reset_new(request):
    otp_id = request.session.get('reset_otp_id')
    if not otp_id:
        return redirect('password_reset')
    if request.method == 'POST':
        pw = request.POST.get('password', '')
        cpw = request.POST.get('confirm_password', '')
        if pw != cpw:
            messages.error(request, 'Passwords do not match.')
        elif len(pw) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        else:
            try:
                otp_obj = PasswordResetOTP.objects.get(id=otp_id, is_used=False)
                user = otp_obj.user
                user.set_password(pw)
                user.save()
                otp_obj.is_used = True
                otp_obj.save()
                request.session.pop('reset_email', None)
                request.session.pop('reset_otp_id', None)
                messages.success(request, 'Password updated successfully! Please log in.')
                if user.user_type == 'manager':
                    return redirect('manager_login')
                if user.user_type == 'member':
                    return redirect('member_login')
                return redirect('admin_login')
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, 'Invalid session.')
                return redirect('password_reset')
    return render(request, 'auth/password_reset_new.html')


def password_reset_resend(request):
    email = request.session.get('reset_email')
    if not email:
        return JsonResponse({'success': False, 'message': 'Session expired.'})
    try:
        user = Login.objects.get(email=email)
        otp_code = generate_otp()
        PasswordResetOTP.objects.create(
            user=user,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        try:
            send_mail(
                subject='Pantry Nova — Password Reset Code',
                message=f'Your new code is: {otp_code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass
        return JsonResponse({'success': True, 'message': 'OTP resent successfully.'})
    except Login.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'})
