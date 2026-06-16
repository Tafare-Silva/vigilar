from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from .forms import ContratoForm
from .models import Contrato
from django.utils import timezone


class ContratoListView(LoginRequiredMixin, ListView):
    model = Contrato
    template_name = 'contratos/lista.html'
    context_object_name = 'contratos'
    paginate_by = 20

    def get_queryset(self):
        qs = Contrato.objects.select_related('cliente', 'servico').order_by('-criado_em')
        status = self.request.GET.get('status', '')
        q = self.request.GET.get('q', '').strip()
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(
                Q(cliente__nome__icontains=q) |
                Q(numero_contrato__icontains=q) |
                Q(servico__nome__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total'] = Contrato.objects.count()
        ctx['total_ativos'] = Contrato.objects.filter(status='ativo').count()
        return ctx


@login_required
def contrato_novo(request):
    cliente_id = request.GET.get('cliente')
    initial = {}
    if cliente_id:
        initial['cliente'] = cliente_id

    if request.method == 'POST':
        form = ContratoForm(request.POST)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.responsavel = request.user
            contrato.status = Contrato.Status.ATIVO
            contrato.save()
            messages.success(
                request,
                f'Contrato {contrato.numero_contrato} criado com sucesso! '
                f'{contrato.numero_mensalidades} mensalidade(s) gerada(s).'
            )
            return redirect('contratos:detalhe', pk=contrato.pk)
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = ContratoForm(initial=initial)

    return render(request, 'contratos/form.html', {
        'form': form,
        'titulo': 'Novo contrato',
        'editando': False,
        'dias_vencimento': [1, 5, 10, 15, 20, 25, 28],
        'hoje': timezone.now().date(),
    })


@login_required
def contrato_detalhe(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    mensalidades = contrato.mensalidades.order_by('numero_parcela')
    return render(request, 'contratos/detalhe.html', {
        'contrato': contrato,
        'mensalidades': mensalidades,
    })


@login_required
def contrato_renovar(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    return redirect(f"/contratos/novo/?cliente={contrato.cliente.pk}")
