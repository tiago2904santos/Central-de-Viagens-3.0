from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.shortcuts import render

from .forms import OficioForm
from .presenters import apresentar_acoes_oficio
from .presenters import apresentar_oficio_card
from .presenters import apresentar_pagina_detalhe_oficio
from .selectors import get_oficio_by_id
from .selectors import listar_oficios
from .selectors import listar_roteiros_para_oficio
from .selectors import listar_servidores_para_oficio
from .selectors import listar_unidades_para_oficio
from .selectors import listar_viaturas_para_oficio
from .services import OficioVinculadoError
from .services import atualizar_oficio
from .services import criar_oficio
from .services import excluir_oficio


def _prepare_form(form):
    form.fields["roteiro"].queryset = listar_roteiros_para_oficio()
    form.fields["solicitante"].queryset = listar_unidades_para_oficio()
    form.fields["servidores"].queryset = listar_servidores_para_oficio()
    form.fields["viatura"].queryset = listar_viaturas_para_oficio()
    form.fields["motorista"].queryset = listar_servidores_para_oficio()


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
        },
    )


def novo(request):
    form = OficioForm(request.POST or None)
    _prepare_form(form)
    if request.method == "POST" and form.is_valid():
        criar_oficio(form)
        messages.success(request, "Ofício criado com sucesso.")
        return redirect("oficios:index")
    return render(
        request,
        "oficios/form.html",
        {
            "page_title": "Novo ofício",
            "page_description": "Cadastre os dados iniciais do ofício.",
            "form": form,
            "submit_label": "Criar ofício",
            "back_url": reverse("oficios:index"),
        },
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
    form = OficioForm(request.POST or None, instance=oficio)
    _prepare_form(form)
    if request.method == "POST" and form.is_valid():
        atualizar_oficio(oficio, form)
        messages.success(request, "Ofício atualizado com sucesso.")
        return redirect("oficios:index")
    return render(
        request,
        "oficios/form.html",
        {
            "page_title": "Editar ofício",
            "page_description": "Atualize os campos básicos do ofício.",
            "form": form,
            "submit_label": "Salvar ofício",
            "back_url": reverse("oficios:index"),
        },
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
