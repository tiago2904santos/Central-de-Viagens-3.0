from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from assinaturas.services.recording import registrar_assinatura_concluida
from assinaturas.services.recording import registrar_verificacao_artefato
from assinaturas.services.verification import verificar_artefato_documento
from documentos.models import DocumentoArtefato
from documentos.services.access import ensure_request_may_view_artefato_pdf
from documentos.services.persistence import atualizar_apos_assinatura
from documentos.services.signing import assinar_pdf_final


def index(request):
    return render(
        request,
        "assinaturas/index.html",
        {
            "page_title": "Assinaturas",
            "page_description": "Base futura para assinatura eletronica, carimbo visual e validacao de integridade.",
        },
    )


@require_GET
def api_verificar_documento(request, pk):
    artefato = get_object_or_404(DocumentoArtefato, pk=pk)
    ensure_request_may_view_artefato_pdf(request, artefato)
    resultado = verificar_artefato_documento(artefato)
    registrar_verificacao_artefato(artefato, resultado)
    status = 200 if resultado.get("ok") else 422
    return JsonResponse(resultado, status=status)


@require_POST
def api_assinar_documento(request, pk):
    artefato = get_object_or_404(DocumentoArtefato, pk=pk)
    ensure_request_may_view_artefato_pdf(request, artefato)
    pdf_bytes = artefato.arquivo.read()
    signed, meta = assinar_pdf_final(pdf_bytes)
    atualizar_apos_assinatura(artefato, pdf_assinado=signed, backend=str(meta.get("backend", "")))
    registrar_assinatura_concluida(artefato, meta)
    return JsonResponse({"ok": True, "meta": meta})
