import logging

from django.apps import AppConfig
from django.conf import settings


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        logger = logging.getLogger(__name__)
        logger.info("Django mode: %s", "PRODUCTION" if not settings.DEBUG else "DEVELOPMENT")
