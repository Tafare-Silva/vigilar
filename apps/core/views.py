"""
apps/core/views.py
------------------
Views do módulo core (configurações da empresa, etc.).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render

from .forms import EmpresaForm
from .models import Empresa


@login_required
def empresa_config(request):
    """Cadastro/edição dos dados da empresa (singleton)."""
    empresa = Empresa.get()

    if request.method == "POST":
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            # cache já é invalidado pelo model.save()
            messages.success(request, "Dados da empresa salvos com sucesso!")
            return redirect("configuracoes:empresa")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, "core/empresa.html", {"form": form, "empresa": empresa})
