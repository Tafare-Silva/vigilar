from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.contratos.models import Contrato
from apps.mensalidades.models import Mensalidade


@login_required
def index(request):
    hoje = timezone.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # ── KPIs principais ──────────────────────────────────────
    total_clientes_ativos = Cliente.objects.ativos().count()

    # Variação de clientes (mês anterior vs atual)
    primeiro_dia_mes = hoje.replace(day=1)
    clientes_mes_atual = Cliente.objects.filter(data_cadastro__gte=primeiro_dia_mes).count()
    mes_anterior = (primeiro_dia_mes - timezone.timedelta(days=1)).replace(day=1)
    clientes_mes_anterior = Cliente.objects.filter(
        data_cadastro__gte=mes_anterior,
        data_cadastro__lt=primeiro_dia_mes,
    ).count()
    variacao_clientes = (
        round(((clientes_mes_atual - clientes_mes_anterior) / max(clientes_mes_anterior, 1)) * 100)
    )

    total_contratos_ativos = Contrato.objects.ativos().count()

    # Receita do mês (mensalidades pagas no mês atual)
    receita_mes = (
        Mensalidade.objects.pagas()
        .filter(data_pagamento__month=mes_atual, data_pagamento__year=ano_atual)
        .aggregate(total=Sum("valor_pago"))["total"] or 0
    )

    total_vencidas = Mensalidade.objects.vencidas().count()
    total_inadimplentes = Cliente.objects.filter(status=Cliente.Status.INADIMPLENTE).count()
    taxa_inadimplencia = (
        round((total_inadimplentes / max(total_clientes_ativos, 1)) * 100, 1)
    )

    from apps.rondas.models import Ronda
    rondas_hoje = Ronda.objects.filter(
        data_hora_inicio__date=hoje,
        status=Ronda.Status.CONCLUIDA
    ).count()

    # ── Mensalidades por status ──────────────────────────────
    mensalidades_pagas = Mensalidade.objects.pagas().count()
    mensalidades_pendentes = Mensalidade.objects.pendentes().filter(
        data_vencimento__gte=hoje
    ).count()

    # ── Tabelas ──────────────────────────────────────────────
    mensalidades_vencendo = list(
        Mensalidade.objects.vencendo_em_dias(7)
        .select_related("contrato__cliente", "contrato")
        .order_by("data_vencimento")[:8]
    )

    ultimos_clientes = list(
        Cliente.objects.order_by("-data_cadastro")
        .select_related()[:8]
    )

    contratos_vencendo = list(
        Contrato.objects.vencendo_em_dias(30)
        .select_related("cliente", "servico")
        .order_by("data_fim")[:5]
    )

    # ── Dados para o gráfico de receita (12 meses) ───────────
    import calendar
    meses_abrev = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    labels_meses = []
    dados_receita = []
    for i in range(11, -1, -1):
        if mes_atual - i <= 0:
            m = mes_atual - i + 12
            a = ano_atual - 1
        else:
            m = mes_atual - i
            a = ano_atual
        labels_meses.append(meses_abrev[m - 1])
        total = (
            Mensalidade.objects.pagas()
            .filter(data_pagamento__month=m, data_pagamento__year=a)
            .aggregate(t=Sum("valor_pago"))["t"] or 0
        )
        dados_receita.append(float(total))

    import json
    context = {
        "hoje": hoje,
        "total_clientes_ativos": total_clientes_ativos,
        "variacao_clientes": variacao_clientes,
        "total_contratos_ativos": total_contratos_ativos,
        "receita_mes": receita_mes,
        "meta_mes": 0,
        "total_vencidas": total_vencidas,
        "total_inadimplentes": total_inadimplentes,
        "taxa_inadimplencia": taxa_inadimplencia,
        "rondas_hoje": rondas_hoje,
        "mensalidades_pagas": mensalidades_pagas,
        "mensalidades_pendentes": mensalidades_pendentes,
        "mensalidades_vencendo": mensalidades_vencendo,
        "ultimos_clientes": ultimos_clientes,
        "contratos_vencendo": contratos_vencendo,
        "labels_meses": json.dumps(labels_meses),
        "dados_receita": json.dumps(dados_receita),
    }
    return render(request, "dashboard/index.html", context)
