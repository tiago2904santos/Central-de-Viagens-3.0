from django import forms

from core.normalizers import normalize_plate
from core.normalizers import normalize_spaces
from core.utils.masks import format_placa
from core.utils.masks import normalize_protocolo

from cadastros.models import Viatura

from .models import ModeloMotivoOficio
from .models import Oficio


class ServidorEquipeSelectMultiple(forms.SelectMultiple):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        servidor = getattr(value, "instance", None)
        if servidor is None:
            return option

        cargo = servidor.cargo.nome if servidor.cargo_id and servidor.cargo else ""
        unidade = str(servidor.unidade) if servidor.unidade_id and servidor.unidade else ""
        rg = servidor.rg_formatado or ""
        cpf = servidor.cpf_formatado or ""
        main_parts = [
            servidor.nome,
            f"RG {rg}" if rg else "",
            f"CPF {cpf}" if cpf else "",
            cargo,
        ]
        main = " • ".join(part for part in main_parts if part)
        search = " ".join(part for part in [servidor.nome, rg, cpf, cargo, unidade] if part)
        option["attrs"].update(
            {
                "data-cargo": cargo,
                "data-cpf": cpf,
                "data-main": main,
                "data-meta": unidade,
                "data-rg": rg,
                "data-search": search,
                "data-unidade": unidade,
            },
        )
        return option


class ServidorMotoristaSelect(forms.Select):
    """Select simples com metadados nos options (picker de busca no cliente)."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        servidor = getattr(value, "instance", None)
        if servidor is None:
            return option

        cargo = servidor.cargo.nome if servidor.cargo_id and servidor.cargo else ""
        unidade = str(servidor.unidade) if servidor.unidade_id and servidor.unidade else ""
        rg = servidor.rg_formatado or ""
        cpf = servidor.cpf_formatado or ""
        main_parts = [
            servidor.nome,
            f"RG {rg}" if rg else "",
            f"CPF {cpf}" if cpf else "",
            cargo,
        ]
        main = " • ".join(part for part in main_parts if part)
        search = " ".join(part for part in [servidor.nome, rg, cpf, cargo, unidade] if part)
        option["attrs"].update(
            {
                "data-cargo": cargo,
                "data-cpf": cpf,
                "data-main": main,
                "data-meta": unidade,
                "data-rg": rg,
                "data-search": search,
                "data-unidade": unidade,
            },
        )
        return option


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
        return super().clean()


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
            "servidores": ServidorEquipeSelectMultiple(
                attrs={
                    "class": "form-select app-multiselect__native",
                    "data-app-multiselect": "true",
                    "data-empty-selected": "Nenhum viajante selecionado.",
                    "data-empty-message": "Nenhum servidor encontrado.",
                    "data-placeholder": "Digite nome, RG ou CPF",
                    "data-search-placeholder": "Digite nome, RG ou CPF",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["modelo_motivo"].queryset = ModeloMotivoOficio.objects.order_by("ordem", "nome")
        self.fields["custeio"].required = False
        self.fields["servidores"].required = False

    def clean_protocolo(self):
        protocolo = normalize_protocolo(self.cleaned_data.get("protocolo", ""))
        if protocolo and len(protocolo) != 9:
            raise forms.ValidationError("Informe um protocolo válido com 9 dígitos.")
        return protocolo

    def clean_motivo(self):
        return normalize_spaces(self.cleaned_data.get("motivo", ""))

    def clean(self):
        return super().clean()


class OficioTransporteForm(forms.ModelForm):
    transporte_busca_ui = forms.CharField(
        label="BUSCAR VIATURA",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "data-oficio-viatura-busca": "true",
                "placeholder": "Digite placa, modelo, unidade ou motorista",
                "autocomplete": "off",
            },
        ),
    )

    porte_transporte_armas = forms.TypedChoiceField(
        label="Porte/transporte de armas",
        coerce=lambda v: v == "sim",
        choices=[("sim", "Sim"), ("nao", "Não")],
        widget=forms.Select(attrs={"class": "form-select", "data-oficio-porte-armas": "true"}),
    )

    class Meta:
        model = Oficio
        fields = [
            "viatura",
            "porte_transporte_armas",
            "transporte_placa_manual",
            "transporte_modelo_manual",
            "transporte_combustivel_manual",
            "transporte_tipo_manual",
            "motorista_modo",
            "motorista",
            "motorista_manual_nome",
            "motorista_manual_rg",
            "motorista_manual_cpf",
            "motorista_manual_cargo",
            "motorista_manual_unidade",
            "motorista_manual_observacao",
        ]
        widgets = {
            "viatura": forms.HiddenInput(attrs={"data-oficio-viatura-id": "true"}),
            "motorista_modo": forms.HiddenInput(attrs={"data-oficio-motorista-modo": "true"}),
            "transporte_placa_manual": forms.HiddenInput(attrs={"data-oficio-placa-hidden": "true"}),
            "transporte_modelo_manual": forms.TextInput(
                attrs={"class": "form-control", "data-oficio-viatura-modelo": "true", "data-mask": "upper"},
            ),
            "transporte_combustivel_manual": forms.Select(
                attrs={"class": "form-select", "data-oficio-viatura-combustivel": "true"},
            ),
            "transporte_tipo_manual": forms.Select(
                attrs={"class": "form-select", "data-oficio-viatura-tipo": "true"},
            ),
            "motorista": ServidorMotoristaSelect(
                attrs={
                    "class": "form-select app-motorista-picker__native",
                    "data-app-motorista-picker": "true",
                    "data-empty-selected": "Nenhum servidor selecionado.",
                    "data-empty-message": "Nenhum servidor encontrado.",
                    "data-placeholder": "Digite nome, RG ou CPF",
                    "data-panel-title": "MOTORISTA SELECIONADO",
                    "data-status-waiting": "Aguardando seleção",
                },
            ),
            "motorista_manual_nome": forms.TextInput(
                attrs={"class": "form-control", "data-mask": "upper", "data-oficio-motorista-manual": "true"},
            ),
            "motorista_manual_rg": forms.TextInput(attrs={"class": "form-control", "data-oficio-motorista-manual": "true"}),
            "motorista_manual_cpf": forms.TextInput(attrs={"class": "form-control", "data-oficio-motorista-manual": "true"}),
            "motorista_manual_cargo": forms.TextInput(
                attrs={"class": "form-control", "data-mask": "upper", "data-oficio-motorista-manual": "true"},
            ),
            "motorista_manual_unidade": forms.TextInput(
                attrs={"class": "form-control", "data-mask": "upper", "data-oficio-motorista-manual": "true"},
            ),
            "motorista_manual_observacao": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "data-oficio-motorista-manual": "true"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["viatura"].required = False
        self.fields["viatura"].empty_label = ""
        self.fields["motorista"].required = False
        self.fields["motorista"].empty_label = ""
        self.fields["transporte_combustivel_manual"].required = False
        self.fields["transporte_tipo_manual"].required = False
        self.fields["transporte_tipo_manual"].choices = [("", "---------")] + list(Viatura.TIPO_CHOICES)
        if not self.is_bound and self.instance.pk:
            self.initial.setdefault(
                "porte_transporte_armas",
                "sim" if self.instance.porte_transporte_armas else "nao",
            )
            if not self.instance.transporte_tipo_manual and not self.instance.viatura_id:
                self.initial.setdefault("transporte_tipo_manual", Viatura.TIPO_DESCARACTERIZADA)
        elif not self.is_bound:
            self.initial.setdefault("porte_transporte_armas", "sim")
            self.initial.setdefault("motorista_modo", Oficio.MOTORISTA_MODO_SERVIDOR)
            self.initial.setdefault("transporte_tipo_manual", Viatura.TIPO_DESCARACTERIZADA)

        if not self.is_bound and self.instance.pk:
            modo = self.instance.motorista_modo or Oficio.MOTORISTA_MODO_SERVIDOR
            self.initial.setdefault("motorista_modo", modo)
            if self.instance.viatura_id and self.instance.viatura:
                v = self.instance.viatura
                self.initial["transporte_placa_manual"] = v.placa
                self.initial["transporte_busca_ui"] = v.placa_formatada
                self.initial["transporte_modelo_manual"] = v.modelo or ""
                if v.combustivel_id:
                    self.initial["transporte_combustivel_manual"] = v.combustivel_id
                if v.tipo:
                    self.initial["transporte_tipo_manual"] = v.tipo
            elif (self.instance.transporte_placa_manual or "").strip():
                self.initial["transporte_busca_ui"] = format_placa(self.instance.transporte_placa_manual)
            if modo == Oficio.MOTORISTA_MODO_MANUAL:
                self.initial.setdefault("motorista_manual_nome", self.instance.motorista_manual_nome)
                self.initial.setdefault("motorista_manual_rg", self.instance.motorista_manual_rg)
                self.initial.setdefault("motorista_manual_cpf", self.instance.motorista_manual_cpf)
                self.initial.setdefault("motorista_manual_cargo", self.instance.motorista_manual_cargo)
                self.initial.setdefault("motorista_manual_unidade", self.instance.motorista_manual_unidade)
                self.initial.setdefault("motorista_manual_observacao", self.instance.motorista_manual_observacao)

    def clean_transporte_placa_manual(self):
        raw = self.cleaned_data.get("transporte_placa_manual", "") or ""
        normalized = normalize_plate(raw)
        viatura = self.cleaned_data.get("viatura")
        if viatura is not None:
            return normalized if normalized else ""
        if not normalized:
            return ""
        if len(normalized) != 7:
            raise forms.ValidationError("Use o formato de placa Mercosul ou antiga (7 caracteres).")
        return normalized

    def clean(self):
        data = super().clean()
        modo = data.get("motorista_modo") or Oficio.MOTORISTA_MODO_SERVIDOR
        if modo == Oficio.MOTORISTA_MODO_MANUAL:
            data["motorista"] = None
        else:
            for name in [
                "motorista_manual_nome",
                "motorista_manual_rg",
                "motorista_manual_cpf",
                "motorista_manual_cargo",
                "motorista_manual_unidade",
                "motorista_manual_observacao",
            ]:
                data[name] = ""
        data["motorista_manual_observacao"] = normalize_spaces(data.get("motorista_manual_observacao", "") or "")
        return data


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
