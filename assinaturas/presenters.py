from __future__ import annotations

from typing import Any

from django.urls import reverse

from assinaturas.models import AssinaturaDigital
from assinaturas.services.assinatura_artefato import assinatura_arquivo_esta_integra
from documentos.models import DocumentoArtefato


def assinatura_ultima_valida(artefato: DocumentoArtefato) -> AssinaturaDigital | None:
    return (
        AssinaturaDigital.objects.filter(artefato=artefato, status=AssinaturaDigital.STATUS_VALID)
        .order_by("-criado_em")
        .first()
    )


def assinatura_status_artefato(artefato: DocumentoArtefato) -> str:
    """
    sem_assinatura | valido | invalido | sem_registo
    """
    tem_ficheiro = bool(getattr(artefato.arquivo_assinado, "name", ""))
    tem_hash = bool((artefato.hash_sha256_assinado or "").strip())
    if not tem_ficheiro and not tem_hash:
        return "sem_assinatura"
    reg = assinatura_ultima_valida(artefato)
    if reg is None:
        return "sem_registo"
    if not assinatura_arquivo_esta_integra(reg):
        return "invalido"
    return "valido"


def assinatura_urls_artefato(artefato: DocumentoArtefato, *, request=None) -> dict[str, str]:
    reg = assinatura_ultima_valida(artefato)
    urls: dict[str, str] = {
        "assinar": reverse("assinaturas:assinatura-assinar-artefato", kwargs={"artefato_id": artefato.pk}),
        "pdf_original": reverse(
            "assinaturas:assinatura-artefato-pdf-original",
            kwargs={"artefato_id": artefato.pk},
        ),
        "verificar": "",
        "pdf_assinado": "",
    }
    if reg is not None:
        urls["verificar"] = reverse(
            "assinaturas:assinatura-verificar-codigo",
            kwargs={"codigo": reg.codigo_verificacao},
        )
        urls["pdf_assinado"] = reverse(
            "assinaturas:assinatura-pdf-assinado",
            kwargs={"assinatura_id": reg.pk},
        )
    if request is not None:
        return {k: (request.build_absolute_uri(v) if v else "") for k, v in urls.items()}
    return urls
