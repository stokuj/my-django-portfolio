import logging

from django.apps import AppConfig
from django.conf import settings


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        logger = logging.getLogger(__name__)
        logger.info("Django mode: %s", "PRODUCTION" if not settings.DEBUG else "DEVELOPMENT")
