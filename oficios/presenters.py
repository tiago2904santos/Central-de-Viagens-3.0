from core.presenters.actions import build_action
from core.presenters.actions import build_delete_action
from core.presenters.actions import build_edit_action
from core.presenters.meta import build_meta
from django.urls import reverse

from .models import Oficio


def _status_variant(status: str) -> str:
    if status == Oficio.STATUS_FINALIZADO:
        return "status-chip--success"
    if status == Oficio.STATUS_ARQUIVADO:
        return "status-chip--muted"
    return "status-chip--warning"


def apresentar_oficio_card(oficio):
    roteiro_label = str(oficio.roteiro) if oficio.roteiro else "Sem roteiro"
    solicitante_label = str(oficio.solicitante) if oficio.solicitante else "—"
    return {
        "number_label": "N° do Ofício",
        "number": oficio.numero_formatado,
        "status": oficio.get_status_display(),
        "status_class": _status_variant(oficio.status),
        "title": f"Ofício {oficio.numero_formatado}",
        "subtitle": oficio.assunto or "Sem assunto",
        "meta": [
            build_meta("Protocolo", oficio.protocolo or "—"),
            build_meta("Data criação", oficio.data_criacao.strftime("%d/%m/%Y")),
            build_meta("Roteiro", roteiro_label),
            build_meta("Solicitante", solicitante_label),
            build_meta("Viajantes", str(oficio.servidores.count())),
        ],
    }


def apresentar_pagina_detalhe_oficio(oficio):
    return {
        "status": oficio.get_status_display(),
        "status_class": _status_variant(oficio.status),
        "numero_formatado": oficio.numero_formatado,
        "protocolo": oficio.protocolo or "—",
        "assunto": oficio.assunto or "—",
        "motivo": oficio.motivo or "—",
        "data_criacao": oficio.data_criacao.strftime("%d/%m/%Y"),
        "roteiro": str(oficio.roteiro) if oficio.roteiro else "—",
        "solicitante": str(oficio.solicitante) if oficio.solicitante else "—",
        "servidores": [servidor.nome for servidor in oficio.servidores.all()],
        "viatura": oficio.viatura.placa_formatada if oficio.viatura else "—",
        "motorista": oficio.motorista.nome if oficio.motorista else "—",
        "custeio": oficio.get_custeio_display(),
        "custeio_observacao": oficio.custeio_observacao or "—",
    }


def apresentar_opcoes_documentais_oficio(oficio):
    _ = oficio
    return [
        {"label": "DOCX (em breve)", "enabled": False},
        {"label": "PDF (em breve)", "enabled": False},
    ]


def apresentar_acoes_oficio(*, detalhe_url: str, editar_url: str, excluir_url: str):
    return [
        action
        for action in [
            build_action("Abrir", detalhe_url),
            build_edit_action(editar_url),
            build_delete_action(excluir_url),
        ]
        if action
    ]


def apresentar_oficio_wizard_header(etapa_atual):
    titles = {
        "dados_viajantes": "Dados e viajantes",
        "transporte": "Transporte",
        "roteiro": "Roteiro e diárias",
        "resumo": "Resumo do ofício",
        "documentos": "Documentos",
    }
    return {
        "title": "Cadastro de ofício",
        "subtitle": titles.get(etapa_atual, "Dados e viajantes"),
    }


def apresentar_status_etapa_oficio(status):
    labels = {
        "not_started": "Não iniciada",
        "current": "Atual",
        "incomplete": "Incompleta",
        "complete": "Concluída",
        "locked": "Bloqueada",
    }
    return {
        "status": status,
        "label": labels.get(status, "Não iniciada"),
    }


def apresentar_oficio_wizard_steps(oficio=None, etapa_atual="dados_viajantes", dados_viajantes_status=None):
    dados_viajantes_status = dados_viajantes_status or "not_started"
    steps = [
        {"key": "dados_viajantes", "number": 1, "title": "Dados e viajantes"},
        {"key": "transporte", "number": 2, "title": "Transporte"},
        {"key": "roteiro", "number": 3, "title": "Roteiro e diárias"},
        {"key": "resumo", "number": 4, "title": "Resumo do ofício"},
        {"key": "documentos", "number": 5, "title": "Documentos"},
    ]
    for step in steps:
        if step["key"] == "dados_viajantes":
            step["url"] = reverse("oficios:dados_viajantes", args=[oficio.pk]) if oficio else ""
            step["state"] = "current" if etapa_atual == "dados_viajantes" else dados_viajantes_status
            step["completion_state"] = dados_viajantes_status
        else:
            step["url"] = ""
            step["state"] = "locked"
            step["completion_state"] = "locked"
        status_data = apresentar_status_etapa_oficio(step["completion_state"])
        step["state_label"] = status_data["label"]
    return steps

