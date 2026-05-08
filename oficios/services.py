from django.db import transaction
from django.db.models import ProtectedError


class OficioVinculadoError(Exception):
    """Exclusão bloqueada porque o ofício possui vínculos protegidos."""


@transaction.atomic
def criar_oficio(form):
    return form.save()


@transaction.atomic
def atualizar_oficio(instance, form):
    _ = instance
    return form.save()


@transaction.atomic
def excluir_oficio(instance):
    try:
        instance.delete()
    except ProtectedError as exc:
        raise OficioVinculadoError from exc


def build_oficio_document_payload(oficio):
    return {
        "numero": oficio.numero,
        "ano": oficio.ano,
        "numero_formatado": oficio.numero_formatado,
        "protocolo": oficio.protocolo,
        "assunto": oficio.assunto,
        "motivo": oficio.motivo,
        "data_criacao": oficio.data_criacao,
        "status": oficio.status,
        "roteiro": str(oficio.roteiro) if oficio.roteiro else "",
        "servidores": [servidor.nome for servidor in oficio.servidores.all()],
        "viatura": oficio.viatura.placa_formatada if oficio.viatura else "",
        "motorista": oficio.motorista.nome if oficio.motorista else "",
        "custeio": oficio.custeio,
    }
