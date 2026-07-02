from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from apps.contratos.models import Contrato
from apps.servicos.models import Servico

from .forms import ClienteForm
from .models import Cliente

ESTADOS_BR = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
]


class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        qs = Cliente.objects.all().order_by("nome")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        tipo = self.request.GET.get("tipo", "")
        cidade = self.request.GET.get("cidade", "").strip()

        if q:
            qs = qs.filter(
                Q(nome__icontains=q) | Q(cpf__icontains=q) |
                Q(cnpj__icontains=q) | Q(email__icontains=q) |
                Q(razao_social__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if tipo:
            qs = qs.filter(tipo_pessoa=tipo)
        if cidade:
            qs = qs.filter(cidade__icontains=cidade)

        order = self.request.GET.get("order", "nome")
        if order in ["nome", "-nome", "data_cadastro", "-data_cadastro"]:
            qs = qs.order_by(order)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        todos = Cliente.objects.all()
        ctx["total_clientes"] = todos.count()
        ctx["total_ativos"] = todos.filter(status=Cliente.Status.ATIVO).count()
        ctx["total_inadimplentes"] = todos.filter(status=Cliente.Status.INADIMPLENTE).count()
        ctx["total_suspensos"] = todos.filter(status=Cliente.Status.SUSPENSO).count()
        return ctx


def _contexto_form(form, editando=False, cliente=None):
    """Contexto comum para as views de criação e edição."""
    return {
        "form": form,
        "titulo": f"Editar — {cliente.nome_exibicao}" if editando else "Novo cliente",
        "subtitulo": "Atualize os dados do cliente" if editando else "Preencha os dados do novo cliente",
        "editando": editando,
        "cliente": cliente,
        "estados": ESTADOS_BR,
        "servicos": Servico.objects.filter(ativo=True).order_by("nome"),
        "dias_vencimento": [1, 5, 10, 15, 20, 25, 28],
    }


@login_required
def cliente_novo(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        criar_contrato = request.POST.get("criar_contrato") == "1"

        if form.is_valid():
            # Validar campos do contrato se marcado
            erros_contrato = []
            if criar_contrato:
                if not request.POST.get("servico_id"):
                    erros_contrato.append("Selecione um serviço.")
                if not request.POST.get("valor_mensal"):
                    erros_contrato.append("Informe o valor da mensalidade.")
                if not request.POST.get("num_mensalidades"):
                    erros_contrato.append("Informe a quantidade de mensalidades.")
                if not request.POST.get("data_inicio"):
                    erros_contrato.append("Informe a data de início.")
                if not request.POST.get("dia_vencimento"):
                    erros_contrato.append("Informe o dia de vencimento.")

            if erros_contrato:
                for e in erros_contrato:
                    messages.error(request, e)
                return render(request, "clientes/form.html", _contexto_form(form))

            with transaction.atomic():
                cliente = form.save()

                if criar_contrato:
                    servico = Servico.objects.get(pk=request.POST["servico_id"])
                    contrato = Contrato.objects.create(
                        cliente=cliente,
                        servico=servico,
                        data_inicio=request.POST["data_inicio"],
                        numero_mensalidades=int(request.POST["num_mensalidades"]),
                        valor_mensal=request.POST["valor_mensal"],
                        dia_vencimento=int(request.POST["dia_vencimento"]),
                        status=Contrato.Status.ATIVO,  # já ativa e dispara signal
                        responsavel=request.user,
                    )
                    messages.success(
                        request,
                        f"Cliente {cliente.nome_exibicao} cadastrado! "
                        f"{contrato.numero_mensalidades} mensalidade(s) gerada(s) — "
                        f"contrato {contrato.numero_contrato}."
                    )
                else:
                    messages.success(request, f"Cliente {cliente.nome_exibicao} cadastrado com sucesso!")

            return redirect("clientes:detalhe", pk=cliente.pk)

        else:
            messages.error(request, "Corrija os erros abaixo antes de salvar.")

    else:
        form = ClienteForm()

    return render(request, "clientes/form.html", _contexto_form(form))


@login_required
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        criar_contrato = request.POST.get("criar_contrato") == "1"

        if form.is_valid():
            erros_contrato = []
            if criar_contrato:
                if not request.POST.get("servico_id"):
                    erros_contrato.append("Selecione um serviço.")
                if not request.POST.get("valor_mensal"):
                    erros_contrato.append("Informe o valor da mensalidade.")
                if not request.POST.get("num_mensalidades"):
                    erros_contrato.append("Informe a quantidade de mensalidades.")
                if not request.POST.get("data_inicio"):
                    erros_contrato.append("Informe a data de início.")
                if not request.POST.get("dia_vencimento"):
                    erros_contrato.append("Informe o dia de vencimento.")

            if erros_contrato:
                for e in erros_contrato:
                    messages.error(request, e)
                return render(request, "clientes/form.html", _contexto_form(form, editando=True, cliente=cliente))

            with transaction.atomic():
                cliente = form.save()

                if criar_contrato:
                    servico = Servico.objects.get(pk=request.POST["servico_id"])
                    contrato = Contrato.objects.create(
                        cliente=cliente,
                        servico=servico,
                        data_inicio=request.POST["data_inicio"],
                        numero_mensalidades=int(request.POST["num_mensalidades"]),
                        valor_mensal=request.POST["valor_mensal"],
                        dia_vencimento=int(request.POST["dia_vencimento"]),
                        status=Contrato.Status.ATIVO,
                        responsavel=request.user,
                    )
                    messages.success(
                        request,
                        f"Cliente {cliente.nome_exibicao} atualizado! "
                        f"{contrato.numero_mensalidades} mensalidade(s) gerada(s) — "
                        f"contrato {contrato.numero_contrato}."
                    )
                else:
                    messages.success(request, f"Cliente {cliente.nome_exibicao} atualizado com sucesso!")

            return redirect("clientes:detalhe", pk=cliente.pk)
        else:
            messages.error(request, "Corrija os erros abaixo antes de salvar.")
    else:
        form = ClienteForm(instance=cliente)

    return render(request, "clientes/form.html", _contexto_form(form, editando=True, cliente=cliente))


@login_required
def cliente_detalhe(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    contratos = cliente.contratos.select_related("servico").order_by("-criado_em")
    return render(request, "clientes/detalhe.html", {
        "cliente": cliente,
        "contratos": contratos,
    })
