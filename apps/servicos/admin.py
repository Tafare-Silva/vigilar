from django.contrib import admin
from .models import Servico

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'valor_mensal', 'duracao_minima_meses', 'ativo', 'ordem')
    list_filter = ('tipo', 'ativo')
    search_fields = ('nome', 'codigo')
    ordering = ('ordem', 'nome')
