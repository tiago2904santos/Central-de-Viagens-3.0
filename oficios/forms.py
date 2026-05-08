from django import forms

from core.normalizers import normalize_spaces
from core.normalizers import normalize_upper

from .models import Oficio


class OficioForm(forms.ModelForm):
    class Meta:
        model = Oficio
        fields = [
            "numero",
            "ano",
            "data_criacao",
            "protocolo",
            "assunto",
            "motivo",
            "status",
            "roteiro",
            "solicitante",
            "servidores",
            "viatura",
            "motorista",
            "custeio",
            "custeio_observacao",
        ]
        widgets = {
            "data_criacao": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "motivo": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "roteiro": forms.Select(attrs={"class": "form-select"}),
            "solicitante": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "servidores": forms.SelectMultiple(attrs={"class": "form-select", "size": "8"}),
            "viatura": forms.Select(attrs={"class": "form-select"}),
            "motorista": forms.Select(attrs={"class": "form-select"}),
            "custeio": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput)):
                field.widget.attrs.setdefault("class", "form-control")
            if field_name in {"protocolo", "assunto"}:
                field.widget.attrs.setdefault("data-mask", "upper")
        self.fields["roteiro"].required = False
        self.fields["solicitante"].required = False
        self.fields["viatura"].required = False
        self.fields["motorista"].required = False
        self.fields["servidores"].required = False

    def clean_protocolo(self):
        return normalize_upper(self.cleaned_data.get("protocolo", ""))

    def clean_assunto(self):
        return normalize_spaces(self.cleaned_data.get("assunto", ""))

    def clean_motivo(self):
        return normalize_spaces(self.cleaned_data.get("motivo", ""))

    def clean_custeio_observacao(self):
        return normalize_spaces(self.cleaned_data.get("custeio_observacao", ""))

    def clean(self):
        cleaned_data = super().clean()
        custeio = cleaned_data.get("custeio")
        observacao = cleaned_data.get("custeio_observacao", "")
        if custeio == Oficio.CUSTEIO_OUTRA_INSTITUICAO and not observacao:
            self.add_error(
                "custeio_observacao",
                "Informe a observação quando o custeio for de outra instituição.",
            )
        return cleaned_data
