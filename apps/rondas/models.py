"""
apps/rondas/models.py
---------------------
Registros de rondas realizadas pelos agentes de segurança.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Agente(BaseModel):
    """Agente / vigilante que realiza as rondas."""

    class Status(models.TextChoices):
        ATIVO = "ativo", _("Ativo")
        INATIVO = "inativo", _("Inativo")
        AFASTADO = "afastado", _("Afastado")

    nome = models.CharField(_("Nome completo"), max_length=200)
    cpf = models.CharField(_("CPF"), max_length=14, unique=True)
    matricula = models.CharField(_("Matrícula"), max_length=20, unique=True, blank=True)
    telefone = models.CharField(_("Telefone"), max_length=20, blank=True)
    celular = models.CharField(_("Celular"), max_length=20, blank=True)
    email = models.EmailField(_("E-mail"), blank=True)
    numero_cnh = models.CharField(_("CNH"), max_length=20, blank=True)
    numero_curso_vigilante = models.CharField(_("N° curso vigilante"), max_length=50, blank=True)
    validade_curso = models.DateField(_("Validade do curso"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
        db_index=True,
    )
    observacoes = models.TextField(_("Observações"), blank=True)

    class Meta:
        verbose_name = _("Agente")
        verbose_name_plural = _("Agentes")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.matricula or self.cpf})"


class Ronda(BaseModel):
    """
    Registro de uma ronda realizada em um endereço do cliente.
    """

    class Status(models.TextChoices):
        PROGRAMADA = "programada", _("Programada")
        EM_ANDAMENTO = "em_andamento", _("Em andamento")
        CONCLUIDA = "concluida", _("Concluída")
        NAO_REALIZADA = "nao_realizada", _("Não realizada")
        OCORRENCIA = "ocorrencia", _("Com ocorrência")

    class Turno(models.TextChoices):
        MANHA = "manha", _("Manhã (06h-12h)")
        TARDE = "tarde", _("Tarde (12h-18h)")
        NOITE = "noite", _("Noite (18h-00h)")
        MADRUGADA = "madrugada", _("Madrugada (00h-06h)")

    # ── Relacionamentos ────────────────────────────────────────────────────
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="rondas",
        verbose_name=_("Cliente"),
    )
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rondas",
        verbose_name=_("Contrato"),
    )
    agente = models.ForeignKey(
        Agente,
        on_delete=models.PROTECT,
        related_name="rondas",
        verbose_name=_("Agente responsável"),
    )

    # ── Datas e horários ───────────────────────────────────────────────────
    data_hora_inicio = models.DateTimeField(_("Início"), db_index=True)
    data_hora_fim = models.DateTimeField(_("Fim"), null=True, blank=True)
    turno = models.CharField(
        _("Turno"),
        max_length=15,
        choices=Turno.choices,
        blank=True,
        db_index=True,
    )

    # ── Status e ocorrência ────────────────────────────────────────────────
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PROGRAMADA,
        db_index=True,
    )
    teve_ocorrencia = models.BooleanField(_("Houve ocorrência?"), default=False, db_index=True)
    descricao_ocorrencia = models.TextField(_("Descrição da ocorrência"), blank=True)
    houve_acionamento_policia = models.BooleanField(
        _("Polícia acionada?"), default=False
    )
    numero_bo = models.CharField(_("Número do B.O."), max_length=50, blank=True)

    # ── Localização (para registro de presença) ────────────────────────────
    latitude_chegada = models.DecimalField(
        _("Latitude chegada"), max_digits=9, decimal_places=6,
        null=True, blank=True,
    )
    longitude_chegada = models.DecimalField(
        _("Longitude chegada"), max_digits=9, decimal_places=6,
        null=True, blank=True,
    )

    # ── Avaliação do serviço ───────────────────────────────────────────────
    avaliacao = models.PositiveSmallIntegerField(
        _("Avaliação (1-5)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    observacoes = models.TextField(_("Observações"), blank=True)

    class Meta:
        verbose_name = _("Ronda")
        verbose_name_plural = _("Rondas")
        ordering = ["-data_hora_inicio"]
        indexes = [
            models.Index(fields=["status", "data_hora_inicio"]),
            models.Index(fields=["cliente", "status"]),
            models.Index(fields=["agente", "data_hora_inicio"]),
            models.Index(fields=["teve_ocorrencia"]),
        ]

    def __str__(self):
        return (
            f"Ronda {self.cliente} — {self.data_hora_inicio:%d/%m/%Y %H:%M} "
            f"({self.get_status_display()})"
        )

    @property
    def duracao_minutos(self):
        if self.data_hora_inicio and self.data_hora_fim:
            delta = self.data_hora_fim - self.data_hora_inicio
            return int(delta.total_seconds() / 60)
        return None

    def iniciar(self, lat=None, lng=None):
        self.status = self.Status.EM_ANDAMENTO
        self.data_hora_inicio = timezone.now()
        if lat:
            self.latitude_chegada = lat
        if lng:
            self.longitude_chegada = lng
        self.save(update_fields=[
            "status", "data_hora_inicio", "latitude_chegada",
            "longitude_chegada", "atualizado_em"
        ])

    def concluir(self, observacao="", teve_ocorrencia=False):
        self.status = self.Status.CONCLUIDA if not teve_ocorrencia else self.Status.OCORRENCIA
        self.data_hora_fim = timezone.now()
        self.teve_ocorrencia = teve_ocorrencia
        if observacao:
            self.observacoes = observacao
        self.save(update_fields=[
            "status", "data_hora_fim", "teve_ocorrencia", "observacoes", "atualizado_em"
        ])
