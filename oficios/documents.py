"""
Payloads canônicos para o núcleo documental (templates DOCX/PDF).

Os modelos DOCX ``termo_autorizacao.docx``, ``plano_trabalho.docx`` e ``ordem_servico.docx``
usam placeholders **aninhados** (ex.: ``{{ oficio.numero_formatado }}``, ``{{ termo.participante.nome }}``).
Para esses tipos, a ``DocumentoFacade`` recebe o payload canónico diretamente (sem ``docxtpl_context`` plano).
O ofício e a justificativa legados usam chaves planas e ``oficios.docxtpl_context``.
"""

from __future__ import annotations

from typing import Any

from cadastros.models import Servidor
from cadastros.selectors import build_configuracao_context

from justificativas.models import Justificativa
from justificativas.services import oficio_exige_justificativa

from documentos.services.types import DocumentoTipo

from .models import Oficio


def _roteiro_resumo(oficio: Oficio) -> dict[str, Any]:
    r = oficio.roteiro
    if not r:
        return {"resumo": "", "destinos_texto": "", "saida": ""}
    partes: list[str] = []
    qs = r.destinos.select_related("cidade", "estado").order_by("ordem", "pk")[:20]
    for d in qs:
        sigla = d.estado.sigla if d.estado_id else ""
        nome_cidade = d.cidade.nome if d.cidade_id else ""
        partes.append(f"{nome_cidade} ({sigla})".strip())
    destinos = "; ".join(partes) if partes else ""
    saida = ""
    if r.saida_dt:
        saida = r.saida_dt.strftime("%d/%m/%Y %H:%M")
    return {
        "resumo": str(r),
        "destinos_texto": destinos,
        "saida": saida,
        "quantidade_diarias": r.quantidade_diarias or "",
    }


def _justificativa_bloco(oficio: Oficio) -> dict[str, Any]:
    exigida = oficio_exige_justificativa(oficio)
    texto = ""
    j: Justificativa | None
    try:
        j = oficio.justificativa
    except Justificativa.DoesNotExist:
        j = None
    if j and j.texto:
        texto = j.texto.strip()
    return {
        "exigida": exigida,
        "texto": texto,
        "status": getattr(j, "status", "") if j else "",
    }


def build_canonical_document_payload(oficio: Oficio, tipo: DocumentoTipo) -> dict[str, Any]:
    """Monta o contexto usado pelos templates registrados em documentos.services.templates."""
    from .services import build_oficio_document_payload

    base = build_oficio_document_payload(oficio)
    institucional = build_configuracao_context()
    oficio_bloco = {
        **base,
        "roteiro_detalhe": _roteiro_resumo(oficio),
    }
    payload: dict[str, Any] = {
        "institucional": institucional,
        "oficio": oficio_bloco,
        "justificativa": _justificativa_bloco(oficio),
    }

    if tipo == DocumentoTipo.TERMO_AUTORIZACAO:
        raise ValueError("Use build_termo_payload com participante e variante.")
    if tipo in (DocumentoTipo.PLANO_TRABALHO, DocumentoTipo.ORDEM_SERVICO):
        payload["em_elaboracao"] = True
    return payload


def build_justificativa_payload(oficio: Oficio) -> dict[str, Any]:
    return build_canonical_document_payload(oficio, DocumentoTipo.JUSTIFICATIVA)


class VarianteTermo:
    SEMIPREENCHIDO = "semipreenchido"
    COMPLETO_COM_VIATURA = "completo_com_viatura"
    COMPLETO_SEM_VIATURA = "completo_sem_viatura"


def _resolver_variante_padrao(oficio: Oficio) -> str:
    from .services import build_oficio_document_payload

    dados = build_oficio_document_payload(oficio)
    viatura = (dados.get("viatura") or "").strip()
    if viatura:
        return VarianteTermo.COMPLETO_COM_VIATURA
    return VarianteTermo.COMPLETO_SEM_VIATURA


def build_termo_payload(
    oficio: Oficio,
    servidor: Servidor,
    *,
    variante: str | None = None,
    modo_semipreenchido: bool = False,
) -> dict[str, Any]:
    if modo_semipreenchido:
        var = VarianteTermo.SEMIPREENCHIDO
    else:
        var = variante or _resolver_variante_padrao(oficio)
    base_ctx = build_canonical_document_payload(oficio, DocumentoTipo.OFICIO)
    participante = {
        "id": servidor.pk,
        "nome": servidor.nome,
        "cargo": servidor.cargo.nome if servidor.cargo_id else "",
        "cpf": servidor.cpf or "",
        "unidade": servidor.unidade.nome if servidor.unidade_id else "",
    }
    base_ctx["termo"] = {
        "variante": var,
        "participante": participante,
    }
    return base_ctx
