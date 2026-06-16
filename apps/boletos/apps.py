from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BoletosConfig(AppConfig):
    name = "apps.boletos"
    verbose_name = _("Boletos")

    def ready(self):
        import apps.boletos.signals  # noqa: F401
