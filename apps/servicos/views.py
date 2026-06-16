from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from .forms import ServicoForm
from .models import Servico


class ServicoListView(LoginRequiredMixin, ListView):
    model = Servico
    template_name = 'servicos/lista.html'
    context_object_name = 'servicos'

    def get_queryset(self):
        return Servico.objects.order_by('ordem', 'nome')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total'] = Servico.objects.count()
        ctx['total_ativos'] = Servico.objects.filter(ativo=True).count()
        return ctx


@login_required
def servico_novo(request):
    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            servico = form.save()
            messages.success(request, f'Serviço "{servico.nome}" cadastrado com sucesso!')
            if request.POST.get('action') == 'salvar_novo':
                return redirect('servicos:novo')
            return redirect('servicos:lista')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = ServicoForm()

    return render(request, 'servicos/form.html', {
        'form': form,
        'titulo': 'Novo serviço',
        'editando': False,
    })


@login_required
def servico_editar(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            servico = form.save()
            messages.success(request, f'Serviço "{servico.nome}" atualizado!')
            return redirect('servicos:lista')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = ServicoForm(instance=servico)

    return render(request, 'servicos/form.html', {
        'form': form,
        'servico': servico,
        'titulo': f'Editar — {servico.nome}',
        'editando': True,
    })


@login_required
def servico_toggle_ativo(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    servico.ativo = not servico.ativo
    servico.save(update_fields=['ativo', 'atualizado_em'])
    status = 'ativado' if servico.ativo else 'desativado'
    messages.success(request, f'Serviço "{servico.nome}" {status}.')
    return redirect('servicos:lista')
