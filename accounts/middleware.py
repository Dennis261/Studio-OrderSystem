from .models import Member


class MemberSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_member = None
        member_id = request.session.get("member_id")
        if member_id:
            request.current_member = (
                Member.objects.filter(id=member_id, is_active=True)
                .first()
            )
            if request.current_member is None:
                request.session.pop("member_id", None)
        return self.get_response(request)
