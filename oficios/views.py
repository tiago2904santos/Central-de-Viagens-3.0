from django.shortcuts import render


def index(request):
    return render(
        request,
        "oficios/index.html",
        {
            "page_title": "Oficios",
            "page_description": (
                "Módulo em preparação arquitetural: Ofícios irão consumir o núcleo documental "
                "e reutilizar blocos do domínio de roteiros sem prometer CRUD completo nesta etapa."
            ),
        },
    )
