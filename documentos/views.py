from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import DocumentoArtefato
from .services import default_document_registry
from .services.persistence import atualizar_apos_assinatura
from .services.signing import assinar_pdf_final


def index(request):
    document_types = default_document_registry.all()
    available_count = sum(1 for item in document_types if item.formatos_permitidos)
    return render(
        request,
        "documentos/index.html",
        {
            "page_title": "Documentos",
            "page_description": (
                "Nucleo documental ativo: tipos, contratos de validacao, nomes de arquivo e "
                "renderers seguros para evolucao dos modulos de dominio."
            ),
            "core_status": "Núcleo base disponível",
            "core_types_total": len(document_types),
            "core_types_with_format": available_count,
        },
    )


@require_POST
def assinar_artefato_documento(request, pk):
    artefato = get_object_or_404(DocumentoArtefato, pk=pk)
    if artefato.formato != "pdf":
        raise Http404("Apenas PDF pode ser assinado digitalmente neste fluxo.")
    pdf_bytes = artefato.arquivo.read()
    signed, meta = assinar_pdf_final(pdf_bytes)
    atualizar_apos_assinatura(artefato, pdf_assinado=signed, backend=str(meta.get("backend", "")))
    nome = f"assinado_{artefato.tipo}.pdf"
    response = HttpResponse(signed, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nome}"'
    response["X-Signature-Backend"] = meta.get("backend", "")
    return response
