from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import admin_member_required
from .forms import MemberForm, MemberLoginForm
from .models import Member


def login_view(request):
    if getattr(request, "current_member", None):
        return redirect("dashboard")
    form = MemberLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        request.session["member_id"] = form.cleaned_data["member"].id
        messages.success(request, f"欢迎回来，{form.cleaned_data['member'].name}。")
        return redirect("dashboard")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
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
            form.save()
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
