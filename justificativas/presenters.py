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
        badge_class = "status-chip--danger"
    else:
        badge_label = "Não exigida"
        badge_class = "status-chip--muted"

    primeira = etapa.get("primeira_saida")
    primeira_label = "—"
    if primeira is not None:
        local = primeira.astimezone(timezone.get_current_timezone())
        primeira_label = local.strftime("%d/%m/%Y %H:%M")

    if obrigatoria:
        resultado_label = "Justificativa obrigatória"
    elif ev.get("status") == "unknown":
        resultado_label = "Aguardando dados do roteiro"
    else:
        resultado_label = "Justificativa dispensada"

    help_texto = (
        "Explique o motivo do cadastramento ou emissão com antecedência igual ou inferior a "
        f"{etapa['prazo_dias']} dias."
        if obrigatoria
        else "Opcional: registre uma justificativa complementar se necessário."
    )

    return {
        "etapa": etapa,
        "regra": ev,
        "badge_label": badge_label,
        "badge_class": badge_class,
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
        "resultado_label": resultado_label,
        "help_texto": help_texto,
    }
