from .models import ActivityLog


def log_activity(request, action, target=None, summary="", metadata=None, actor=None):
    if request is None:
        current_actor = actor
        ip_address = None
        user_agent = ""
    else:
        current_actor = actor if actor is not None else getattr(request, "current_member", None)
        ip_address = _client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

    target_type = ""
    target_id = None
    target_repr = ""
    if target is not None:
        target_type = target._meta.verbose_name
        target_id = target.pk
        target_repr = str(target)[:160]

    return ActivityLog.objects.create(
        actor=current_actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_repr=target_repr,
        summary=summary,
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
