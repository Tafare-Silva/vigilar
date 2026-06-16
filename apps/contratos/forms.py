from django import forms
from django.utils import timezone
from apps.clientes.models import Cliente
from apps.servicos.models import Servico
from .models import Contrato


class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            'cliente', 'servico', 'data_inicio',
            'numero_mensalidades', 'valor_mensal',
            'dia_vencimento', 'desconto', 'observacoes',
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(
            status__in=['ativo', 'inadimplente', 'suspenso']
        ).order_by('nome')
        self.fields['servico'].queryset = Servico.objects.filter(ativo=True).order_by('nome')
        self.fields['desconto'].required = False
        self.fields['observacoes'].required = False

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-input form-select'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-input'
            else:
                field.widget.attrs['class'] = 'form-input'

        self.fields['data_inicio'].initial = timezone.now().date()
        self.fields['numero_mensalidades'].widget.attrs.update({'min': 1, 'max': 120, 'placeholder': '12'})
        self.fields['valor_mensal'].widget.attrs['placeholder'] = '0,00'
        self.fields['desconto'].widget.attrs['placeholder'] = '0,00'
