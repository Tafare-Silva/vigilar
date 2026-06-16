"""
apps/core/forms.py
------------------
Formulários do módulo core.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Empresa


class EmpresaForm(forms.ModelForm):

    class Meta:
        model = Empresa
        fields = [
            "nome", "cnpj", "inscricao_estadual",
            "telefone", "celular", "email", "site",
            "logradouro", "numero", "complemento",
            "bairro", "cidade", "estado", "cep",
            "logo", "rodape_recibo",
        ]
        widgets = {
            "rodape_recibo": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-input")
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.setdefault("class", "form-input")
            else:
                field.widget.attrs.setdefault("class", "form-input")

        placeholders = {
            "nome": "Ex: C.R.S Segurança Ltda.",
            "cnpj": "00.000.000/0001-00",
            "inscricao_estadual": "Inscrição estadual",
            "telefone": "(00) 0000-0000",
            "celular": "(00) 00000-0000",
            "email": "contato@empresa.com.br",
            "site": "https://www.empresa.com.br",
            "logradouro": "Rua, Avenida…",
            "numero": "Nº",
            "complemento": "Sala, Bloco…",
            "bairro": "Bairro",
            "cidade": "Cidade",
            "cep": "00000-000",
            "rodape_recibo": "Ex: Obrigado pela confiança! Dúvidas: (00) 0000-0000",
        }
        for fname, ph in placeholders.items():
            if fname in self.fields:
                self.fields[fname].widget.attrs["placeholder"] = ph

        # Todos os campos são opcionais exceto o nome
        for fname in self.fields:
            if fname != "nome":
                self.fields[fname].required = False
