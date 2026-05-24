"""Custom session-based role decorators."""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

from .models import Login


def _get_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return Login.objects.get(LOGIN_ID=user_id, is_active=True)
    except Login.DoesNotExist:
        return None


def login_required_session(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_user(request)
        if not user:
            messages.warning(request, 'Please log in to continue.')
            return redirect('manager_login')
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_user(request)
        if not user or user.user_type != 'admin':
            messages.warning(request, 'Admin access required.')
            return redirect('admin_login')
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_user(request)
        if not user or user.user_type != 'manager':
            messages.warning(request, 'Kitchen Manager access required.')
            return redirect('manager_login')
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def member_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_user(request)
        if not user or user.user_type != 'member':
            messages.warning(request, 'Family Member access required.')
            return redirect('member_login')
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def household_member_required(view_func):
    """Allows manager OR member."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_user(request)
        if not user or user.user_type not in ('manager', 'member'):
            messages.warning(request, 'Login required.')
            return redirect('manager_login')
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper
