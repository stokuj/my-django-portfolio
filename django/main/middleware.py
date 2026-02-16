from .models import PageView


class VisitorCountMiddleware:
    """Increment the visitor counter once per session for home page visits."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_home = request.path in ("/", "/home/")
        if is_home and not request.session.get("has_visited"):
            counter = PageView.get_instance()
            counter.count += 1
            counter.save()
            request.session["has_visited"] = True

        return self.get_response(request)
