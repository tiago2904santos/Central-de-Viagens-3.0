from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from assinaturas.models import AssinaturaDigital
from assinaturas.models import PedidoAssinaturaDocumento
from assinaturas.services.assinatura_artefato import assinar_artefato_com_etiqueta
from assinaturas.services.assinatura_artefato import assinatura_arquivo_esta_integra
from assinaturas.services.assinatura_artefato import mascarar_cpf_assinatura
from assinaturas.services.codigos import normalizar_codigo_verificacao
from assinaturas.services.hash import calcular_sha256_bytes
from assinaturas.services.pedidos import criar_ou_obter_pedido_assinatura
from assinaturas.services.pedidos import url_publica_pedido_assinatura
from assinaturas.services.recording import registrar_assinatura_concluida
from assinaturas.services.recording import registrar_verificacao_artefato
from assinaturas.services.resolvedores import AssinanteNaoConfiguradoError
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
    from assinaturas.services.validacao_codigo import validar_assinatura_por_codigo

    vd = validar_assinatura_por_codigo(c)
    if not vd["existe"]:
        raise Http404()
    assinatura = vd["assinatura"]
    artefato = vd["artefato"]
    assert assinatura is not None and artefato is not None
    integra = bool(vd["integra"])
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


@login_required
@require_http_methods(["GET", "POST"])
def assinar_artefato(request, artefato_id):
    return gerar_link_assinatura(request, artefato_id)


@login_required
@require_http_methods(["GET", "POST"])
def gerar_link_assinatura(request, artefato_id):
    artefato = get_object_or_404(DocumentoArtefato, pk=artefato_id)
    ensure_request_may_view_artefato_pdf(request, artefato)
    try:
        pedido = criar_ou_obter_pedido_assinatura(
            artefato,
            criado_por=request.user,
            request=request,
            forcar_novo=request.POST.get("forcar_novo") == "1",
        )
    except AssinanteNaoConfiguradoError as exc:
        messages.error(request, str(exc))
        return _redirect_apos_gerar_link(request, artefato)

    link = url_publica_pedido_assinatura(request, pedido)
    messages.success(request, f"Link de assinatura gerado: {link}")
    return _redirect_apos_gerar_link(request, artefato)


def _redirect_apos_gerar_link(request, artefato):
    next_url = (request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER") or "").strip()
    if next_url:
        return redirect(next_url)
    if artefato.oficio_id:
        return redirect(reverse("oficios:wizard_assinaturas", args=[artefato.oficio_id]))
    return redirect(reverse("documentos:artefato_pdf_visualizar", args=[artefato.pk]))


def _posicao_from_post(post):
    return {
        "box_x": float(post.get("sig_x", "0.58")),
        "box_y": float(post.get("sig_y", "0.78")),
        "box_w": float(post.get("sig_w", "0.34")),
        "box_h": float(post.get("sig_h", "0.11")),
        "page_index": int(post.get("sig_page", "-1")),
    }


def _pedido_403_se_usuario_incorreto(request, pedido: PedidoAssinaturaDocumento) -> None:
    if pedido.assinante_usuario_id and pedido.assinante_usuario_id != request.user.pk:
        raise PermissionDenied("Este pedido de assinatura pertence a outro usuário.")


@login_required
@require_http_methods(["GET", "POST"])
def assinar_pedido(request, token):
    pedido = get_object_or_404(
        PedidoAssinaturaDocumento.objects.select_related("artefato", "assinante_servidor", "assinante_usuario"),
        token=token,
    )
    _pedido_403_se_usuario_incorreto(request, pedido)
    if pedido.status == PedidoAssinaturaDocumento.STATUS_ASSINADO and pedido.assinatura_id:
        return HttpResponseRedirect(
            reverse(
                "assinaturas:assinatura-verificar-codigo",
                kwargs={"codigo": pedido.assinatura.codigo_verificacao},
            )
        )
    if pedido.status != PedidoAssinaturaDocumento.STATUS_PENDENTE:
        raise Http404("Pedido de assinatura indisponível.")
    if pedido.esta_expirado:
        pedido.status = PedidoAssinaturaDocumento.STATUS_EXPIRADO
        pedido.save(update_fields=["status"])
        raise Http404("Pedido de assinatura expirado.")

    artefato = pedido.artefato
    ensure_request_may_view_artefato_pdf(request, artefato)
    if request.method == "POST":
        pos = _posicao_from_post(request.POST)
        ass = assinar_artefato_com_etiqueta(
            artefato,
            nome_assinante=pedido.nome_assinante_snapshot,
            cpf_assinante=pedido.cpf_assinante_snapshot,
            email_assinante=pedido.email_assinante_snapshot,
            usuario=request.user,
            request=request,
            posicao=pos,
        )
        pedido.status = PedidoAssinaturaDocumento.STATUS_ASSINADO
        pedido.assinado_em = timezone.now()
        pedido.ip_assinatura = request.META.get("REMOTE_ADDR") or None
        pedido.user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:4000]
        pedido.posicao_etiqueta_json = pos
        pedido.assinatura = ass
        pedido.hash_documento_original = ass.hash_documento
        pedido.hash_documento_assinado = ass.hash_documento_assinado
        pedido.auditoria = {
            **(pedido.auditoria or {}),
            "assinado_por_user_id": str(request.user.pk),
            "codigo_verificacao": ass.codigo_verificacao,
        }
        pedido.save(
            update_fields=[
                "status",
                "assinado_em",
                "ip_assinatura",
                "user_agent",
                "posicao_etiqueta_json",
                "assinatura",
                "hash_documento_original",
                "hash_documento_assinado",
                "auditoria",
            ]
        )
        return HttpResponseRedirect(
            reverse(
                "assinaturas:assinatura-verificar-codigo",
                kwargs={"codigo": ass.codigo_verificacao},
            )
        )
    pdf_url = reverse(
        "assinaturas:assinatura-artefato-pdf-original",
        kwargs={"artefato_id": artefato.pk},
    )
    return render(
        request,
        "assinaturas/assinar_pedido.html",
        {
            "page_title": "Assinatura do documento",
            "artefato": artefato,
            "pedido": pedido,
            "pdf_url": pdf_url,
            "cpf_mascarado": mascarar_cpf_assinatura(pedido.cpf_assinante_snapshot),
            "pedido_url": url_publica_pedido_assinatura(request, pedido),
        },
    )


@login_required
@require_GET
def assinatura_artefato_pdf_original(request, artefato_id):
    artefato = get_object_or_404(DocumentoArtefato, pk=artefato_id)
    ensure_request_may_view_artefato_pdf(request, artefato)
    return _pdf_inline_response(artefato.arquivo, "original.pdf")
