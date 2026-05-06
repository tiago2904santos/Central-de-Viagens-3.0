from django.urls import reverse

from core.presenters.actions import build_delete_action
from core.presenters.actions import build_edit_action
from core.presenters.actions import build_open_action
from . import roteiro_logic
from .models import Roteiro


def _label_cidade_uf(cidade, estado):
    if cidade:
        uf = cidade.estado.sigla if getattr(cidade, "estado", None) else getattr(cidade, "uf", "")
        return f"{cidade.nome}/{uf}"
    if estado:
        return estado.sigla
    return "—"


def _periodo_resumo(roteiro):
    pontos = [
        p
        for p in [
            getattr(roteiro, "saida_dt", None),
            getattr(roteiro, "chegada_dt", None),
            getattr(roteiro, "retorno_saida_dt", None),
            getattr(roteiro, "retorno_chegada_dt", None),
        ]
        if p
    ]
    if not pontos:
        return "Período a definir"
    inicio = min(pontos)
    fim = max(pontos)
    return f"{inicio:%d/%m/%Y %H:%M} até {fim:%d/%m/%Y %H:%M}"


def _format_trecho_dt(dt):
    if not dt:
        return "—"
    return f"{dt:%d/%m/%Y %H:%M}"


def apresentar_roteiro_card(roteiro):
    origem_txt = _label_cidade_uf(roteiro.origem_cidade, roteiro.origem_estado)
    destinos_todos = list(roteiro.destinos.all()) if roteiro.pk else []
    destino_principal_txt = "—"
    if destinos_todos:
        primeiro = destinos_todos[0]
        destino_principal_txt = _label_cidade_uf(primeiro.cidade, primeiro.estado)

    if destino_principal_txt != "—":
        titulo_rota = f"{origem_txt} → {destino_principal_txt}"
    else:
        titulo_rota = origem_txt if origem_txt != "—" else f"Roteiro #{roteiro.pk}"

    if destinos_todos:
        destino_txt = ", ".join(_label_cidade_uf(d.cidade, d.estado) for d in destinos_todos)
    else:
        destino_txt = "—"

    detail_url = reverse("roteiros:detalhe", args=[roteiro.pk])
    edit_url = reverse("roteiros:editar", args=[roteiro.pk])
    delete_url = reverse("roteiros:excluir", args=[roteiro.pk])
    qtd = getattr(roteiro, "trechos_count", None)
    if qtd is None:
        qtd = roteiro.trechos.count()

    status = roteiro.get_status_display() if hasattr(roteiro, "get_status_display") else roteiro.status
    status_code = getattr(roteiro, "status", "") or ""
    if status_code == Roteiro.STATUS_FINALIZADO:
        status_chip_class = "status-chip--completed"
        status_variant = "finalizado"
    elif status_code == Roteiro.STATUS_RASCUNHO:
        status_chip_class = "status-chip--draft"
        status_variant = "rascunho"
    else:
        status_chip_class = "status-chip--muted"
        status_variant = "outro"

    trechos_payload = []
    for trecho in roteiro.trechos.all():
        orig_t = _label_cidade_uf(trecho.origem_cidade, trecho.origem_estado)
        dest_t = _label_cidade_uf(trecho.destino_cidade, trecho.destino_estado)
        trechos_payload.append(
            {
                "rota": f"{orig_t} → {dest_t}",
                "saida": _format_trecho_dt(trecho.saida_dt),
                "chegada": _format_trecho_dt(trecho.chegada_dt),
            }
        )

    diarias_txt = (roteiro.quantidade_diarias or "").strip() or "—"

    return {
        "title": titulo_rota,
        "subtitle": "Roteiro reutilizável para documentos",
        "status": status,
        "status_chip_class": status_chip_class,
        "status_variant": status_variant,
        "meta": [
            {"label": "Sede", "value": origem_txt},
            {"label": "Destinos", "value": destino_txt},
            {"label": "Período", "value": _periodo_resumo(roteiro)},
            {"label": "Trechos", "value": str(qtd)},
            {"label": "Diárias", "value": diarias_txt},
        ],
        "trechos": trechos_payload,
        "actions": [build_open_action(detail_url), build_edit_action(edit_url), build_delete_action(delete_url)],
    }


def apresentar_contexto_formulario_roteiro_avulso(
    *,
    evento,
    form,
    obj,
    destinos_atuais,
    trechos_list,
    step3_state,
    route_options,
):
    """Contexto do wizard de roteiro avulso (dict para template); sem HTML."""
    return roteiro_logic._build_roteiro_form_context(
        evento=evento,
        form=form,
        obj=obj,
        destinos_atuais=destinos_atuais,
        trechos_list=trechos_list,
        is_avulso=True,
        step3_state=step3_state,
        route_options=route_options,
    )


def apresentar_pagina_detalhe_roteiro(roteiro, trechos):
    pk = roteiro.pk
    destinos = list(roteiro.destinos.all())
    destinos_detalhe = [
        {"ordem": idx + 1, "label": _label_cidade_uf(d.cidade, d.estado)}
        for idx, d in enumerate(destinos)
    ]
    return {
        "page_title": f"Roteiro #{pk}",
        "page_description": "Resumo do roteiro, trechos e diárias calculadas.",
        "roteiro": roteiro,
        "trechos": trechos,
        "destinos_detalhe": destinos_detalhe,
        "edit_url": reverse("roteiros:editar", args=[pk]),
        "delete_url": reverse("roteiros:excluir", args=[pk]),
        "back_url": reverse("roteiros:index"),
    }
