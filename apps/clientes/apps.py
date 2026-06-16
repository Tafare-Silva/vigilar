from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ClientesConfig(AppConfig):
    name = "apps.clientes"
    verbose_name = _("Clientes")

    def ready(self):
        import apps.clientes.signals  # noqa: F401
