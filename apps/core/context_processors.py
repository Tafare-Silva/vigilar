"""Context processors globais — injetados em todos os templates."""
from django.conf import settings
from django.core.cache import cache


def configuracoes_globais(request):
    dados = cache.get("empresa_config")

    if dados is None:
        try:
            from apps.core.models import Empresa
            e = Empresa.objects.get(pk=1)
            dados = {
                "nome": e.nome,
                "cnpj": e.cnpj,
                "telefone": e.telefone or e.celular,
                "logo_url": e.logo.url if e.logo else None,
                "rodape_recibo": e.rodape_recibo,
                "empresa": e,
            }
        except Exception:
            dados = {
                "nome": getattr(settings, "NOME_EMPRESA", ""),
                "cnpj": getattr(settings, "CNPJ_EMPRESA", ""),
                "telefone": getattr(settings, "TELEFONE_EMPRESA", ""),
                "logo_url": None,
                "rodape_recibo": "",
                "empresa": None,
            }
        cache.set("empresa_config", dados, 300)

    return {
        "NOME_EMPRESA": dados["nome"],
        "CNPJ_EMPRESA": dados["cnpj"],
        "TELEFONE_EMPRESA": dados["telefone"],
        "LOGO_EMPRESA": dados["logo_url"],
        "RODAPE_RECIBO": dados["rodape_recibo"],
        "EMPRESA": dados["empresa"],
    }
