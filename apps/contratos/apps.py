from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContratosConfig(AppConfig):
    name = "apps.contratos"
    verbose_name = _("Contratos")

    def ready(self):
        import apps.contratos.signals  # noqa: F401
