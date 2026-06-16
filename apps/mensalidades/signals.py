"""
Signal: quando uma mensalidade é paga, sincroniza o boleto correspondente.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Mensalidade


@receiver(post_save, sender=Mensalidade)
def sincronizar_boleto_ao_pagar(sender, instance, **kwargs):
    """
    Se a mensalidade foi paga e tem boleto associado, atualiza o status do boleto.
    """
    if instance.status == Mensalidade.Status.PAGA:
        try:
            boleto = instance.boleto
            if boleto.status not in ("pago", "cancelado"):
                from apps.boletos.models import Boleto
                boleto.status = Boleto.Status.PAGO
                boleto.save(update_fields=["status", "atualizado_em"])
        except Exception:
            pass
