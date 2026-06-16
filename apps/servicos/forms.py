from django import forms
from .models import Servico


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = [
            'nome', 'codigo', 'tipo', 'descricao',
            'valor_mensal', 'duracao_minima_meses',
            'frequencia_rondas_semana', 'horario_inicio', 'horario_fim',
            'ativo', 'ordem',
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-input form-select'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-input'
            elif isinstance(field.widget, forms.CheckboxInput):
                pass
            else:
                field.widget.attrs['class'] = 'form-input'

        self.fields['codigo'].required = False
        self.fields['descricao'].required = False
        self.fields['frequencia_rondas_semana'].required = False
        self.fields['horario_inicio'].required = False
        self.fields['horario_fim'].required = False
        self.fields['ordem'].required = False

        self.fields['nome'].widget.attrs['placeholder'] = 'Ex: Ronda Residencial Básica'
        self.fields['codigo'].widget.attrs['placeholder'] = 'Ex: RRB-01 (opcional)'
        self.fields['valor_mensal'].widget.attrs['placeholder'] = '0,00'
        self.fields['duracao_minima_meses'].widget.attrs['placeholder'] = '12'
        self.fields['frequencia_rondas_semana'].widget.attrs['placeholder'] = '0'
        self.fields['ordem'].widget.attrs['placeholder'] = '0'
