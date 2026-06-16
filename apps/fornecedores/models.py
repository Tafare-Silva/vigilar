"""
apps/fornecedores/models.py
---------------------------
Modelo de Fornecedor (sempre Pessoa Jurídica).
"""

from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Fornecedor(BaseModel):
    """Fornecedor de produtos e serviços para a empresa de segurança."""

    class Categoria(models.TextChoices):
        EQUIPAMENTOS = "equipamentos", _("Equipamentos de segurança")
        UNIFORMES = "uniformes", _("Uniformes e EPIs")
        VEICULOS = "veiculos", _("Veículos e manutenção")
        TECNOLOGIA = "tecnologia", _("Tecnologia e TI")
        SERVICOS_GERAIS = "servicos_gerais", _("Serviços gerais")
        RECURSOS_HUMANOS = "recursos_humanos", _("Recursos humanos / Terceiros")
        OUTROS = "outros", _("Outros")

    class Status(models.TextChoices):
        ATIVO = "ativo", _("Ativo")
        INATIVO = "inativo", _("Inativo")
        BLOQUEADO = "bloqueado", _("Bloqueado")

    # ── Identificação ──────────────────────────────────────────────────────
    razao_social = models.CharField(_("Razão social"), max_length=200)
    nome_fantasia = models.CharField(_("Nome fantasia"), max_length=200, blank=True)
    cnpj = models.CharField(
        _("CNPJ"),
        max_length=18,
        unique=True,
        validators=[RegexValidator(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", "CNPJ inválido.")],
    )
    inscricao_estadual = models.CharField(_("Inscrição estadual"), max_length=30, blank=True)
    inscricao_municipal = models.CharField(_("Inscrição municipal"), max_length=30, blank=True)

    # ── Categoria / Status ─────────────────────────────────────────────────
    categoria = models.CharField(
        _("Categoria"),
        max_length=30,
        choices=Categoria.choices,
        default=Categoria.OUTROS,
        db_index=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
        db_index=True,
    )

    # ── Contato principal ──────────────────────────────────────────────────
    contato_nome = models.CharField(_("Nome do contato"), max_length=200, blank=True)
    email = models.EmailField(_("E-mail"), blank=True)
    telefone = models.CharField(_("Telefone"), max_length=20, blank=True)
    celular = models.CharField(_("Celular"), max_length=20, blank=True)
    site = models.URLField(_("Site"), blank=True)

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
    cidade = models.CharField(_("Cidade"), max_length=100, blank=True)
    estado = models.CharField(_("Estado"), max_length=2, blank=True)

    # ── Dados bancários ────────────────────────────────────────────────────
    banco = models.CharField(_("Banco"), max_length=100, blank=True)
    agencia = models.CharField(_("Agência"), max_length=10, blank=True)
    conta = models.CharField(_("Conta"), max_length=20, blank=True)
    tipo_conta = models.CharField(
        _("Tipo de conta"),
        max_length=20,
        choices=[("corrente", "Corrente"), ("poupanca", "Poupança")],
        blank=True,
    )
    chave_pix = models.CharField(_("Chave PIX"), max_length=150, blank=True)

    # ── Notas ──────────────────────────────────────────────────────────────
    observacoes = models.TextField(_("Observações"), blank=True)

    class Meta:
        verbose_name = _("Fornecedor")
        verbose_name_plural = _("Fornecedores")
        ordering = ["razao_social"]
        indexes = [
            models.Index(fields=["categoria", "status"]),
        ]

    def __str__(self):
        return self.nome_fantasia or self.razao_social

    def get_absolute_url(self):
        return reverse("fornecedores:detalhe", kwargs={"pk": self.pk})
