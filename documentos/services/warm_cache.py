"""
Pré-materialização de artefatos (ex.: PDF) quando o ofício está completo — sem Celery.
"""

from __future__ import annotations

import logging

from django.conf import settings

from documentos.services.types import DocumentoFormato
from documentos.services.types import DocumentoTipo

logger = logging.getLogger(__name__)


def ensure_document_artifact_cached(oficio, *, tipo: DocumentoTipo = DocumentoTipo.OFICIO) -> None:
    """
    Garante PDF em cache para o ofício completo (best-effort; falhas de motor não rebentam a view).
    """
    if not getattr(settings, "DOCUMENTOS_PREGENERATE_PDF", True):
        return None
    from oficios.services import validar_oficio_para_documento

    if validar_oficio_para_documento(oficio).get("pendencias"):
        return None
    try:
        if tipo == DocumentoTipo.OFICIO:
            from oficios.services import gerar_resposta_documento_oficio

            gerar_resposta_documento_oficio(oficio, DocumentoFormato.PDF)
    except Exception:
        logger.warning(
            "Pré-geração PDF ignorada (motor ou dados). O download tentará de novo.",
            exc_info=True,
        )
    return None
