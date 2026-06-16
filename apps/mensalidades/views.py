from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView
from .models import Mensalidade


class MensalidadeListView(LoginRequiredMixin, ListView):
    model = Mensalidade
    template_name = 'mensalidades/lista.html'
    context_object_name = 'mensalidades'
    paginate_by = 25

    def get_queryset(self):
        hoje = timezone.now().date()
        qs = Mensalidade.objects.select_related(
            'contrato__cliente', 'contrato__servico'
        ).order_by('data_vencimento')

        # Atualizar status de vencidas
        qs.filter(
            status='pendente',
            data_vencimento__lt=hoje
        ).update(status='vencida')

        status = self.request.GET.get('status', '')
        q = self.request.GET.get('q', '').strip()
        vencer_em = self.request.GET.get('vencer_em', '')
        mes = self.request.GET.get('mes', '')
        ano = self.request.GET.get('ano', '')
        tipo_pessoa = self.request.GET.get('tipo_pessoa', '')

        if status:
            qs = qs.filter(status=status)

        if q:
            qs = qs.filter(
                Q(contrato__cliente__nome__icontains=q) |
                Q(contrato__numero_contrato__icontains=q) |
                Q(contrato__cliente__razao_social__icontains=q) |
                Q(contrato__cliente__nome_fantasia__icontains=q)
            )

        if tipo_pessoa:
            qs = qs.filter(contrato__cliente__tipo_pessoa=tipo_pessoa)

        if vencer_em:
            dias = int(vencer_em)
            limite = hoje + timezone.timedelta(days=dias)
            qs = qs.filter(
                status__in=['pendente', 'vencida'],
                data_vencimento__lte=limite
            )

        if mes:
            qs = qs.filter(data_vencimento__month=mes)
        if ano:
            qs = qs.filter(data_vencimento__year=ano)
        else:
            # padrão: ano atual
            qs = qs.filter(data_vencimento__year=hoje.year)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoje = timezone.now().date()
        todas = Mensalidade.objects.all()
        ctx['total_pendentes'] = todas.filter(status='pendente', data_vencimento__gte=hoje).count()
        ctx['total_vencidas'] = todas.filter(status='vencida').count()
        ctx['total_pagas_mes'] = todas.filter(
            status='paga',
            data_pagamento__month=hoje.month,
            data_pagamento__year=hoje.year,
        ).count()
        ctx['valor_recebido_mes'] = todas.filter(
            status='paga',
            data_pagamento__month=hoje.month,
            data_pagamento__year=hoje.year,
        ).aggregate(t=Sum('valor_pago'))['t'] or 0

        # ── Totais do filtro atual (queryset completo, antes da paginação) ──
        fqs = self.object_list
        ctx['filtro_total']          = fqs.count()
        ctx['filtro_pagas']          = fqs.filter(status='paga').count()
        ctx['filtro_pendentes']      = fqs.filter(status='pendente').count()
        ctx['filtro_vencidas']       = fqs.filter(status='vencida').count()
        ctx['filtro_valor_recebido'] = fqs.filter(status='paga').aggregate(
            t=Sum('valor_pago'))['t'] or 0
        ctx['filtro_valor_total']    = fqs.aggregate(
            t=Sum('valor'))['t'] or 0

        ctx['hoje'] = hoje
        ctx['ano_atual'] = hoje.year
        ctx['mes_atual'] = hoje.month
        ctx['anos'] = range(hoje.year - 1, hoje.year + 2)
        ctx['meses'] = [
            (1,'Jan'),(2,'Fev'),(3,'Mar'),(4,'Abr'),(5,'Mai'),(6,'Jun'),
            (7,'Jul'),(8,'Ago'),(9,'Set'),(10,'Out'),(11,'Nov'),(12,'Dez'),
        ]
        return ctx


@login_required
def mensalidade_detalhe(request, pk):
    m = get_object_or_404(Mensalidade, pk=pk)
    return render(request, 'mensalidades/detalhe.html', {'mensalidade': m})


@login_required
def salvar_observacao(request, pk):
    """Salva ou atualiza a observação de uma mensalidade via AJAX."""
    m = get_object_or_404(Mensalidade, pk=pk)
    if request.method == "POST":
        obs = request.POST.get("observacoes", "").strip()
        m.observacoes = obs
        m.save(update_fields=["observacoes", "atualizado_em"])
        return JsonResponse({"ok": True, "observacoes": obs})
    return JsonResponse({"ok": False}, status=405)


@login_required
def registrar_pagamento(request, pk):
    m = get_object_or_404(Mensalidade, pk=pk)
    if request.method == 'POST':
        valor_pago = request.POST.get('valor_pago')
        forma = request.POST.get('forma_pagamento')
        data_pgto = request.POST.get('data_pagamento') or timezone.now().date()
        obs = request.POST.get('observacoes', '')

        if not valor_pago or not forma:
            messages.error(request, 'Informe o valor e a forma de pagamento.')
            return redirect(request.META.get('HTTP_REFERER', 'mensalidades:lista'))

        m.registrar_pagamento(
            valor_pago=valor_pago,
            forma=forma,
            usuario=request.user,
            data=data_pgto,
            observacao=obs,
        )
        messages.success(request, f'Pagamento de R$ {valor_pago} registrado com sucesso!')

        next_url = request.POST.get('next', '')
        if next_url:
            return redirect(next_url)
        return redirect('mensalidades:lista')

    return redirect('mensalidades:lista')
