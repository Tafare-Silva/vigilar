from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FornecedoresConfig(AppConfig):
    name = "apps.fornecedores"
    verbose_name = _("Fornecedores")

    def ready(self):
        import apps.fornecedores.signals  # noqa: F401
