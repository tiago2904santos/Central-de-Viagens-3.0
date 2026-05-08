from core.presenters.actions import build_action
from core.presenters.actions import build_delete_action
from core.presenters.actions import build_edit_action
from core.presenters.meta import build_meta

from .models import Oficio


def _status_variant(status: str) -> str:
    if status == Oficio.STATUS_FINALIZADO:
        return "status-chip--success"
    if status == Oficio.STATUS_ARQUIVADO:
        return "status-chip--muted"
    return "status-chip--warning"


def apresentar_oficio_card(oficio):
    roteiro_label = str(oficio.roteiro) if oficio.roteiro else "Sem roteiro"
    return {
        "status": oficio.get_status_display(),
        "status_class": _status_variant(oficio.status),
        "title": f"Ofício {oficio.numero_formatado}",
        "subtitle": oficio.assunto or "Sem assunto",
        "meta": [
            build_meta("Protocolo", oficio.protocolo or "—"),
            build_meta("Data", oficio.data_criacao.strftime("%d/%m/%Y")),
            build_meta("Roteiro", roteiro_label),
            build_meta("Servidores", str(oficio.servidores.count())),
            build_meta("Viatura", oficio.viatura.placa_formatada if oficio.viatura else "—"),
            build_meta("Motorista", oficio.motorista.nome if oficio.motorista else "—"),
            build_meta("Custeio", oficio.get_custeio_display()),
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
