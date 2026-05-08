from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .forms import OficioDadosViajantesForm
from .presenters import apresentar_acoes_oficio
from .presenters import apresentar_oficio_card
from .presenters import apresentar_oficio_wizard_header
from .presenters import apresentar_oficio_wizard_steps
from .presenters import apresentar_pagina_detalhe_oficio
from .selectors import get_oficio_by_id
from .selectors import listar_oficios
from .selectors import listar_roteiros_para_oficio
from .selectors import listar_servidores_para_oficio
from .selectors import listar_unidades_para_oficio
from .services import OficioVinculadoError
from .services import atualizar_oficio_dados_viajantes
from .services import avaliar_oficio_dados_viajantes
from .services import criar_oficio_dados_viajantes
from .services import excluir_oficio


def _prepare_dados_viajantes_form(form):
    form.fields["roteiro"].queryset = listar_roteiros_para_oficio()
    form.fields["solicitante"].queryset = listar_unidades_para_oficio()
    form.fields["servidores"].queryset = listar_servidores_para_oficio()


def _wizard_dados_viajantes_context(*, form, oficio=None, avaliacao=None):
    avaliacao = avaliacao or avaliar_oficio_dados_viajantes(oficio=oficio, form=form)
    pendencias = avaliacao["pendencias"]
    return {
        "page_title": "Cadastro de ofício",
        "wizard_header": apresentar_oficio_wizard_header("dados_viajantes"),
        "wizard_steps": apresentar_oficio_wizard_steps(
            oficio=oficio,
            etapa_atual="dados_viajantes",
            dados_viajantes_status=avaliacao["status"],
        ),
        "pendencias": pendencias,
        "numero_preview": oficio.numero_formatado if oficio else "Gerado automaticamente ao salvar.",
        "form": form,
        "oficio": oficio,
        "back_url": reverse("oficios:index"),
    }


def _redirect_after_dados_viajantes_save(request, oficio, *, created=False):
    action = request.POST.get("action")
    if action == "save_continue":
        messages.success(
            request,
            "Ofício cadastrado com sucesso."
            if created
            else "Dados e viajantes atualizados com sucesso.",
        )
        return redirect("oficios:detalhe", pk=oficio.pk)
    messages.success(
        request,
        "Ofício cadastrado com sucesso." if created else "Dados e viajantes atualizados com sucesso.",
    )
    return redirect("oficios:dados_viajantes", pk=oficio.pk)


def index(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    oficios = listar_oficios(q=q, status=status or None)
    cards = []
    for oficio in oficios:
        card = apresentar_oficio_card(oficio)
        card["actions"] = apresentar_acoes_oficio(
            detalhe_url=reverse("oficios:detalhe", args=[oficio.pk]),
            editar_url=reverse("oficios:editar", args=[oficio.pk]),
            excluir_url=reverse("oficios:excluir", args=[oficio.pk]),
        )
        cards.append(card)
    return render(
        request,
        "oficios/index.html",
        {
            "page_title": "Ofícios",
            "page_description": "CRUD mínimo inicial para gestão de ofícios e evolução documental.",
            "q": q,
            "status": status,
            "cards": cards,
            "create_url": reverse("oficios:novo"),
            "search_clear_url": reverse("oficios:index"),
            "empty_message": "Nenhum ofício cadastrado ainda.",
        },
    )


def novo(request):
    form = OficioDadosViajantesForm(request.POST or None)
    _prepare_dados_viajantes_form(form)
    if request.method == "POST" and form.is_valid():
        oficio = criar_oficio_dados_viajantes(form)
        return _redirect_after_dados_viajantes_save(request, oficio, created=True)
    avaliacao = avaliar_oficio_dados_viajantes(form=form) if request.method == "POST" else None
    return render(
        request,
        "oficios/wizard_dados_viajantes.html",
        _wizard_dados_viajantes_context(form=form, avaliacao=avaliacao),
    )


def detalhe(request, pk):
    oficio = get_oficio_by_id(pk)
    detail = apresentar_pagina_detalhe_oficio(oficio)
    return render(
        request,
        "oficios/detail.html",
        {
            "page_title": f"Ofício {detail['numero_formatado']}",
            "page_description": "Detalhes do ofício e vínculos mínimos de contexto.",
            "oficio": oficio,
            "detail": detail,
            "edit_url": reverse("oficios:editar", args=[oficio.pk]),
            "delete_url": reverse("oficios:excluir", args=[oficio.pk]),
            "back_url": reverse("oficios:index"),
        },
    )


def editar(request, pk):
    oficio = get_oficio_by_id(pk)
    return redirect("oficios:dados_viajantes", pk=oficio.pk)


def dados_viajantes(request, pk):
    oficio = get_oficio_by_id(pk)
    form = OficioDadosViajantesForm(request.POST or None, instance=oficio)
    _prepare_dados_viajantes_form(form)
    if request.method == "POST" and form.is_valid():
        oficio = atualizar_oficio_dados_viajantes(oficio, form)
        return _redirect_after_dados_viajantes_save(request, oficio)
    avaliacao = avaliar_oficio_dados_viajantes(form=form, oficio=oficio)
    return render(
        request,
        "oficios/wizard_dados_viajantes.html",
        _wizard_dados_viajantes_context(form=form, oficio=oficio, avaliacao=avaliacao),
    )


def excluir(request, pk):
    oficio = get_oficio_by_id(pk)
    if request.method == "POST":
        try:
            excluir_oficio(oficio)
        except OficioVinculadoError:
            messages.error(
                request,
                "Não foi possível excluir o ofício porque ele está vinculado a outros registros.",
            )
            return redirect("oficios:index")
        messages.success(request, "Ofício excluído com sucesso.")
        return redirect("oficios:index")
    return render(
        request,
        "oficios/confirm_delete.html",
        {
            "page_title": "Excluir ofício",
            "page_description": "A exclusão é física e pode ser bloqueada quando houver vínculos.",
            "object": oficio,
            "back_url": reverse("oficios:index"),
        },
    )
