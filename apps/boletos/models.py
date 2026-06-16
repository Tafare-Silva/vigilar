"""
apps/boletos/models.py
----------------------
Armazena os boletos emitidos via API bancária.
Desacoplado da Mensalidade para suportar múltiplos bancos.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Boleto(BaseModel):
    """
    Boleto bancário emitido para uma mensalidade.
    Guarda o retorno bruto da API para auditoria e reprocessamento.
    """

    class Banco(models.TextChoices):
        ASAAS = "asaas", _("Asaas")
        EFI = "efi", _("Efí Bank / Gerencianet")
        INTER = "inter", _("Banco Inter")
        ITAU = "itau", _("Itaú")
        BRADESCO = "bradesco", _("Bradesco")
        SICOOB = "sicoob", _("Sicoob")

    class Status(models.TextChoices):
        PENDENTE = "pendente", _("Pendente")
        EMITIDO = "emitido", _("Emitido")
        REGISTRADO = "registrado", _("Registrado no banco")
        PAGO = "pago", _("Pago")
        VENCIDO = "vencido", _("Vencido")
        CANCELADO = "cancelado", _("Cancelado")
        ERRO = "erro", _("Erro na emissão")

    # ── Relacionamento ─────────────────────────────────────────────────────
    mensalidade = models.OneToOneField(
        "mensalidades.Mensalidade",
        on_delete=models.PROTECT,
        related_name="boleto",
        verbose_name=_("Mensalidade"),
    )

    # ── Dados do boleto ────────────────────────────────────────────────────
    banco = models.CharField(
        _("Banco"),
        max_length=20,
        choices=Banco.choices,
        db_index=True,
    )
    nosso_numero = models.CharField(_("Nosso número"), max_length=50, blank=True, db_index=True)
    linha_digitavel = models.CharField(_("Linha digitável"), max_length=200, blank=True)
    codigo_barras = models.CharField(_("Código de barras"), max_length=200, blank=True)
    url_pdf = models.URLField(_("URL do PDF"), max_length=500, blank=True)
    url_pagamento = models.URLField(
        _("Link de pagamento"),
        max_length=500,
        blank=True,
        help_text=_("Link para pagamento online (Asaas, Efí etc.)."),
    )

    # ── Status e datas ─────────────────────────────────────────────────────
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
        db_index=True,
    )
    emitido_em = models.DateTimeField(_("Emitido em"), null=True, blank=True)
    vencimento = models.DateField(_("Vencimento"))
    valor = models.DecimalField(_("Valor (R$)"), max_digits=10, decimal_places=2)

    # ── ID externo (retornado pela API do banco) ───────────────────────────
    id_externo = models.CharField(
        _("ID externo (banco)"),
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_("Identificador retornado pela API da instituição financeira."),
    )

    # ── Resposta bruta da API (para auditoria) ─────────────────────────────
    resposta_emissao = models.JSONField(
        _("Resposta da emissão (JSON)"),
        null=True,
        blank=True,
        help_text=_("Payload completo retornado pela API na emissão."),
    )
    resposta_webhook = models.JSONField(
        _("Último webhook recebido (JSON)"),
        null=True,
        blank=True,
        help_text=_("Último payload de webhook recebido do banco."),
    )
    tentativas = models.PositiveSmallIntegerField(_("Tentativas de emissão"), default=0)
    erro_mensagem = models.TextField(_("Mensagem de erro"), blank=True)

    class Meta:
        verbose_name = _("Boleto")
        verbose_name_plural = _("Boletos")
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["status", "vencimento"]),
            models.Index(fields=["banco", "nosso_numero"]),
        ]

    def __str__(self):
        return f"Boleto {self.nosso_numero or self.id} — {self.get_banco_display()}"

    @property
    def esta_pago(self):
        return self.status == self.Status.PAGO

    @property
    def pode_ser_cancelado(self):
        return self.status in (self.Status.EMITIDO, self.Status.REGISTRADO)


class WebhookBoleto(models.Model):
    """
    Armazena todos os webhooks recebidos do banco para auditoria.
    Independente de estar atrelado a um boleto existente.
    """

    banco = models.CharField(_("Banco"), max_length=20)
    evento = models.CharField(_("Evento"), max_length=100, db_index=True)
    payload = models.JSONField(_("Payload"))
    ip_origem = models.GenericIPAddressField(_("IP de origem"), null=True, blank=True)
    processado = models.BooleanField(_("Processado?"), default=False, db_index=True)
    boleto = models.ForeignKey(
        Boleto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhooks",
        verbose_name=_("Boleto"),
    )
    erro = models.TextField(_("Erro ao processar"), blank=True)
    recebido_em = models.DateTimeField(_("Recebido em"), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Webhook de boleto")
        verbose_name_plural = _("Webhooks de boletos")
        ordering = ["-recebido_em"]

    def __str__(self):
        return f"Webhook {self.banco}/{self.evento} — {self.recebido_em:%d/%m/%Y %H:%M}"
