"""
apps/mensalidades/models.py
---------------------------
Mensalidade gerada automaticamente a partir de um Contrato.
É o coração financeiro do sistema.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class MensalidadeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deletado_em__isnull=True)

    def pendentes(self):
        return self.get_queryset().filter(status=Mensalidade.Status.PENDENTE)

    def vencidas(self):
        return self.get_queryset().filter(
            status=Mensalidade.Status.PENDENTE,
            data_vencimento__lt=timezone.now().date(),
        )

    def pagas(self):
        return self.get_queryset().filter(status=Mensalidade.Status.PAGA)

    def do_mes(self, ano, mes):
        return self.get_queryset().filter(
            data_vencimento__year=ano,
            data_vencimento__month=mes,
        )

    def vencendo_em_dias(self, dias=7):
        hoje = timezone.now().date()
        limite = hoje + timezone.timedelta(days=dias)
        return self.pendentes().filter(data_vencimento__range=[hoje, limite])


class Mensalidade(BaseModel):
    """
    Parcela mensal de um contrato.
    Status: pendente → paga | vencida | cancelada.
    """

    class Status(models.TextChoices):
        PENDENTE = "pendente", _("Pendente")
        PAGA = "paga", _("Paga")
        VENCIDA = "vencida", _("Vencida")
        CANCELADA = "cancelada", _("Cancelada")
        ESTORNADA = "estornada", _("Estornada")

    class FormaPagamento(models.TextChoices):
        BOLETO = "boleto", _("Boleto bancário")
        PIX = "pix", _("PIX")
        CARTAO_CREDITO = "cartao_credito", _("Cartão de crédito")
        CARTAO_DEBITO = "cartao_debito", _("Cartão de débito")
        TRANSFERENCIA = "transferencia", _("Transferência bancária")
        DINHEIRO = "dinheiro", _("Dinheiro")
        CHEQUE = "cheque", _("Cheque")

    # ── Relacionamento ─────────────────────────────────────────────────────
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.PROTECT,
        related_name="mensalidades",
        verbose_name=_("Contrato"),
    )

    # ── Identificação da parcela ────────────────────────────────────────────
    numero_parcela = models.PositiveSmallIntegerField(_("Número da parcela"))

    # ── Valores ────────────────────────────────────────────────────────────
    valor = models.DecimalField(
        _("Valor (R$)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    valor_pago = models.DecimalField(
        _("Valor pago (R$)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    juros = models.DecimalField(
        _("Juros (R$)"),
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    multa = models.DecimalField(
        _("Multa (R$)"),
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    desconto_pagamento = models.DecimalField(
        _("Desconto no pagamento (R$)"),
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    # ── Datas ──────────────────────────────────────────────────────────────
    data_vencimento = models.DateField(_("Data de vencimento"), db_index=True)
    data_pagamento = models.DateField(_("Data de pagamento"), null=True, blank=True)

    # ── Status / Pagamento ─────────────────────────────────────────────────
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
        db_index=True,
    )
    forma_pagamento = models.CharField(
        _("Forma de pagamento"),
        max_length=20,
        choices=FormaPagamento.choices,
        blank=True,
    )
    recebido_por = models.ForeignKey(
        "core.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensalidades_recebidas",
        verbose_name=_("Recebido por"),
    )
    comprovante = models.FileField(
        _("Comprovante"),
        upload_to="comprovantes/%Y/%m/",
        null=True,
        blank=True,
    )
    observacoes = models.TextField(_("Observações"), blank=True)

    objects = MensalidadeManager()

    class Meta:
        verbose_name = _("Mensalidade")
        verbose_name_plural = _("Mensalidades")
        ordering = ["data_vencimento"]
        unique_together = [("contrato", "numero_parcela")]
        indexes = [
            models.Index(fields=["status", "data_vencimento"]),
            models.Index(fields=["contrato", "status"]),
        ]

    def __str__(self):
        return (
            f"Parcela {self.numero_parcela} — {self.contrato.cliente} "
            f"— Venc. {self.data_vencimento:%d/%m/%Y}"
        )

    def get_absolute_url(self):
        return reverse("mensalidades:detalhe", kwargs={"pk": self.pk})

    @property
    def esta_vencida(self):
        return (
            self.status == self.Status.PENDENTE
            and self.data_vencimento < timezone.now().date()
        )

    @property
    def dias_atraso(self):
        if self.esta_vencida:
            return (timezone.now().date() - self.data_vencimento).days
        return 0

    @property
    def valor_total_a_pagar(self):
        return self.valor + self.juros + self.multa - self.desconto_pagamento

    def registrar_pagamento(self, valor_pago, forma, usuario=None, data=None, observacao=""):
        """Registra o pagamento da mensalidade."""
        self.valor_pago = valor_pago
        self.forma_pagamento = forma
        self.data_pagamento = data or timezone.now().date()
        self.status = self.Status.PAGA
        self.recebido_por = usuario
        if observacao:
            self.observacoes = observacao
        self.save(update_fields=[
            "valor_pago", "forma_pagamento", "data_pagamento",
            "status", "recebido_por", "observacoes", "atualizado_em",
        ])

    def atualizar_status_vencimento(self):
        """Chamado periodicamente pelo Celery para marcar mensalidades vencidas."""
        if self.esta_vencida:
            self.status = self.Status.VENCIDA
            self.save(update_fields=["status", "atualizado_em"])
