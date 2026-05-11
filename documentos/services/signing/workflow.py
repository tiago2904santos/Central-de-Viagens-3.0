"""Fluxo de assinatura de artefatos (reutilizável por views de página e download)."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from assinaturas.services.recording import registrar_assinatura_concluida

from documentos.models import DocumentoArtefato
from documentos.services.access import ensure_request_may_view_artefato_pdf
from documentos.services.persistence import atualizar_apos_assinatura
from documentos.services.signing import assinar_pdf_final


def assinar_artefato_pdf(request: HttpRequest, artefato: DocumentoArtefato) -> dict[str, Any]:
    """
    Valida permissão, assina o PDF original, persiste `arquivo_assinado` e regista auditoria.

    Retorno inclui bytes assinados e metadados do motor para respostas HTTP ou mensagens.
    """
    ensure_request_may_view_artefato_pdf(request, artefato)
    pdf_bytes = artefato.arquivo.read()
    signed, meta = assinar_pdf_final(pdf_bytes)
    atualizar_apos_assinatura(artefato, pdf_assinado=signed, backend=str(meta.get("backend", "")))
    registrar_assinatura_concluida(artefato, meta)
    return {"pdf_bytes": signed, "meta": meta, "backend": str(meta.get("backend", ""))}
