from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .activity import log_activity
from .decorators import admin_member_required
from .forms import MemberForm, MemberLoginForm
from .models import ActivityLog, Member


def login_view(request):
    if getattr(request, "current_member", None):
        return redirect("dashboard")
    form = MemberLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        member = form.cleaned_data["member"]
        request.session["member_id"] = member.id
        log_activity(request, ActivityLog.Action.LOGIN, target=member, actor=member)
        messages.success(request, f"欢迎回来，{member.name}。")
        return redirect("dashboard")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if getattr(request, "current_member", None):
        log_activity(
            request,
            ActivityLog.Action.LOGOUT,
            target=request.current_member,
            actor=request.current_member,
        )
    request.session.flush()
    return redirect("login")


@admin_member_required
def manage_members(request):
    editing = None
    if request.GET.get("edit"):
        editing = get_object_or_404(Member, pk=request.GET["edit"])

    form = MemberForm(request.POST or None, instance=editing)
    if request.method == "POST" and form.is_valid():
        if not editing and not form.cleaned_data.get("pin"):
            form.add_error("pin", "新增成员必须设置口令。")
        else:
            member = form.save()
            log_activity(
                request,
                ActivityLog.Action.MEMBER_SAVE,
                target=member,
                summary=f"保存成员：{member.name}",
                metadata={
                    "is_admin": member.is_admin,
                    "is_active": member.is_active,
                    "mode": "edit" if editing else "create",
                },
            )
            messages.success(request, "成员已保存。")
            return redirect("manage_members")

    return render(
        request,
        "manage/members.html",
        {
            "form": form,
            "members": Member.objects.all(),
            "editing": editing,
        },
    )


@admin_member_required
def manage_logs(request):
    logs = ActivityLog.objects.select_related("actor")
    selected_action = request.GET.get("action", "")
    selected_member = request.GET.get("member", "")
    query = request.GET.get("q", "").strip()

    if selected_action:
        logs = logs.filter(action=selected_action)
    if selected_member.isdigit():
        logs = logs.filter(actor_id=selected_member)
    if query:
        logs = logs.filter(Q(summary__icontains=query) | Q(target_repr__icontains=query))

    return render(
        request,
        "manage/logs.html",
        {
            "logs": logs[:200],
            "actions": ActivityLog.Action.choices,
            "members": Member.objects.filter(is_active=True),
            "selected_action": selected_action,
            "selected_member": selected_member,
            "query": query,
        },
    )
