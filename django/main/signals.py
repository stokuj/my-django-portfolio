from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .context_processors import PROJECT_COUNT_CACHE_KEY
from .models import Project


@receiver(post_save, sender=Project)
@receiver(post_delete, sender=Project)
def invalidate_project_count_cache(**kwargs):
    cache.delete(PROJECT_COUNT_CACHE_KEY)
