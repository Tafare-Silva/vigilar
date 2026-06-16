from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ServicosConfig(AppConfig):
    name = "apps.servicos"
    verbose_name = _("Servicos")

    def ready(self):
        import apps.servicos.signals  # noqa: F401
