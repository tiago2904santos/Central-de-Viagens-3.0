from datetime import datetime

from django.http import HttpResponse

from documentos.services.timing import measure_step

from .exceptions import UnsupportedDocumentFormat
from .filenames import build_document_filename
from .types import DocumentoFormato
from .types import DocumentoTipo


def get_content_type_for_format(formato: DocumentoFormato) -> str:
    if formato == DocumentoFormato.DOCX:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if formato == DocumentoFormato.PDF:
        return "application/pdf"
    value = getattr(formato, "value", str(formato))
    raise UnsupportedDocumentFormat(f"Formato não suportado: {value}")


def build_download_response(
    *,
    content: bytes,
    tipo: DocumentoTipo,
    formato: DocumentoFormato,
    reference: str | None = None,
    now: datetime | None = None,
) -> HttpResponse:
    with measure_step(
        "build_download_response",
        {"tipo": tipo.value, "formato": formato.value, "reference": reference or ""},
    ):
        filename = build_document_filename(tipo, formato, reference=reference, now=now)
        response = HttpResponse(content, content_type=get_content_type_for_format(formato))
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
