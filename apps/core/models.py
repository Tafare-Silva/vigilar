"""
apps/core/models.py
-------------------
Modelos base e modelo de usuário customizado.
Todos os outros apps herdam de BaseModel.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# ─────────────────────────────────────────────────────────────────────────────
# Manager customizado para soft-delete
# ─────────────────────────────────────────────────────────────────────────────

class AtivoManager(models.Manager):
    """Retorna apenas registros não deletados."""

    def get_queryset(self):
        return super().get_queryset().filter(deletado_em__isnull=True)


class TodosManager(models.Manager):
    """Retorna todos os registros, incluindo deletados (para admin/auditoria)."""

    def get_queryset(self):
        return super().get_queryset()


# ─────────────────────────────────────────────────────────────────────────────
# Model base — todos os apps herdam daqui
# ─────────────────────────────────────────────────────────────────────────────

class BaseModel(models.Model):
    """
    Model base com UUID, timestamps e soft-delete.

    Campos:
        id          — UUID v4, imutável, chave primária
        criado_em   — preenchido automaticamente na criação
        atualizado_em — atualizado em cada save()
        deletado_em — preenchido no soft-delete; NULL = ativo
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em"),
        db_index=True,
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Atualizado em"),
    )
    deletado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Deletado em"),
        db_index=True,
    )

    # Manager padrão filtra registros ativos
    objects = AtivoManager()
    todos = TodosManager()

    class Meta:
        abstract = True
        ordering = ["-criado_em"]

    def soft_delete(self):
        """Marca o registro como deletado sem remover do banco."""
        self.deletado_em = timezone.now()
        self.save(update_fields=["deletado_em", "atualizado_em"])

    def restaurar(self):
        """Restaura um registro soft-deletado."""
        self.deletado_em = None
        self.save(update_fields=["deletado_em", "atualizado_em"])

    @property
    def ativo(self):
        return self.deletado_em is None

    def __str__(self):
        return f"{self.__class__.__name__} ({self.id})"


# ─────────────────────────────────────────────────────────────────────────────
# Usuário customizado
# ─────────────────────────────────────────────────────────────────────────────

class UsuarioManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("O e-mail é obrigatório."))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("perfil", Usuario.Perfil.ADMIN)
        if "username" not in extra_fields:
            extra_fields["username"] = email.split("@")[0]
    
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Usuário do sistema com autenticação via e-mail.
    Perfis: ADMIN, GERENTE, OPERADOR, FINANCEIRO.
    """

    class Perfil(models.TextChoices):
        ADMIN = "admin", _("Administrador")
        GERENTE = "gerente", _("Gerente")
        OPERADOR = "operador", _("Operador")
        FINANCEIRO = "financeiro", _("Financeiro")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("E-mail"), unique=True, db_index=True)
    username = models.CharField(          
    _("Nome de usuário"),
    max_length=50,
    unique=True,
    help_text=_("Usado para login. Apenas letras, números e @/./+/-/_"),
    )
    nome = models.CharField(_("Nome completo"), max_length=200)
    perfil = models.CharField(
        _("Perfil"),
        max_length=20,
        choices=Perfil.choices,
        default=Perfil.OPERADOR,
        db_index=True,
    )
    telefone = models.CharField(_("Telefone"), max_length=20, blank=True)
    avatar = models.ImageField(
        _("Avatar"), upload_to="avatars/%Y/%m/", null=True, blank=True
    )
    is_active = models.BooleanField(_("Ativo"), default=True)
    is_staff = models.BooleanField(_("Staff"), default=False)
    criado_em = models.DateTimeField(_("Criado em"), auto_now_add=True)
    atualizado_em = models.DateTimeField(_("Atualizado em"), auto_now=True)
    ultimo_acesso = models.DateTimeField(_("Último acesso"), null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        verbose_name = _("Usuário")
        verbose_name_plural = _("Usuários")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} <{self.email}>"

    @property
    def primeiro_nome(self):
        return self.nome.split()[0] if self.nome else ""

    def tem_perfil(self, *perfis):
        return self.perfil in perfis


# ─────────────────────────────────────────────────────────────────────────────
# Log de atividade (auditoria manual além do django-auditlog)
# ─────────────────────────────────────────────────────────────────────────────

class LogAtividade(models.Model):
    """Registro de ações realizadas pelos usuários no sistema."""

    class Acao(models.TextChoices):
        CRIACAO = "criacao", _("Criação")
        EDICAO = "edicao", _("Edição")
        EXCLUSAO = "exclusao", _("Exclusão")
        RESTAURACAO = "restauracao", _("Restauração")
        PAGAMENTO = "pagamento", _("Pagamento")
        EMISSAO_BOLETO = "emissao_boleto", _("Emissão de boleto")
        CANCELAMENTO = "cancelamento", _("Cancelamento")
        LOGIN = "login", _("Login")
        LOGOUT = "logout", _("Logout")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="logs",
        verbose_name=_("Usuário"),
    )
    acao = models.CharField(_("Ação"), max_length=30, choices=Acao.choices, db_index=True)
    tabela = models.CharField(_("Tabela"), max_length=100, db_index=True)
    registro_id = models.CharField(_("ID do registro"), max_length=36, blank=True, db_index=True)
    descricao = models.TextField(_("Descrição"), blank=True)
    dados_anteriores = models.JSONField(_("Dados anteriores"), null=True, blank=True)
    dados_novos = models.JSONField(_("Dados novos"), null=True, blank=True)
    ip = models.GenericIPAddressField(_("IP"), null=True, blank=True)
    criado_em = models.DateTimeField(_("Criado em"), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Log de atividade")
        verbose_name_plural = _("Logs de atividade")
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tabela", "registro_id"]),
            models.Index(fields=["usuario", "acao"]),
        ]

    def __str__(self):
        return f"[{self.get_acao_display()}] {self.tabela} — {self.usuario}"


# ─────────────────────────────────────────────────────────────────────────────
# Configuração da empresa — singleton (pk sempre = 1)
# ─────────────────────────────────────────────────────────────────────────────

class Empresa(models.Model):
    """
    Dados da empresa que utiliza o sistema.
    Singleton: só deve existir um registro (pk=1).
    """

    nome = models.CharField(_("Nome da empresa"), max_length=200, default="Minha Empresa")
    cnpj = models.CharField(_("CNPJ"), max_length=18, blank=True)
    inscricao_estadual = models.CharField(_("Inscrição estadual"), max_length=30, blank=True)
    telefone = models.CharField(_("Telefone"), max_length=20, blank=True)
    celular = models.CharField(_("Celular"), max_length=20, blank=True)
    email = models.EmailField(_("E-mail"), blank=True)
    site = models.URLField(_("Site"), blank=True)

    # Endereço
    logradouro = models.CharField(_("Logradouro"), max_length=200, blank=True)
    numero = models.CharField(_("Número"), max_length=10, blank=True)
    complemento = models.CharField(_("Complemento"), max_length=100, blank=True)
    bairro = models.CharField(_("Bairro"), max_length=100, blank=True)
    cidade = models.CharField(_("Cidade"), max_length=100, blank=True)
    estado = models.CharField(_("Estado"), max_length=2, blank=True)
    cep = models.CharField(_("CEP"), max_length=9, blank=True)

    # Logo e identidade visual
    logo = models.ImageField(
        _("Logo"),
        upload_to="empresa/logos/",
        null=True,
        blank=True,
        help_text=_("Aparece no cabeçalho do recibo e no sistema. Recomendado: PNG fundo transparente, mín. 200×80 px."),
    )

    # Texto livre para rodapé do recibo
    rodape_recibo = models.CharField(
        _("Rodapé do recibo"),
        max_length=300,
        blank=True,
        help_text=_("Texto exibido no rodapé do recibo de pagamento."),
    )

    atualizado_em = models.DateTimeField(_("Atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Empresa")
        verbose_name_plural = _("Empresa")

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        """Garante que só exista uma única instância (singleton)."""
        self.pk = 1
        super().save(*args, **kwargs)
        # Invalida cache
        from django.core.cache import cache
        cache.delete("empresa_config")

    def delete(self, *args, **kwargs):
        pass  # Impede exclusão do singleton

    @classmethod
    def get(cls):
        """Retorna a instância única, criando com valores padrão se não existir."""
        from django.conf import settings
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "nome": getattr(settings, "NOME_EMPRESA", "Minha Empresa"),
                "cnpj": getattr(settings, "CNPJ_EMPRESA", ""),
                "telefone": getattr(settings, "TELEFONE_EMPRESA", ""),
            },
        )
        return obj
