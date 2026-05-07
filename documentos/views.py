from django.shortcuts import render

from .services import default_document_registry


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
