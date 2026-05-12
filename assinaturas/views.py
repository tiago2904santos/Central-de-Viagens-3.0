from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from assinaturas.models import AssinaturaDigital
from assinaturas.services.assinatura_artefato import assinar_artefato_com_etiqueta
from assinaturas.services.assinatura_artefato import assinatura_arquivo_esta_integra
from assinaturas.services.assinatura_artefato import mascarar_cpf_assinatura
from assinaturas.services.codigos import normalizar_codigo_verificacao
from assinaturas.services.hash import calcular_sha256_bytes
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


@login_not_required
@require_GET
def assinatura_verificar_codigo(request, codigo):
    c = normalizar_codigo_verificacao(codigo)
    assinatura = AssinaturaDigital.objects.filter(codigo_verificacao=c).select_related("artefato").first()
    if assinatura is None:
        raise Http404()
    artefato = assinatura.artefato
    integra = assinatura_arquivo_esta_integra(assinatura)
    hash_atual = ""
    if artefato.arquivo_assinado and getattr(artefato.arquivo_assinado, "name", ""):
        try:
            data = artefato.arquivo_assinado.read()
            hash_atual = calcular_sha256_bytes(data)
        except OSError:
            hash_atual = ""
    cpf_m = mascarar_cpf_assinatura(assinatura.cpf_assinante)
    ctx = {
        "assinatura": assinatura,
        "artefato": artefato,
        "status_valido": assinatura.status == AssinaturaDigital.STATUS_VALID,
        "status_integridade_registro": integra,
        "hash_atual_pdf_assinado": hash_atual,
        "cpf_mascarado": cpf_m,
        "url_pdf_original": reverse(
            "assinaturas:assinatura-pdf-original",
            kwargs={"assinatura_id": assinatura.pk},
        ),
        "url_pdf_assinado": reverse(
            "assinaturas:assinatura-pdf-assinado",
            kwargs={"assinatura_id": assinatura.pk},
        ),
    }
    return render(request, "assinaturas/verificar_codigo.html", ctx)


def _pdf_inline_response(field_file, filename: str) -> FileResponse:
    if not field_file or not getattr(field_file, "name", ""):
        raise Http404("Ficheiro nao encontrado.")
    fh = field_file.open("rb")
    resp = FileResponse(fh, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


@login_not_required
@require_GET
def assinatura_pdf_original(request, assinatura_id):
    ass = get_object_or_404(AssinaturaDigital, pk=assinatura_id)
    return _pdf_inline_response(ass.artefato.arquivo, "original.pdf")


@login_not_required
@require_GET
def assinatura_pdf_assinado(request, assinatura_id):
    ass = get_object_or_404(AssinaturaDigital, pk=assinatura_id)
    return _pdf_inline_response(ass.artefato.arquivo_assinado, "assinado.pdf")


@login_required
def assinatura_gestao(request):
    return index(request)

@require_http_methods(["GET", "POST"])
def assinar_artefato(request, artefato_id):
    artefato = get_object_or_404(DocumentoArtefato, pk=artefato_id)
    ensure_request_may_view_artefato_pdf(request, artefato)
    if request.method == "POST":
        pos = {
            "box_x": float(request.POST.get("sig_x", "0.37")),
            "box_y": float(request.POST.get("sig_y", "0.8")),
            "box_w": float(request.POST.get("sig_w", "0.269")),
            "box_h": float(request.POST.get("sig_h", "0.067")),
            "page_index": int(request.POST.get("sig_page", "-1")),
        }
        nome = (request.POST.get("nome_assinante") or "").strip() or (
            request.user.get_full_name() or request.user.get_username()
        )
        cpf = (request.POST.get("cpf_assinante") or "").strip()
        email = (request.POST.get("email_assinante") or "").strip()
        ass = assinar_artefato_com_etiqueta(
            artefato,
            nome_assinante=nome,
            cpf_assinante=cpf,
            email_assinante=email,
            usuario=request.user,
            request=request,
            posicao=pos,
        )
        return HttpResponseRedirect(
            reverse("assinaturas:assinatura-verificar-codigo", kwargs={"codigo": ass.codigo_verificacao})
        )
    pdf_url = reverse("assinaturas:assinatura-artefato-pdf-original", kwargs={"artefato_id": artefato.pk})
    return render(
        request,
        "assinaturas/assinar_artefato.html",
        {
            "page_title": "Assinatura do documento",
            "artefato": artefato,
            "pdf_url": pdf_url,
        },
    )


@require_GET
def assinatura_artefato_pdf_original(request, artefato_id):
    artefato = get_object_or_404(DocumentoArtefato, pk=artefato_id)
    ensure_request_may_view_artefato_pdf(request, artefato)
    return _pdf_inline_response(artefato.arquivo, "original.pdf")
