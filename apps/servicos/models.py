"""
apps/servicos/models.py
-----------------------
Catálogo de serviços/planos oferecidos pela empresa.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Servico(BaseModel):
    """
    Plano / serviço comercializado.
    Ex: 'Ronda Residencial Básica — R$120/mês — 12 meses'.
    """

    class Tipo(models.TextChoices):
        RONDA_RESIDENCIAL = "ronda_residencial", _("Ronda residencial")
        RONDA_COMERCIAL = "ronda_comercial", _("Ronda comercial")
        MONITORAMENTO = "monitoramento", _("Monitoramento eletrônico")
        SEGURANCA_EVENTO = "seguranca_evento", _("Segurança em evento")
        PORTARIA = "portaria", _("Portaria / Recepção")
        OUTROS = "outros", _("Outros")

    # ── Identificação ──────────────────────────────────────────────────────
    nome = models.CharField(_("Nome do serviço"), max_length=200, unique=True)
    codigo = models.CharField(_("Código"), max_length=20, unique=True, blank=True)
    tipo = models.CharField(
        _("Tipo"),
        max_length=30,
        choices=Tipo.choices,
        default=Tipo.RONDA_RESIDENCIAL,
        db_index=True,
    )
    descricao = models.TextField(_("Descrição"), blank=True)

    # ── Valores e duração ──────────────────────────────────────────────────
    valor_mensal = models.DecimalField(
        _("Valor mensal (R$)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    duracao_minima_meses = models.PositiveSmallIntegerField(
        _("Duração mínima (meses)"),
        default=12,
        help_text=_("Quantidade mínima de meses do contrato."),
    )

    # ── Detalhes operacionais ──────────────────────────────────────────────
    frequencia_rondas_semana = models.PositiveSmallIntegerField(
        _("Rondas por semana"),
        default=0,
        help_text=_("Quantas rondas por semana estão inclusas no plano. 0 = não se aplica."),
    )
    horario_inicio = models.TimeField(
        _("Horário início"), null=True, blank=True,
        help_text=_("Horário de início das rondas previstas no plano.")
    )
    horario_fim = models.TimeField(_("Horário fim"), null=True, blank=True)

    # ── Controle ───────────────────────────────────────────────────────────
    ativo = models.BooleanField(_("Ativo"), default=True, db_index=True)
    ordem = models.PositiveSmallIntegerField(
        _("Ordem de exibição"), default=0,
        help_text=_("Ordena a exibição no cadastro de contratos.")
    )

    class Meta:
        verbose_name = _("Serviço")
        verbose_name_plural = _("Serviços")
        ordering = ["ordem", "nome"]
        indexes = [
            models.Index(fields=["tipo", "ativo"]),
        ]

    def __str__(self):
        return f"{self.nome} — R${self.valor_mensal}/mês"

    def get_absolute_url(self):
        return reverse("servicos:detalhe", kwargs={"pk": self.pk})
