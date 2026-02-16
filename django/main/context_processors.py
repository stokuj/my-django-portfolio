# main/context_processors.py
from django.core.cache import cache

from .models import PageView, Project

PROJECT_COUNT_CACHE_KEY = "main:project_count"
VISITOR_COUNT_CACHE_KEY = "main:visitor_count"
COUNT_CACHE_TIMEOUT = 300


def project_count(request):
    count = cache.get(PROJECT_COUNT_CACHE_KEY)
    if count is None:
        count = Project.objects.count()
        cache.set(PROJECT_COUNT_CACHE_KEY, count, COUNT_CACHE_TIMEOUT)
    return {"project_count": count}


def visitor_counter(request):
    count = cache.get(VISITOR_COUNT_CACHE_KEY)
    if count is None:
        count = PageView.get_instance().count
        cache.set(VISITOR_COUNT_CACHE_KEY, count, COUNT_CACHE_TIMEOUT)
    return {"visitor_count": count}
