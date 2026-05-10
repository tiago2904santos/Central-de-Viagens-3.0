"""Regras de obrigatoriedade de justificativa por prazo (Ofício)."""

from __future__ import annotations

from datetime import date
from typing import Any

from django.utils import timezone

from cadastros.models import ConfiguracaoSistema


def get_prazo_justificativa_dias() -> int:
    """Prazo mínimo em dias corridos; usa ConfiguracaoSistema com fallback 10."""
    try:
        return int(ConfiguracaoSistema.get_singleton().prazo_justificativa_dias)
    except Exception:
        return 10


def get_primeira_saida_oficio(oficio):
    """
    Primeira saída do roteiro vinculado: `Roteiro.saida_dt`, senão primeiro trecho com `saida_dt`.
    Retorna datetime timezone-aware ou None.
    """
    roteiro = getattr(oficio, "roteiro", None)
    if roteiro is None:
        return None

    if roteiro.saida_dt:
        dt = roteiro.saida_dt
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    for trecho in roteiro.trechos.order_by("ordem", "pk"):
        if trecho.saida_dt:
            dt = trecho.saida_dt
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return dt
    return None


def calcular_dias_antecedencia_justificativa(oficio):
    """Dias entre a data da primeira saída e data_criacao do ofício; None se não avaliável."""
    primeira = get_primeira_saida_oficio(oficio)
    if primeira is None:
        return None
    d0 = oficio.data_criacao
    if not isinstance(d0, date):
        d0 = d0.date() if hasattr(d0, "date") else d0
    s_local = primeira.astimezone(timezone.get_current_timezone()).date()
    return (s_local - d0).days


def oficio_exige_justificativa(oficio) -> bool:
    return bool(avaliar_justificativa_oficio(oficio).get("obrigatoria"))


def avaliar_justificativa_oficio(oficio) -> dict[str, Any]:
    """
    Avalia se a justificativa é obrigatória pela regra de antecedência.

    status:
      - unknown — sem roteiro ou sem data de saída utilizável
      - required — obrigatória (antecedência <= prazo ou saída antes da criação)
      - not_applicable — regra avaliada e não obrigatória (antecedência > prazo)
    """
    prazo = get_prazo_justificativa_dias()
    d0 = oficio.data_criacao
    if isinstance(d0, date):
        d0_date = d0
    else:
        d0_date = d0.date()

    primeira = get_primeira_saida_oficio(oficio)
    if primeira is None:
        return {
            "obrigatoria": False,
            "primeira_saida": None,
            "data_criacao": d0_date,
            "dias_antecedencia": None,
            "prazo_dias": prazo,
            "status": "unknown",
            "motivo_regra": "Sem roteiro ou sem data de saída definida.",
        }

    s_local = primeira.astimezone(timezone.get_current_timezone()).date()
    dias = (s_local - d0_date).days

    if dias < 0:
        return {
            "obrigatoria": True,
            "primeira_saida": primeira,
            "data_criacao": d0_date,
            "dias_antecedencia": dias,
            "prazo_dias": prazo,
            "status": "required",
            "motivo_regra": "Saída anterior à data de criação do ofício.",
        }

    if dias <= prazo:
        return {
            "obrigatoria": True,
            "primeira_saida": primeira,
            "data_criacao": d0_date,
            "dias_antecedencia": dias,
            "prazo_dias": prazo,
            "status": "required",
            "motivo_regra": (
                f"Antecedência ({dias} dias) igual ou inferior ao prazo mínimo ({prazo} dias)."
            ),
        }

    return {
        "obrigatoria": False,
        "primeira_saida": primeira,
        "data_criacao": d0_date,
        "dias_antecedencia": dias,
        "prazo_dias": prazo,
        "status": "not_applicable",
        "motivo_regra": (
            f"Antecedência ({dias} dias) superior ao prazo mínimo ({prazo} dias)."
        ),
    }
