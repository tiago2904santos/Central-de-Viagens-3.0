from django.utils import timezone

from .services import avaliar_etapa_justificativa_oficio
from .services import avaliar_justificativa_oficio


def apresentar_justificativa_wizard_context(oficio):
    """
    Contexto de apresentação da etapa de justificativa (badge, alertas, labels).
    """
    etapa = avaliar_etapa_justificativa_oficio(oficio)
    ev = avaliar_justificativa_oficio(oficio)

    obrigatoria = bool(etapa.get("obrigatoria"))
    if obrigatoria:
        badge_label = "Obrigatória"
        badge_variant = "danger"
    else:
        badge_label = "Não exigida"
        badge_variant = "muted"

    primeira = etapa.get("primeira_saida")
    primeira_label = "—"
    if primeira is not None:
        local = primeira.astimezone(timezone.get_current_timezone())
        primeira_label = local.strftime("%d/%m/%Y %H:%M")

    return {
        "etapa": etapa,
        "regra": ev,
        "badge_label": badge_label,
        "badge_variant": badge_variant,
        "alerta_regra": ev.get("motivo_regra") or "",
        "data_criacao_label": ev["data_criacao"].strftime("%d/%m/%Y"),
        "primeira_saida_label": primeira_label,
        "dias_antecedencia_label": (
            str(etapa["dias_antecedencia"])
            if etapa["dias_antecedencia"] is not None
            else "—"
        ),
        "prazo_dias_label": str(etapa["prazo_dias"]),
        "status_etapa_label": etapa["status"],
        "pendencias": etapa.get("pendencias") or [],
    }
