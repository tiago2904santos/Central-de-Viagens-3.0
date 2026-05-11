from __future__ import annotations

import hashlib
from typing import Any, Mapping

from django.conf import settings
from django.core.files.base import ContentFile

from documentos.models import DocumentoArtefato
from documentos.services.facade import DocumentoGerado
from documentos.services.timing import measure_step


def persist_geracao(
    doc: DocumentoGerado,
    *,
    oficio_id: int | None = None,
    servidor_id: int | None = None,
    payload_snapshot: Mapping[str, Any] | None = None,
    cache_key: str = "",
    engine: str = "",
    generator_version: str = "",
) -> DocumentoArtefato | None:
    if not getattr(settings, "DOCUMENTOS_PERSIST_ARTEFATOS", False):
        return None
    nome = doc.nome_arquivo
    arquivo = ContentFile(doc.conteudo, name=nome)
    payload_snapshot = dict(payload_snapshot or {})
    gen_ver = generator_version or str(getattr(settings, "DOCUMENTOS_GENERATOR_VERSION", "1") or "1")
    with measure_step(
        "persist_geracao",
        {
            "tipo": doc.tipo.value,
            "formato": doc.formato.value,
            "oficio_id": oficio_id,
            "servidor_id": servidor_id,
        },
    ):
        return DocumentoArtefato.objects.create(
            tipo=doc.tipo.value,
            formato=doc.formato.value,
            oficio_id=oficio_id,
            servidor_id=servidor_id,
            payload_snapshot=payload_snapshot,
            hash_sha256=doc.hash_sha256,
            arquivo=arquivo,
            assinatura_backend="",
            cache_key=cache_key or "",
            engine=engine or "",
            generator_version=gen_ver,
        )


def atualizar_apos_assinatura(
    artefato: DocumentoArtefato,
    *,
    pdf_assinado: bytes,
    backend: str,
) -> DocumentoArtefato:
    digest = hashlib.sha256(pdf_assinado).hexdigest()
    nome = f"assinado_{artefato.pk}.pdf"
    artefato.arquivo_assinado.save(nome, ContentFile(pdf_assinado), save=False)
    artefato.hash_sha256_assinado = digest
    artefato.assinatura_backend = backend
    from django.utils import timezone

    artefato.assinado_em = timezone.now()
    artefato.save(
        update_fields=[
            "arquivo_assinado",
            "hash_sha256_assinado",
            "assinatura_backend",
            "assinado_em",
        ],
    )
    return artefato
