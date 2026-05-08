from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .forms import OficioDadosViajantesForm
from .forms import ModeloMotivoOficioForm
from .presenters import apresentar_acoes_oficio
from .presenters import apresentar_linha_lista_simples_modelo_motivo
from .presenters import apresentar_oficio_card
from .presenters import apresentar_oficio_wizard_header
from .presenters import apresentar_oficio_wizard_summary
from .presenters import apresentar_oficio_wizard_steps
from .presenters import apresentar_pagina_detalhe_oficio
from .selectors import get_oficio_by_id
from .selectors import get_modelo_motivo_by_id
from .selectors import listar_modelos_motivo
from .selectors import listar_oficios
from .selectors import listar_servidores_para_oficio
from .services import atualizar_modelo_motivo
from .services import OficioVinculadoError
from .services import atualizar_oficio_dados_viajantes
from .services import avaliar_oficio_dados_viajantes
from .services import criar_modelo_motivo
from .services import criar_oficio_dados_viajantes
from .services import excluir_modelo_motivo
from .services import excluir_oficio
from .services import get_next_available_numero_oficio


def _prepare_dados_viajantes_form(form):
    form.fields["servidores"].queryset = listar_servidores_para_oficio()


def _wizard_dados_viajantes_context(*, form, oficio=None, avaliacao=None):
    avaliacao = avaliacao or avaliar_oficio_dados_viajantes(oficio=oficio, form=form)
    pendencias = avaliacao["pendencias"]
    summary_kwargs = {}
    if oficio is None:
        ano_corrente = timezone.localdate().year
        numero_preview = get_next_available_numero_oficio(ano_corrente)
        summary_kwargs = {
            "numero_preview": f"{numero_preview:02d}/{ano_corrente}",
            "data_preview": timezone.localdate().strftime("%d/%m/%Y"),
        }
    summary = apresentar_oficio_wizard_summary(oficio, **summary_kwargs)
    custeio_value = ""
    if form.is_bound:
        custeio_value = form.data.get("custeio", "")
    else:
        custeio_value = getattr(form.instance, "custeio", "") if getattr(form, "instance", None) else ""
    mostrar_custeio_observacao = custeio_value == "OUTRA_INSTITUICAO"
    modelos_queryset = form.fields["modelo_motivo"].queryset
    return {
        "page_title": "Cadastro de ofício",
        "wizard_header": apresentar_oficio_wizard_header("dados_viajantes"),
        "wizard_steps": apresentar_oficio_wizard_steps(
            oficio=oficio,
            etapa_atual="dados_viajantes",
            dados_viajantes_status=avaliacao["status"],
        ),
        "pendencias": pendencias,
        "wizard_summary": summary,
        "mostrar_custeio_observacao": mostrar_custeio_observacao,
        "modelos_motivo_url": reverse("oficios:modelos_motivo_index"),
        "tem_modelos_motivo": modelos_queryset.exists(),
        "modelo_motivo_selecionado": bool(form["modelo_motivo"].value()),
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
        oficio = criar_oficio_dados_viajantes(form, action=request.POST.get("action", "save_draft"))
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
        oficio = atualizar_oficio_dados_viajantes(oficio, form, action=request.POST.get("action", "save_draft"))
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


def modelos_motivo_index(request):
    q = request.GET.get("q", "").strip()
    modelos = listar_modelos_motivo(q=q or None, incluir_inativos=True)
    rows = [
        apresentar_linha_lista_simples_modelo_motivo(
            modelo,
            edit_url=reverse("oficios:modelo_motivo_editar", args=[modelo.pk]),
            delete_url=reverse("oficios:modelo_motivo_excluir", args=[modelo.pk]),
        )
        for modelo in modelos
    ]
    return render(
        request,
        "oficios/modelos_motivo/index.html",
        {
            "page_title": "Modelos de motivo",
            "page_description": "Cadastre textos reutilizáveis para preencher rapidamente o motivo dos ofícios.",
            "q": q,
            "rows": rows,
            "new_url": reverse("oficios:modelo_motivo_novo"),
        },
    )


def modelo_motivo_novo(request):
    form = ModeloMotivoOficioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        criar_modelo_motivo(form)
        messages.success(request, "Modelo de motivo criado com sucesso.")
        return redirect("oficios:modelos_motivo_index")
    return render(
        request,
        "oficios/modelos_motivo/form.html",
        {
            "page_title": "Novo modelo de motivo",
            "page_description": "Crie textos reutilizáveis para agilizar o preenchimento do motivo nos ofícios.",
            "form": form,
            "back_url": reverse("oficios:modelos_motivo_index"),
            "submit_label": "Salvar modelo",
        },
    )


def modelo_motivo_editar(request, pk):
    modelo = get_modelo_motivo_by_id(pk)
    form = ModeloMotivoOficioForm(request.POST or None, instance=modelo)
    if request.method == "POST" and form.is_valid():
        atualizar_modelo_motivo(modelo, form)
        messages.success(request, "Modelo de motivo atualizado com sucesso.")
        return redirect("oficios:modelos_motivo_index")
    return render(
        request,
        "oficios/modelos_motivo/form.html",
        {
            "page_title": "Editar modelo de motivo",
            "page_description": "Crie textos reutilizáveis para agilizar o preenchimento do motivo nos ofícios.",
            "form": form,
            "back_url": reverse("oficios:modelos_motivo_index"),
            "submit_label": "Salvar alterações",
        },
    )


def modelo_motivo_excluir(request, pk):
    modelo = get_modelo_motivo_by_id(pk)
    if request.method == "POST":
        excluir_modelo_motivo(modelo)
        messages.success(request, "Modelo de motivo excluído com sucesso.")
        return redirect("oficios:modelos_motivo_index")
    return render(
        request,
        "oficios/modelos_motivo/confirm_delete.html",
        {
            "page_title": "Excluir modelo de motivo",
            "page_description": "Confirme a remoção deste modelo de motivo.",
            "object": modelo,
            "back_url": reverse("oficios:modelos_motivo_index"),
        },
    )
