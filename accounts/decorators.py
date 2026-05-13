from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def member_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not getattr(request, "current_member", None):
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapped


def admin_member_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        member = getattr(request, "current_member", None)
        if not member:
            return redirect("login")
        if not member.is_admin:
            messages.error(request, "只有管理员可以访问该页面。")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped
