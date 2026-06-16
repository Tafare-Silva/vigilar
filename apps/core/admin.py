from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import LogAtividade, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("email", "nome", "perfil", "is_active", "criado_em")
    list_filter = ("perfil", "is_active", "is_staff")
    search_fields = ("email", "nome")
    ordering = ("nome",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Dados pessoais"), {"fields": ("nome", "telefone", "avatar")}),
        (_("Permissões"), {"fields": ("perfil", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Datas"), {"fields": ("ultimo_acesso", "criado_em", "atualizado_em")}),
    )
    readonly_fields = ("criado_em", "atualizado_em", "ultimo_acesso")
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "nome", "perfil", "password1", "password2")}),
    )


@admin.register(LogAtividade)
class LogAtividadeAdmin(admin.ModelAdmin):
    list_display = ("acao", "tabela", "registro_id", "usuario", "ip", "criado_em")
    list_filter = ("acao", "tabela")
    search_fields = ("tabela", "registro_id", "descricao")
    readonly_fields = ("criado_em",)
    ordering = ("-criado_em",)
