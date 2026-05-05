from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import AssinaturaConfiguracao
from .models import Cargo
from .models import ConfiguracaoSistema
from .models import Cidade
from .models import Combustivel
from .models import Estado
from .models import Servidor
from .models import Unidade
from .models import Viatura


def listar_unidades(q=None):
    queryset = Unidade.objects.order_by("nome")
    if q:
        queryset = queryset.filter(Q(nome__icontains=q) | Q(sigla__icontains=q))
    return queryset


def listar_cidades(q=None):
    queryset = Cidade.objects.select_related("estado").order_by("estado__sigla", "nome")
    if q:
        queryset = queryset.filter(
            Q(nome__icontains=q)
            | Q(uf__icontains=q)
            | Q(estado__nome__icontains=q)
            | Q(estado__sigla__icontains=q)
        )
    return queryset


def listar_estados(q=None):
    queryset = Estado.objects.order_by("nome")
    if q:
        queryset = queryset.filter(Q(nome__icontains=q) | Q(sigla__icontains=q))
    return queryset


def get_unidade_by_id(pk):
    return get_object_or_404(Unidade, pk=pk)


def get_cidade_by_id(pk):
    return get_object_or_404(Cidade.objects.select_related("estado"), pk=pk)


def get_estado_by_id(pk):
    return get_object_or_404(Estado, pk=pk)


def listar_cargos(q=None):
    queryset = Cargo.objects.order_by("nome")
    if q:
        queryset = queryset.filter(Q(nome__icontains=q))
    return queryset


def get_cargo_by_id(pk):
    return get_object_or_404(Cargo, pk=pk)


def listar_combustiveis(q=None):
    queryset = Combustivel.objects.order_by("nome")
    if q:
        queryset = queryset.filter(Q(nome__icontains=q))
    return queryset


def get_combustivel_by_id(pk):
    return get_object_or_404(Combustivel, pk=pk)


def listar_servidores(q=None):
    queryset = Servidor.objects.select_related("cargo", "unidade").order_by("nome")
    if q:
        queryset = queryset.filter(
            Q(nome__icontains=q)
            | Q(cpf__icontains=q)
            | Q(rg__icontains=q)
            | Q(cargo__nome__icontains=q)
            | Q(unidade__nome__icontains=q)
            | Q(unidade__sigla__icontains=q)
        )
    return queryset


def get_servidor_by_id(pk):
    return get_object_or_404(Servidor.objects.select_related("cargo", "unidade"), pk=pk)


def listar_viaturas(q=None):
    queryset = (
        Viatura.objects.select_related("combustivel")
        .prefetch_related("motoristas")
        .order_by("placa")
    )
    if q:
        queryset = (
            queryset.filter(
                Q(placa__icontains=q)
                | Q(modelo__icontains=q)
                | Q(combustivel__nome__icontains=q)
                | Q(tipo__icontains=q)
                | Q(motoristas__nome__icontains=q)
            )
            .distinct()
        )
    return queryset


def get_viatura_by_id(pk):
    return get_object_or_404(
        Viatura.objects.select_related("combustivel").prefetch_related("motoristas"),
        pk=pk,
    )


def get_configuracao_sistema():
    return ConfiguracaoSistema.get_singleton()


def build_configuracao_context():
    configuracao = get_configuracao_sistema()
    assinaturas = {}
    tipos_documentais = {
        AssinaturaConfiguracao.TIPO_OFICIO,
        AssinaturaConfiguracao.TIPO_JUSTIFICATIVA,
        AssinaturaConfiguracao.TIPO_PLANO_TRABALHO,
        AssinaturaConfiguracao.TIPO_ORDEM_SERVICO,
    }
    assinaturas_qs = configuracao.assinaturas.select_related("servidor").filter(
        tipo__in=tipos_documentais,
        ordem=1,
    ).order_by("tipo", "ordem")
    for assinatura in assinaturas_qs:
        if not assinatura.ativo or not assinatura.servidor_id:
            continue
        assinaturas.setdefault(assinatura.tipo, []).append(
            {
                "ordem": assinatura.ordem,
                "servidor": assinatura.servidor,
                "nome": assinatura.servidor.nome,
            },
        )

    sede_documental = " / ".join(
        value for value in [configuracao.cidade_endereco, configuracao.uf] if value
    )
    return {
        "divisao": configuracao.divisao,
        "unidade": configuracao.unidade,
        "cep": configuracao.cep,
        "cep_formatado": configuracao.cep_formatado,
        "logradouro": configuracao.logradouro,
        "numero": configuracao.numero,
        "bairro": configuracao.bairro,
        "cidade_endereco": configuracao.cidade_endereco,
        "uf": configuracao.uf,
        "sede_documental": sede_documental,
        "telefone": configuracao.telefone,
        "telefone_formatado": configuracao.telefone_formatado,
        "email": configuracao.email,
        "assinaturas": assinaturas,
    }
