from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RondasConfig(AppConfig):
    name = "apps.rondas"
    verbose_name = _("Rondas")

    def ready(self):
        import apps.rondas.signals  # noqa: F401
