from core.presenters.actions import build_action
from core.presenters.actions import build_delete_action
from core.presenters.actions import build_edit_action
from core.presenters.badges import build_badge
from core.presenters.meta import build_meta
from core.utils.masks import format_placa
from core.utils.masks import format_protocolo
from django.urls import reverse

from .models import Oficio


def _status_variant(status: str) -> str:
    if status in {Oficio.STATUS_GERADO, Oficio.STATUS_FINALIZADO}:
        return "status-chip--success"
    if status == Oficio.STATUS_ARQUIVADO:
        return "status-chip--muted"
    return "status-chip--warning"


def apresentar_oficio_card(oficio):
    return {
        "number_label": "N° do Ofício",
        "number": oficio.numero_formatado,
        "status": oficio.get_status_display(),
        "status_class": _status_variant(oficio.status),
        "title": f"Ofício {oficio.numero_formatado}",
        "subtitle": oficio.motivo[:120] if oficio.motivo else "Sem motivo",
        "meta": [
            build_meta("Protocolo", format_protocolo(oficio.protocolo) or "—"),
            build_meta("Data criação", oficio.data_criacao.strftime("%d/%m/%Y")),
            build_meta("Custeio", oficio.get_custeio_display()),
            build_meta("Viajantes", str(oficio.servidores.count())),
        ],
    }


def apresentar_pagina_detalhe_oficio(oficio):
    viatura_label = "—"
    if oficio.viatura_id:
        viatura_label = oficio.viatura.placa_formatada
    elif (oficio.transporte_placa_manual or "").strip():
        viatura_label = format_placa(oficio.transporte_placa_manual)
    motorista_label = "—"
    if oficio.motorista_id:
        motorista_label = oficio.motorista.nome
    elif oficio.motorista_modo == Oficio.MOTORISTA_MODO_MANUAL and (oficio.motorista_manual_nome or "").strip():
        motorista_label = oficio.motorista_manual_nome.strip()
    return {
        "status": oficio.get_status_display(),
        "status_class": _status_variant(oficio.status),
        "numero_formatado": oficio.numero_formatado,
        "protocolo": format_protocolo(oficio.protocolo) or "—",
        "motivo": oficio.motivo or "—",
        "data_criacao": oficio.data_criacao.strftime("%d/%m/%Y"),
        "servidores": [servidor.nome for servidor in oficio.servidores.all()],
        "viatura": viatura_label,
        "motorista": motorista_label,
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
        "justificativa": "Justificativa",
        "documentos": "Documentos",
        "resumo": "Documentos",
    }
    return {
        "title": "Cadastro de ofício",
        "subtitle": titles.get(etapa_atual, "Dados e viajantes"),
    }


def _map_justificativa_etapa_para_completion(etapa: dict) -> str:
    st = etapa.get("status") or ""
    if st == "not_required":
        return "complete"
    if st == "not_started":
        return "not_started"
    if st == "incomplete":
        return "incomplete"
    if st == "complete":
        return "complete"
    return "not_started"


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


def apresentar_oficio_wizard_steps(
    oficio=None,
    etapa_atual="dados_viajantes",
    dados_viajantes_status=None,
    transporte_status=None,
    roteiro_status=None,
    justificativa_status=None,
    documentos_status=None,
):
    dados_viajantes_status = dados_viajantes_status or "not_started"
    transporte_status = transporte_status or "not_started"
    roteiro_status = roteiro_status or "not_started"
    if oficio is not None and justificativa_status is None:
        from justificativas.services import avaliar_etapa_justificativa_oficio

        justificativa_status = _map_justificativa_etapa_para_completion(
            avaliar_etapa_justificativa_oficio(oficio)
        )
    else:
        justificativa_status = justificativa_status or "not_started"
    documentos_status = documentos_status or "not_started"
    steps = [
        {"key": "dados_viajantes", "number": 1, "title": "Dados e viajantes"},
        {"key": "transporte", "number": 2, "title": "Transporte"},
        {"key": "roteiro", "number": 3, "title": "Roteiro e diárias"},
        {"key": "justificativa", "number": 4, "title": "Justificativa"},
        {"key": "documentos", "number": 5, "title": "Documentos"},
    ]
    for step in steps:
        key = step["key"]
        if key == "dados_viajantes":
            step["url"] = reverse("oficios:dados_viajantes", args=[oficio.pk]) if oficio else ""
            step["state"] = "current" if etapa_atual == key else dados_viajantes_status
            step["completion_state"] = dados_viajantes_status
        elif key == "transporte":
            step["url"] = reverse("oficios:transporte", args=[oficio.pk]) if oficio else ""
            step["state"] = "current" if etapa_atual == key else transporte_status
            step["completion_state"] = transporte_status
        elif key == "roteiro":
            step["url"] = reverse("oficios:wizard_roteiro", args=[oficio.pk]) if oficio else ""
            step["state"] = "current" if etapa_atual == key else roteiro_status
            step["completion_state"] = roteiro_status
        elif key == "justificativa":
            step["url"] = reverse("oficios:wizard_justificativa", args=[oficio.pk]) if oficio else ""
            step["state"] = "current" if etapa_atual == key else justificativa_status
            step["completion_state"] = justificativa_status
        elif key == "documentos":
            step["url"] = reverse("oficios:wizard_resumo", args=[oficio.pk]) if oficio else ""
            step["state"] = "current" if etapa_atual == key else documentos_status
            step["completion_state"] = documentos_status
        else:
            step["url"] = ""
            step["state"] = "locked"
            step["completion_state"] = "locked"
        status_data = apresentar_status_etapa_oficio(step["completion_state"])
        step["state_label"] = status_data["label"]
    return steps


def apresentar_oficio_wizard_summary(oficio):
    if oficio is None:
        raise ValueError("Cadastro de oficio exige um rascunho persistido.")

    return {
        "numero_label": oficio.numero_formatado,
        "data_criacao_label": oficio.data_criacao.strftime("%d/%m/%Y"),
        "status_label": oficio.get_status_display(),
        "status_state": str(oficio.status or "").lower(),
    }


def apresentar_modelo_motivo_card(modelo):
    texto = (modelo.texto or "").strip()
    if len(texto) > 140:
        texto = f"{texto[:140]}..."
    return {
        "id": modelo.pk,
        "nome": modelo.nome,
        "is_padrao": modelo.is_padrao,
        "texto_preview": texto or "—",
        "editar_url": reverse("oficios:modelo_motivo_editar", args=[modelo.pk]),
        "excluir_url": reverse("oficios:modelo_motivo_excluir", args=[modelo.pk]),
    }


def apresentar_linha_lista_simples_modelo_motivo(modelo, edit_url="#", delete_url="#"):
    badges = []
    if modelo.is_padrao:
        badges.append(build_badge("Padrão", "accent"))
    texto = (modelo.texto or "").strip()
    if len(texto) > 90:
        texto = f"{texto[:90]}..."
    return {
        "title": modelo.nome,
        "badges": badges,
        "meta": [
            build_meta("Prévia", texto or "—"),
        ],
        "edit_url": edit_url,
        "delete_url": delete_url,
    }

