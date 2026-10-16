from django.conf import settings
from django.db.models import F

from .models import PageView


class VisitorCountMiddleware:
    """Increment the visitor counter once per browser (cookie) for home page visits."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        first_visit = request.path == "/" and not request.COOKIES.get("has_visited")
        if first_visit:
            counter = PageView.get_instance()
            PageView.objects.filter(id=counter.id).update(count=F("count") + 1)

        response = self.get_response(request)

        if first_visit:
            response.set_cookie(
                "has_visited",
                "1",
                max_age=settings.SESSION_COOKIE_AGE,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=True,
                samesite="Lax",
            )
        return response
