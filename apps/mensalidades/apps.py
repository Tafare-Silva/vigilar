from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MensalidadesConfig(AppConfig):
    name = "apps.mensalidades"
    verbose_name = _("Mensalidades")

    def ready(self):
        import apps.mensalidades.signals  # noqa: F401
