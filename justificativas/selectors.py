from django.shortcuts import get_object_or_404

from .models import Justificativa
from .models import ModeloJustificativa


def get_justificativa_by_oficio(oficio):
    return get_object_or_404(Justificativa, oficio=oficio)


def get_or_none_justificativa_by_oficio(oficio):
    if not getattr(oficio, "pk", None):
        return None
    return Justificativa.objects.filter(oficio=oficio).first()


def listar_modelos_justificativa(*, incluir_inativos=False):
    qs = ModeloJustificativa.objects.all()
    if not incluir_inativos:
        qs = qs.filter(ativo=True)
    return qs.order_by("ordem", "nome")


def get_modelo_justificativa_by_id(pk):
    return get_object_or_404(ModeloJustificativa, pk=pk)
