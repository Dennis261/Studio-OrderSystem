from accounts.models import Member


def mentioned_members(body):
    mentions = []
    seen = set()
    for member in Member.objects.filter(is_active=True).order_by("-name"):
        token = f"@{member.name}"
        if token in body and member.id not in seen:
            mentions.append(member)
            seen.add(member.id)
    return mentions


def create_todos_for_mentions(post):
    from todos.models import Todo

    todos = []
    for member in mentioned_members(post.body):
        todo, created = Todo.objects.get_or_create(
            source_post=post,
            target=member,
            defaults={"order": post.order, "status": Todo.Status.UNREAD},
        )
        if created:
            todos.append(todo)
    return todos
