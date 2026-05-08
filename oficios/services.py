from django.db import transaction
from django.db.models import ProtectedError

from .models import Oficio


class OficioVinculadoError(Exception):
    """Exclusão bloqueada porque o ofício possui vínculos protegidos."""


@transaction.atomic
def criar_oficio(form):
    return form.save()


@transaction.atomic
def atualizar_oficio(instance, form):
    _ = instance
    return form.save()


@transaction.atomic
def criar_oficio_dados_viajantes(form):
    return form.save()


@transaction.atomic
def atualizar_oficio_dados_viajantes(oficio, form):
    _ = oficio
    return form.save()


def avaliar_oficio_dados_viajantes(oficio=None, form=None):
    if form is not None:
        values = _dados_viajantes_from_form(form)
    elif oficio is not None:
        values = _dados_viajantes_from_oficio(oficio)
    else:
        values = {}

    pendencias = []
    if not values.get("data_criacao"):
        pendencias.append("Informe a data de criação.")
    if not values.get("assunto"):
        pendencias.append("Informe o assunto.")
    if not values.get("motivo"):
        pendencias.append("Informe o motivo.")
    if not values.get("custeio"):
        pendencias.append("Informe o custeio.")
    if values.get("custeio") == Oficio.CUSTEIO_OUTRA_INSTITUICAO and not values.get("custeio_observacao"):
        pendencias.append("Informe a observação de custeio.")
    if not values.get("servidores_count"):
        pendencias.append("Selecione ao menos um viajante.")

    if not values.get("has_started"):
        status = "not_started"
    elif pendencias:
        status = "incomplete"
    else:
        status = "complete"
    return {"status": status, "pendencias": pendencias}


def _dados_viajantes_from_form(form):
    if form.is_bound:
        data = form.cleaned_data if form.is_valid() else form.data
        get_value = data.get
        servidores = (
            list(get_value("servidores") or [])
            if hasattr(data, "get")
            else []
        )
        if not servidores and hasattr(form.data, "getlist"):
            servidores = form.data.getlist("servidores")
        text_values = [
            get_value("assunto", ""),
            get_value("motivo", ""),
            get_value("protocolo", ""),
            get_value("custeio_observacao", ""),
        ]
        has_started = form.is_bound or any(str(value).strip() for value in text_values) or bool(servidores)
        return {
            "data_criacao": get_value("data_criacao"),
            "assunto": str(get_value("assunto", "") or "").strip(),
            "motivo": str(get_value("motivo", "") or "").strip(),
            "custeio": get_value("custeio"),
            "custeio_observacao": str(get_value("custeio_observacao", "") or "").strip(),
            "servidores_count": len(servidores),
            "has_started": has_started,
        }
    instance = getattr(form, "instance", None)
    return _dados_viajantes_from_oficio(instance) if instance and instance.pk else {}


def _dados_viajantes_from_oficio(oficio):
    if oficio is None:
        return {}
    text_values = [oficio.assunto, oficio.motivo, oficio.protocolo, oficio.custeio_observacao]
    servidores_count = oficio.servidores.count() if oficio.pk else 0
    return {
        "data_criacao": oficio.data_criacao,
        "assunto": oficio.assunto.strip(),
        "motivo": oficio.motivo.strip(),
        "custeio": oficio.custeio,
        "custeio_observacao": oficio.custeio_observacao.strip(),
        "servidores_count": servidores_count,
        "has_started": bool(oficio.pk) or any(value.strip() for value in text_values) or bool(servidores_count),
    }


@transaction.atomic
def excluir_oficio(instance):
    try:
        instance.delete()
    except ProtectedError as exc:
        raise OficioVinculadoError from exc


def build_oficio_document_payload(oficio):
    return {
        "numero": oficio.numero,
        "ano": oficio.ano,
        "numero_formatado": oficio.numero_formatado,
        "protocolo": oficio.protocolo,
        "assunto": oficio.assunto,
        "motivo": oficio.motivo,
        "data_criacao": oficio.data_criacao,
        "status": oficio.status,
        "roteiro": str(oficio.roteiro) if oficio.roteiro else "",
        "servidores": [servidor.nome for servidor in oficio.servidores.all()],
        "viatura": oficio.viatura.placa_formatada if oficio.viatura else "",
        "motorista": oficio.motorista.nome if oficio.motorista else "",
        "custeio": oficio.custeio,
    }
