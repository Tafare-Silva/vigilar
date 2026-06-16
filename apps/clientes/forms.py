"""
apps/clientes/forms.py
----------------------
Formulário de cadastro e edição de clientes.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Cliente


class ClienteForm(forms.ModelForm):

    class Meta:
        model = Cliente
        fields = [
            # Identificação
            "tipo_pessoa",
            "nome", "cpf", "rg", "data_nascimento",
            "razao_social", "nome_fantasia", "cnpj", "inscricao_estadual",
            # Contato
            "email", "telefone", "celular", "whatsapp",
            # Endereço
            "cep", "logradouro", "numero", "complemento",
            "bairro", "cidade", "estado", "ponto_referencia",
            # Controle
            "status", "observacoes",
        ]
        widgets = {
            "tipo_pessoa": forms.RadioSelect(),
            "data_nascimento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
            "whatsapp": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classe form-input em todos os campos (exceto radio/checkbox)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.RadioSelect, forms.CheckboxInput)):
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-input form-select")
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-input")
            else:
                field.widget.attrs.setdefault("class", "form-input")

        # Placeholders
        placeholders = {
            "nome": "Nome completo",
            "cpf": "000.000.000-00",
            "rg": "00.000.000-0",
            "razao_social": "Razão social da empresa",
            "nome_fantasia": "Nome fantasia (opcional)",
            "cnpj": "00.000.000/0001-00",
            "inscricao_estadual": "Inscrição estadual",
            "email": "email@exemplo.com.br",
            "telefone": "(00) 0000-0000",
            "celular": "(00) 00000-0000",
            "cep": "00000-000",
            "logradouro": "Rua, Avenida, etc.",
            "numero": "Nº",
            "complemento": "Apto, Bloco, Casa…",
            "bairro": "Bairro",
            "cidade": "Cidade",
            "ponto_referencia": "Ex: Próximo ao mercado…",
            "observacoes": "Informações adicionais sobre o cliente…",
        }
        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["placeholder"] = placeholder

        # Campos não obrigatórios no form (validação condicional no clean)
        optional_fields = [
            "cpf", "rg", "data_nascimento",
            "razao_social", "nome_fantasia", "cnpj", "inscricao_estadual",
            "email", "telefone", "celular",
            "cep", "logradouro", "numero", "complemento",
            "bairro", "cidade", "estado", "ponto_referencia",
            "observacoes",
        ]
        for f in optional_fields:
            if f in self.fields:
                self.fields[f].required = False

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo_pessoa")

        if tipo == Cliente.TipoPessoa.FISICA:
            if not cleaned.get("cpf"):
                self.add_error("cpf", _("CPF é obrigatório para Pessoa Física."))
        elif tipo == Cliente.TipoPessoa.JURIDICA:
            if not cleaned.get("razao_social"):
                self.add_error("razao_social", _("Razão social é obrigatória para Pessoa Jurídica."))
            if not cleaned.get("cnpj"):
                self.add_error("cnpj", _("CNPJ é obrigatório para Pessoa Jurídica."))

        return cleaned

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf", "")
        return cpf or None

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj", "")
        if not cnpj:
            return cnpj
        qs = Cliente.todos.filter(cnpj=cnpj)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("Já existe um cliente com este CNPJ."))
        return cnpj
