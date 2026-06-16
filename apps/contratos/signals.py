"""
Signal: quando um Contrato muda para ATIVO, gera as mensalidades automaticamente.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Contrato


@receiver(post_save, sender=Contrato)
def gerar_mensalidades_ao_ativar(sender, instance, created, **kwargs):
    """
    Dispara a geração de mensalidades quando o contrato é ativado.
    A lógica dentro de gerar_mensalidades() é idempotente.
    """
    if instance.status == Contrato.Status.ATIVO and not instance.mensalidades_geradas:
        instance.gerar_mensalidades()
