def member_context(request):
    member = getattr(request, "current_member", None)
    unread_count = 0
    if member:
        unread_count = member.todos.filter(status="unread").count()
    return {
        "current_member": member,
        "unread_todo_count": unread_count,
    }
