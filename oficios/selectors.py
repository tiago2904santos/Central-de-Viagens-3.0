from django.db.models import Q
from django.shortcuts import get_object_or_404

from cadastros.models import Servidor
from cadastros.models import Unidade
from cadastros.models import Viatura
from roteiros.models import Roteiro

from .models import Oficio


def listar_oficios(q: str | None = None, status: str | None = None):
    queryset = (
        Oficio.objects.select_related("roteiro", "viatura", "motorista", "solicitante")
        .prefetch_related("servidores")
        .order_by("-data_criacao", "-created_at")
    )
    if status:
        queryset = queryset.filter(status=status)
    if q:
        query = q.strip()
        filters = (
            Q(protocolo__icontains=query)
            | Q(assunto__icontains=query)
            | Q(motivo__icontains=query)
            | Q(roteiro__observacoes__icontains=query)
            | Q(roteiro__origem_cidade__nome__icontains=query)
            | Q(roteiro__origem_estado__nome__icontains=query)
        )
        if query.isdigit():
            filters |= Q(numero=int(query)) | Q(ano=int(query))
        queryset = queryset.filter(filters).distinct()
    return queryset


def get_oficio_by_id(pk: int):
    queryset = Oficio.objects.select_related("roteiro", "viatura", "motorista", "solicitante").prefetch_related(
        "servidores",
    )
    return get_object_or_404(queryset, pk=pk)


def listar_roteiros_para_oficio():
    return Roteiro.objects.order_by("-created_at")


def listar_servidores_para_oficio():
    return Servidor.objects.select_related("cargo", "unidade").order_by("nome")


def listar_viaturas_para_oficio():
    return Viatura.objects.select_related("combustivel").prefetch_related("motoristas").order_by("placa")


def listar_unidades_para_oficio():
    return Unidade.objects.order_by("nome")
