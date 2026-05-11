from __future__ import annotations

from documentos.models import DocumentoArtefato


def get_latest_artefato_pdf_for_oficio(oficio_id: int, tipo: str) -> DocumentoArtefato | None:
    """Último artefato PDF persistido para o ofício e tipo documental (ex.: `oficio`, `justificativa`)."""
    return (
        DocumentoArtefato.objects.filter(oficio_id=oficio_id, tipo=tipo, formato="pdf")
        .order_by("-criado_em")
        .first()
    )
