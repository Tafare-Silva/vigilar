"""
apps/clientes/models.py
-----------------------
Modelo de Cliente (Pessoa Física ou Jurídica).
"""

from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class ClienteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deletado_em__isnull=True)

    def pessoas_fisicas(self):
        return self.get_queryset().filter(tipo_pessoa=Cliente.TipoPessoa.FISICA)

    def pessoas_juridicas(self):
        return self.get_queryset().filter(tipo_pessoa=Cliente.TipoPessoa.JURIDICA)

    def ativos(self):
        return self.get_queryset().filter(status=Cliente.Status.ATIVO)

    def inadimplentes(self):
        return self.get_queryset().filter(status=Cliente.Status.INADIMPLENTE)


class Cliente(BaseModel):
    """
    Representa um cliente contratante de serviços de segurança.
    Suporta Pessoa Física (CPF) e Pessoa Jurídica (CNPJ).
    """

    class TipoPessoa(models.TextChoices):
        FISICA = "PF", _("Pessoa Física")
        JURIDICA = "PJ", _("Pessoa Jurídica")

    class Status(models.TextChoices):
        ATIVO = "ativo", _("Ativo")
        INATIVO = "inativo", _("Inativo")
        INADIMPLENTE = "inadimplente", _("Inadimplente")
        SUSPENSO = "suspenso", _("Suspenso")

    # ── Identificação ──────────────────────────────────────────────────────
    tipo_pessoa = models.CharField(
        _("Tipo de pessoa"),
        max_length=2,
        choices=TipoPessoa.choices,
        default=TipoPessoa.FISICA,
        db_index=True,
    )
    # PF
    nome = models.CharField(_("Nome completo"), max_length=200)
    cpf = models.CharField(
        _("CPF"),
        max_length=14,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", "CPF inválido.")],
    )
    rg = models.CharField(_("RG"), max_length=20, blank=True)
    data_nascimento = models.DateField(_("Data de nascimento"), null=True, blank=True)

    # PJ
    razao_social = models.CharField(_("Razão social"), max_length=200, blank=True)
    nome_fantasia = models.CharField(_("Nome fantasia"), max_length=200, blank=True)
    cnpj = models.CharField(
        _("CNPJ"),
        max_length=18,
        blank=True,
        unique=True,
        null=True,
        validators=[RegexValidator(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", "CNPJ inválido.")],
    )
    inscricao_estadual = models.CharField(_("Inscrição estadual"), max_length=30, blank=True)

    # ── Contato ────────────────────────────────────────────────────────────
    email = models.EmailField(_("E-mail"), blank=True, db_index=True)
    telefone = models.CharField(_("Telefone"), max_length=20, blank=True)
    celular = models.CharField(
        _("Celular"),
        max_length=20,
        blank=True,
        validators=[RegexValidator(r"^\(\d{2}\)\s?\d{4,5}-\d{4}$", "Celular inválido.")],
    )
    whatsapp = models.BooleanField(_("Tem WhatsApp?"), default=True)

    # ── Endereço ───────────────────────────────────────────────────────────
    cep = models.CharField(
        _("CEP"),
        max_length=9,
        blank=True,
        validators=[RegexValidator(r"^\d{5}-\d{3}$", "CEP inválido.")],
    )
    logradouro = models.CharField(_("Logradouro"), max_length=200, blank=True)
    numero = models.CharField(_("Número"), max_length=10, blank=True)
    complemento = models.CharField(_("Complemento"), max_length=100, blank=True)
    bairro = models.CharField(_("Bairro"), max_length=100, blank=True)
    cidade = models.CharField(_("Cidade"), max_length=100, blank=True, db_index=True)
    estado = models.CharField(_("Estado"), max_length=2, blank=True, db_index=True)
    ponto_referencia = models.CharField(_("Ponto de referência"), max_length=200, blank=True)

    # ── Status / Controle ──────────────────────────────────────────────────
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
        db_index=True,
    )
    data_cadastro = models.DateField(_("Data de cadastro"), auto_now_add=True)
    observacoes = models.TextField(_("Observações"), blank=True)

    objects = ClienteManager()

    class Meta:
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["status", "tipo_pessoa"]),
            models.Index(fields=["cidade", "estado"]),
        ]

    def __str__(self):
        return self.nome_exibicao

    def get_absolute_url(self):
        return reverse("clientes:detalhe", kwargs={"pk": self.pk})

    @property
    def nome_exibicao(self):
        """Retorna o nome mais adequado conforme o tipo de pessoa."""
        if self.tipo_pessoa == self.TipoPessoa.JURIDICA:
            return self.nome_fantasia or self.razao_social or self.nome
        return self.nome

    @property
    def documento(self):
        """Retorna CPF ou CNPJ conforme tipo de pessoa."""
        if self.tipo_pessoa == self.TipoPessoa.FISICA:
            return self.cpf or ""
        return self.cnpj or ""

    @property
    def endereco_completo(self):
        partes = [self.logradouro, self.numero]
        if self.complemento:
            partes.append(self.complemento)
        partes += [self.bairro, f"{self.cidade}/{self.estado}", self.cep]
        return ", ".join(p for p in partes if p)

    @property
    def tem_contrato_ativo(self):
        return self.contratos.filter(status="ativo").exists()
