"""Geração do documento de plano de trabalho (payload canónico + modelo DOCX legado)."""

from __future__ import annotations

import logging

from documentos.services.facade import build_default_facade
from documentos.services.persistence import persist_geracao
from documentos.services.responses import build_download_response
from documentos.services.types import DocumentoFormato
from documentos.services.types import DocumentoTipo

from oficios.documents import build_canonical_document_payload
from oficios.models import Oficio

logger = logging.getLogger(__name__)


def gerar_resposta_plano_trabalho_documento(oficio: Oficio, formato: DocumentoFormato):
    """
    Modelo `plano_trabalho.docx` usa placeholders aninhados (ex.: ``{{ oficio.numero_formatado }}``).
    O contexto passado ao docxtpl é o payload canónico; não é necessário ``docxtpl_context`` plano.
    """
    payload = build_canonical_document_payload(oficio, DocumentoTipo.PLANO_TRABALHO)
    facade = build_default_facade()
    reference = f"{oficio.numero_formatado.replace('/', '-')}-plano-trabalho"
    doc = facade.gerar(
        tipo=DocumentoTipo.PLANO_TRABALHO,
        formato=formato,
        payload=payload,
        reference=reference,
    )
    response = build_download_response(
        content=doc.conteudo,
        tipo=DocumentoTipo.PLANO_TRABALHO,
        formato=formato,
        reference=reference,
    )
    response["X-Document-SHA256"] = doc.hash_sha256
    try:
        persist_geracao(doc, oficio_id=oficio.pk, payload_snapshot=payload)
    except Exception:
        logger.exception("Não foi possível persistir artefato de plano de trabalho.")
    return response
