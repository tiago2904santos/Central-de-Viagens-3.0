from django import forms

from core.normalizers import normalize_spaces
from core.utils.masks import normalize_protocolo

from .models import ModeloMotivoOficio
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
        for optional_field in ("roteiro", "solicitante", "viatura", "motorista", "servidores"):
            if optional_field in self.fields:
                self.fields[optional_field].required = False

    def clean_protocolo(self):
        return normalize_protocolo(self.cleaned_data.get("protocolo", ""))

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


class OficioDadosViajantesForm(OficioForm):
    modelo_motivo = forms.ModelChoiceField(
        label="Modelo de motivo",
        queryset=ModeloMotivoOficio.objects.none(),
        required=False,
        empty_label="Selecione um modelo (opcional)",
        widget=forms.Select(attrs={"class": "form-select", "data-modelo-motivo-select": "true"}),
    )

    class Meta(OficioForm.Meta):
        fields = [
            "protocolo",
            "motivo",
            "custeio",
            "custeio_observacao",
            "servidores",
        ]
        widgets = {
            "protocolo": forms.TextInput(attrs={"class": "form-control", "data-mask": "protocolo"}),
            "motivo": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "data-motivo-textarea": "true"},
            ),
            "custeio": forms.Select(attrs={"class": "form-select"}),
            "custeio_observacao": forms.TextInput(attrs={"class": "form-control"}),
            "servidores": forms.SelectMultiple(
                attrs={"class": "form-select", "size": "8", "data-filterable-multiselect-native": "true"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["modelo_motivo"].queryset = ModeloMotivoOficio.objects.order_by("ordem", "nome")

    def clean_protocolo(self):
        protocolo = normalize_protocolo(self.cleaned_data.get("protocolo", ""))
        if protocolo and len(protocolo) != 9:
            raise forms.ValidationError("Informe um protocolo válido com 9 dígitos.")
        return protocolo

    def clean_motivo(self):
        motivo = normalize_spaces(self.cleaned_data.get("motivo", ""))
        if not motivo:
            raise forms.ValidationError("Informe o motivo.")
        return motivo

    def clean(self):
        cleaned_data = super().clean()
        servidores = cleaned_data.get("servidores")
        if not servidores:
            self.add_error("servidores", "Selecione ao menos um viajante.")
        return cleaned_data


class ModeloMotivoOficioForm(forms.ModelForm):
    nome = forms.CharField(
        label="Nome",
        help_text="Use um nome curto para identificar o modelo.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    texto = forms.CharField(
        label="Texto do modelo",
        help_text="Este texto será copiado para o motivo do ofício e poderá ser editado antes de salvar.",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )
    is_padrao = forms.BooleanField(
        label="Modelo padrão",
        required=False,
        help_text="Marque apenas se este modelo deve ser sugerido como principal.",
        widget=forms.CheckboxInput(attrs={"class": "app-card-toggle__input"}),
    )

    class Meta:
        model = ModeloMotivoOficio
        fields = ["nome", "texto", "is_padrao"]
