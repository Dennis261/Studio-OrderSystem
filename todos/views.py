from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.activity import log_activity
from accounts.decorators import member_required
from accounts.models import ActivityLog

from .models import Todo


@member_required
def todo_list(request):
    status = request.GET.get("status", "")
    todos = Todo.objects.filter(target=request.current_member).select_related(
        "order", "source_post", "source_post__author"
    )
    if status in dict(Todo.Status.choices):
        todos = todos.filter(status=status)
    return render(
        request,
        "todos/list.html",
        {
            "todos": todos,
            "status": status,
            "status_choices": Todo.Status.choices,
        },
    )


@member_required
def open_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk, target=request.current_member)
    if todo.status == Todo.Status.UNREAD:
        todo.status = Todo.Status.READ
        todo.read_at = timezone.now()
        todo.save(update_fields=["status", "read_at"])
        log_activity(
            request,
            ActivityLog.Action.TODO_READ,
            target=todo.order,
            summary=f"阅读待办：{todo.order.customer_display}",
            metadata={"todo_id": todo.id, "source_post_id": todo.source_post_id},
        )
    return redirect(f"{todo.order.get_absolute_url()}#post-{todo.source_post_id}")


@member_required
@require_POST
def complete_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk, target=request.current_member)
    todo.status = Todo.Status.DONE
    todo.done_at = timezone.now()
    if todo.read_at is None:
        todo.read_at = timezone.now()
    todo.save(update_fields=["status", "read_at", "done_at"])
    log_activity(
        request,
        ActivityLog.Action.TODO_DONE,
        target=todo.order,
        summary=f"完成待办：{todo.order.customer_display}",
        metadata={"todo_id": todo.id, "source_post_id": todo.source_post_id},
    )
    return redirect(request.POST.get("next") or "todo_list")
