"""
apps/contratos/models.py
------------------------
Contrato liga Cliente <-> Serviço e dispara a geração de mensalidades.
"""

from dateutil.relativedelta import relativedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.clientes.models import Cliente
from apps.core.models import BaseModel
from apps.servicos.models import Servico


class ContratoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deletado_em__isnull=True)

    def ativos(self):
        return self.get_queryset().filter(status=Contrato.Status.ATIVO)

    def vencendo_em_dias(self, dias=30):
        limite = timezone.now().date() + timezone.timedelta(days=dias)
        return self.ativos().filter(data_fim__lte=limite)


class Contrato(BaseModel):
    """
    Contrato de prestação de serviços de segurança.
    Ao ser ativado, gera automaticamente as mensalidades via signal.
    """

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", _("Rascunho")
        ATIVO = "ativo", _("Ativo")
        SUSPENSO = "suspenso", _("Suspenso")
        CANCELADO = "cancelado", _("Cancelado")
        ENCERRADO = "encerrado", _("Encerrado")

    # ── Partes ─────────────────────────────────────────────────────────────
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name=_("Cliente"),
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name=_("Serviço"),
    )

    # ── Vigência ───────────────────────────────────────────────────────────
    data_inicio = models.DateField(_("Data de início"))
    data_fim = models.DateField(_("Data de término"), null=True, blank=True)
    numero_mensalidades = models.PositiveSmallIntegerField(
        _("Número de mensalidades"),
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text=_("Quantidade total de parcelas a serem geradas."),
    )

    # ── Financeiro ─────────────────────────────────────────────────────────
    valor_mensal = models.DecimalField(
        _("Valor mensal (R$)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text=_("Valor negociado (pode diferir do valor padrão do serviço)."),
    )
    dia_vencimento = models.PositiveSmallIntegerField(
        _("Dia de vencimento"),
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        default=10,
        help_text=_("Dia do mês para vencimento das mensalidades (1-28)."),
    )
    desconto = models.DecimalField(
        _("Desconto (R$)"),
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    # ── Status / Controle ──────────────────────────────────────────────────
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.RASCUNHO,
        db_index=True,
    )
    numero_contrato = models.CharField(
        _("Número do contrato"),
        max_length=30,
        unique=True,
        blank=True,
        help_text=_("Gerado automaticamente se deixado em branco."),
    )
    responsavel = models.ForeignKey(
        "core.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contratos_responsavel",
        verbose_name=_("Responsável"),
    )
    mensalidades_geradas = models.BooleanField(
        _("Mensalidades geradas?"),
        default=False,
        help_text=_("Indica se as mensalidades já foram criadas para este contrato."),
    )
    observacoes = models.TextField(_("Observações"), blank=True)

    objects = ContratoManager()

    class Meta:
        verbose_name = _("Contrato")
        verbose_name_plural = _("Contratos")
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["status", "data_fim"]),
            models.Index(fields=["cliente", "status"]),
        ]

    def __str__(self):
        return f"Contrato {self.numero_contrato} — {self.cliente}"

    def get_absolute_url(self):
        return reverse("contratos:detalhe", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.numero_contrato:
            self.numero_contrato = self._gerar_numero_contrato()
        if not self.data_fim and self.data_inicio and self.numero_mensalidades:
            from datetime import date
            # garante que data_inicio é um objeto date, não string
            data = self.data_inicio
            if isinstance(data, str):
                from datetime import datetime
                data = datetime.strptime(data, '%Y-%m-%d').date()
            self.data_fim = data + relativedelta(months=self.numero_mensalidades)
        super().save(*args, **kwargs)

    def _gerar_numero_contrato(self):
        """Gera número sequencial no formato CONT-AAAA-NNNN."""
        ano = timezone.now().year
        ultimo = (
            Contrato.todos.filter(numero_contrato__startswith=f"CONT-{ano}-")
            .order_by("-numero_contrato")
            .first()
        )
        if ultimo:
            try:
                seq = int(ultimo.numero_contrato.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"CONT-{ano}-{seq:04d}"

    @property
    def valor_total(self):
        return (self.valor_mensal - self.desconto) * self.numero_mensalidades

    @property
    def esta_ativo(self):
        return self.status == self.Status.ATIVO

    @property
    def dias_para_vencer(self):
        if self.data_fim:
            return (self.data_fim - timezone.now().date()).days
        return None

    def gerar_mensalidades(self):
        from apps.mensalidades.models import Mensalidade
        from datetime import datetime

        if self.mensalidades_geradas:
            return

        # Garantir que data_inicio é um objeto date
        data = self.data_inicio
        if isinstance(data, str):
            data = datetime.strptime(data, '%Y-%m-%d').date()

        mensalidades = []
        for i in range(self.numero_mensalidades):
            # Calcular vencimento: mesmo dia do mês, avançando i meses
            vencimento = data.replace(day=int(self.dia_vencimento)) + relativedelta(months=i)
            mensalidades.append(
                Mensalidade(
                    contrato=self,
                    numero_parcela=i + 1,
                    valor=float(self.valor_mensal) - float(self.desconto or 0),
                    data_vencimento=vencimento,
                    status=Mensalidade.Status.PENDENTE,
                )
            )

        Mensalidade.objects.bulk_create(mensalidades)
        self.mensalidades_geradas = True
        self.save(update_fields=["mensalidades_geradas", "atualizado_em"])
