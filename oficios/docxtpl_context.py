"""
Contexto plano (flat) para templates DOCX legados (docxtpl), alinhado a
`oficio_model.docx` e `modelo_justificativa.docx` do Central de Viagens 2.0.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.utils import timezone

from cadastros.selectors import build_configuracao_context

from justificativas.models import Justificativa

from roteiros.models import RoteiroTrecho

from .models import Oficio

ASSUNTO_AUTORIZACAO = "Solicitação de autorização e concessão de diárias."
ASSUNTO_CONVALIDACAO = "Solicitação de convalidação e concessão de diárias."
DESTINO_FORA_PARANA = "SESP"
DESTINO_DENTRO_PARANA = "Gabinete do Delegado Geral Adjunto"

_MESES_PTBR = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

# Chaves extraídas dos .docx legados (garantir todas presentes no dict).
OFICIO_DOCXTPL_KEYS = frozenset(
    {
        "oficio",
        "data_do_oficio",
        "protocolo",
        "nome_chefia",
        "cargo_chefia",
        "unidade",
        "unidade_cabecalho",
        "orgao_destino",
        "placa",
        "viatura",
        "combustivel",
        "tipo_viatura",
        "motorista_formatado",
        "custo",
        "diarias_x",
        "diaria",
        "destinos_bloco",
        "col_servidor",
        "col_rgcpf",
        "col_cargo",
        "col_ida_saida",
        "col_ida_chegada",
        "col_volta_saida",
        "col_volta_chegada",
        "col_solicitacao",
        "assunto_linha",
        "assunto_oficio",
        "assunto_termo",
        "armamento",
        "motivo",
        "divisao",
        "email",
        "endereco",
        "telefone",
        "unidade_rodape",
    },
)

JUSTIFICATIVA_DOCXTPL_KEYS = frozenset(
    {
        "sede",
        "data_extenso",
        "justificativa",
        "assinante_justificativa",
        "cargo_assinante_justificativa",
        "divisao",
        "unidade",
        "unidade_rodape",
        "endereco",
        "email",
        "telefone",
    },
)


def _txt(v: object) -> str:
    return str(v or "").strip()


def _hdr(v: object) -> str:
    t = _txt(v)
    return t.upper() if t else ""


def _fmt_date(d: date | datetime | None) -> str:
    if not d:
        return ""
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d/%m/%Y")


def _fmt_time(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%H:%M")


def _build_endereco(inst: dict[str, Any]) -> str:
    partes = [
        _txt(inst.get("logradouro")),
        _txt(inst.get("numero")),
        _txt(inst.get("bairro")),
    ]
    cidade = _txt(inst.get("cidade_endereco"))
    uf = _txt(inst.get("uf")).upper()
    cidade_uf = " / ".join([p for p in (cidade, uf) if p])
    if cidade_uf:
        partes.append(cidade_uf)
    cep = _txt(inst.get("cep_formatado") or inst.get("cep"))
    if cep:
        partes.append(f"CEP {cep}")
    return ", ".join(p for p in partes if p)


def _build_sede(inst: dict[str, Any]) -> str:
    cidade = _txt(inst.get("cidade_endereco"))
    uf = _txt(inst.get("uf")).upper()
    if cidade and uf:
        return f"{cidade}/{uf}"
    if cidade:
        return cidade
    return _txt(inst.get("sede"))


def _assinatura_nome_cargo(inst: dict[str, Any]) -> tuple[str, str]:
    ass = inst.get("assinaturas") or {}
    rows: list[dict[str, Any]] = []
    if isinstance(ass, dict):
        for _tipo, lst in ass.items():
            if not isinstance(lst, list):
                continue
            for row in lst:
                if isinstance(row, dict) and (_txt(row.get("nome")) or row.get("servidor")):
                    rows.append(row)
    rows.sort(key=lambda r: int(r.get("ordem") or 0))
    if not rows:
        return _txt(inst.get("nome_chefia")), _txt(inst.get("cargo_chefia"))
    row = rows[0]
    srv = row.get("servidor")
    nome = _txt(row.get("nome") or (getattr(srv, "nome", "") if srv else ""))
    cargo = ""
    if srv is not None and getattr(srv, "cargo_id", None):
        cargo = _txt(srv.cargo.nome)
    return nome, cargo


def _orgao_destino(oficio: Oficio) -> str:
    r = getattr(oficio, "roteiro", None)
    if not r:
        return DESTINO_DENTRO_PARANA
    for d in r.destinos.select_related("estado"):
        if d.estado_id and d.estado.sigla != "PR":
            return DESTINO_FORA_PARANA
    for t in r.trechos.select_related("destino_estado"):
        if t.destino_estado_id and t.destino_estado.sigla != "PR":
            return DESTINO_FORA_PARANA
    return DESTINO_DENTRO_PARANA


def _build_column_lines(items: list[str], blank_lines: int = 1) -> str:
    lines: list[str] = []
    cleaned = [str(x).strip() for x in items if str(x or "").strip()]
    for index, item in enumerate(cleaned):
        lines.append(item)
        if index < len(cleaned) - 1:
            lines.extend([""] * blank_lines)
    return "\n".join(lines)


def _viajantes(oficio: Oficio) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for s in oficio.servidores.select_related("cargo").order_by("nome"):
        out.append(
            {
                "nome": _txt(s.nome),
                "cargo": _txt(s.cargo.nome if s.cargo_id else ""),
                "rg": _txt(s.rg_formatado),
                "cpf": _txt(s.cpf_formatado),
            },
        )
    return out


def _col_rgcpf(viajantes: list[dict[str, str]]) -> str:
    linhas: list[str] = []
    for index, v in enumerate(viajantes):
        linhas.append(f"RG: {v.get('rg') or '-'}")
        linhas.append(f"CPF: {v.get('cpf') or '-'}")
        if index < len(viajantes) - 1:
            linhas.append("")
    return "\n".join(linhas)


def _trecho_label(t: RoteiroTrecho) -> tuple[str, str]:
    def cidade_sigla(c, e):
        if c and e:
            return f"{c.nome}/{e.sigla}"
        if c:
            return c.nome
        if e:
            return e.sigla
        return ""

    orig = cidade_sigla(t.origem_cidade, t.origem_estado)
    dest = cidade_sigla(t.destino_cidade, t.destino_estado)
    return orig or "—", dest or "—"


def _route_columns(trechos: list[RoteiroTrecho]) -> tuple[str, str]:
    saida_lines: list[str] = []
    chegada_lines: list[str] = []
    for idx, trecho in enumerate(trechos):
        orig, dest = _trecho_label(trecho)
        sd = _fmt_date(trecho.saida_dt) if trecho.saida_dt else ""
        st = _fmt_time(trecho.saida_dt) if trecho.saida_dt else ""
        cd = _fmt_date(trecho.chegada_dt) if trecho.chegada_dt else ""
        ct = _fmt_time(trecho.chegada_dt) if trecho.chegada_dt else ""
        saida_lines.append(f"Saída {orig}: {sd} {st}".strip())
        chegada_lines.append(f"Chegada {dest}: {cd} {ct}".strip())
        if idx < len(trechos) - 1:
            saida_lines.append("")
            chegada_lines.append("")
    return "\n".join(saida_lines), "\n".join(chegada_lines)


def _roteiro_trechos(oficio: Oficio) -> tuple[list[RoteiroTrecho], list[RoteiroTrecho]]:
    r = oficio.roteiro
    if not r:
        return [], []
    qs = list(r.trechos.select_related("origem_cidade", "origem_estado", "destino_cidade", "destino_estado").order_by("ordem", "pk"))
    ida = [t for t in qs if t.tipo == RoteiroTrecho.TIPO_IDA]
    volta = [t for t in qs if t.tipo == RoteiroTrecho.TIPO_RETORNO]
    if not volta and (r.retorno_saida_dt or r.retorno_chegada_dt):
        # Um bloco de retorno só no cabeçalho do roteiro (sem trecho RETORNO).
        volta = []
    return ida, volta


def _destinos_bloco(oficio: Oficio) -> str:
    r = oficio.roteiro
    if not r:
        return ""
    partes: list[str] = []
    for d in r.destinos.select_related("cidade", "estado").order_by("ordem", "pk"):
        if d.cidade_id and d.estado_id:
            partes.append(f"{d.cidade.nome}/{d.estado.sigla}")
    return "\n".join(partes) if partes else ""


def _custeio_text(oficio: Oficio) -> str:
    labels = {
        Oficio.CUSTEIO_UNIDADE_DPC: "UNIDADE - DPC (diárias e combustível custeados pela DPC).",
        Oficio.CUSTEIO_OUTRA_INSTITUICAO: "OUTRA INSTITUIÇÃO",
        Oficio.CUSTEIO_ONUS_LIMITADO: "ÔNUS LIMITADOS AOS PRÓPRIOS VENCIMENTOS",
    }
    linhas: list[str] = []
    for choice in (
        Oficio.CUSTEIO_UNIDADE_DPC,
        Oficio.CUSTEIO_OUTRA_INSTITUICAO,
        Oficio.CUSTEIO_ONUS_LIMITADO,
    ):
        marcador = "( X )" if oficio.custeio == choice else "(   )"
        label = labels.get(choice, choice)
        if choice == Oficio.CUSTEIO_OUTRA_INSTITUICAO and oficio.custeio == choice and oficio.custeio_observacao:
            label = f"{label}: {oficio.custeio_observacao}"
        linhas.append(f"{marcador} {label}")
    return "\n".join(linhas)


def _motorista_formatado(oficio: Oficio) -> str:
    if oficio.motorista_id:
        nome = _txt(oficio.motorista.nome)
        return nome
    if oficio.motorista_modo == Oficio.MOTORISTA_MODO_MANUAL:
        nome = _txt(oficio.motorista_manual_nome)
        if not nome:
            return ""
        linhas = [nome]
        ref = _txt(oficio.motorista_oficio_referencia)
        if ref:
            linhas.append(f"Ofício do motorista: {ref}")
        prot = _txt(oficio.motorista_protocolo_ref)
        if prot:
            linhas.append(f"Protocolo do motorista: {prot}")
        return "\n".join(linhas)
    return ""


def _veiculo_bloco(oficio: Oficio) -> dict[str, str]:
    placa = ""
    modelo = ""
    comb = ""
    tipo_v = ""
    if oficio.viatura_id:
        v = oficio.viatura
        placa = _txt(v.placa_formatada)
        modelo = _txt(v.modelo)
        comb = _txt(v.combustivel.nome if v.combustivel_id else "")
        tipo_v = _txt(v.get_tipo_display())
    else:
        from core.utils.masks import format_placa

        placa = format_placa(oficio.transporte_placa_manual) if oficio.transporte_placa_manual else ""
        modelo = _txt(oficio.transporte_modelo_manual)
        if oficio.transporte_combustivel_manual_id:
            comb = _txt(oficio.transporte_combustivel_manual.nome)
        tipo_v = _txt(oficio.get_transporte_tipo_manual_display() if oficio.transporte_tipo_manual else "")
    return {
        "placa": placa,
        "viatura": modelo or placa or "—",
        "combustivel": comb,
        "tipo_viatura": tipo_v,
    }


def _diarias(oficio: Oficio) -> tuple[str, str]:
    r = oficio.roteiro
    if not r:
        return "", ""
    q = _txt(r.quantidade_diarias)
    if r.valor_diarias is not None:
        valor = str(r.valor_diarias).replace(".", ",")
        extenso = _txt(r.valor_diarias_extenso)
        if extenso:
            valor = f"{valor} ({extenso})"
        return q, valor
    return q, ""


def build_oficio_docxtpl_context(oficio: Oficio) -> dict[str, Any]:
    inst = build_configuracao_context()
    nome_chefia, cargo_chefia = _assinatura_nome_cargo(inst)
    unidade = _txt(inst.get("unidade")) or _txt(inst.get("nome_orgao")) or _txt(inst.get("sigla_orgao"))
    viajantes = _viajantes(oficio)
    ida, volta = _roteiro_trechos(oficio)
    ida_saida, ida_chegada = _route_columns(ida)
    volta_saida, volta_chegada = _route_columns(volta)
    v = _veiculo_bloco(oficio)
    diarias_x, diaria = _diarias(oficio)
    data_of = _fmt_date(oficio.data_criacao)
    from core.utils.masks import format_protocolo

    protocolo = format_protocolo(oficio.protocolo)

    ctx: dict[str, Any] = {
        "oficio": oficio.numero_formatado if oficio.numero and oficio.ano else "—",
        "data_do_oficio": data_of,
        "protocolo": protocolo,
        "nome_chefia": nome_chefia,
        "cargo_chefia": cargo_chefia,
        "unidade": _txt(unidade),
        "unidade_cabecalho": _hdr(unidade),
        "orgao_destino": _orgao_destino(oficio),
        "placa": v["placa"],
        "viatura": v["viatura"],
        "combustivel": v["combustivel"],
        "tipo_viatura": v["tipo_viatura"],
        "motorista_formatado": _motorista_formatado(oficio),
        "custo": _custeio_text(oficio),
        "diarias_x": diarias_x,
        "diaria": diaria,
        "destinos_bloco": _destinos_bloco(oficio),
        "col_servidor": _build_column_lines([v["nome"] for v in viajantes], blank_lines=2),
        "col_rgcpf": _col_rgcpf(viajantes),
        "col_cargo": _build_column_lines([v["cargo"] for v in viajantes], blank_lines=2),
        "col_ida_saida": ida_saida,
        "col_ida_chegada": ida_chegada,
        "col_volta_saida": volta_saida,
        "col_volta_chegada": volta_chegada,
        "col_solicitacao": "",
        "assunto_linha": _txt(oficio.assunto) or ASSUNTO_AUTORIZACAO,
        "assunto_oficio": "(Autorização)",
        "assunto_termo": "autorização",
        "armamento": "Sim" if oficio.porte_transporte_armas else "Não",
        "motivo": _txt(oficio.motivo),
        "divisao": _hdr(inst.get("divisao")),
        "email": _txt(inst.get("email")),
        "endereco": _build_endereco(inst),
        "telefone": _txt(inst.get("telefone_formatado") or inst.get("telefone")),
        "unidade_rodape": _txt(unidade),
    }
    for key in OFICIO_DOCXTPL_KEYS:
        ctx.setdefault(key, "")
    return ctx


def _format_data_extenso(d: date) -> str:
    mes = _MESES_PTBR.get(d.month, str(d.month))
    return f"{d.day} de {mes} de {d.year}"


def build_justificativa_docxtpl_context(oficio: Oficio) -> dict[str, Any]:
    inst = build_configuracao_context()
    nome_a, cargo_a = _assinatura_nome_cargo(inst)
    unidade = _txt(inst.get("unidade")) or _txt(inst.get("nome_orgao")) or _txt(inst.get("sigla_orgao"))
    texto = ""
    try:
        j = oficio.justificativa
        texto = _txt(j.texto)
    except Justificativa.DoesNotExist:
        pass

    ctx: dict[str, Any] = {
        "sede": _build_sede(inst),
        "data_extenso": _format_data_extenso(timezone.localdate()),
        "justificativa": texto,
        "assinante_justificativa": nome_a,
        "cargo_assinante_justificativa": cargo_a,
        "divisao": _hdr(inst.get("divisao")),
        "unidade": _hdr(unidade),
        "unidade_rodape": _txt(unidade),
        "endereco": _build_endereco(inst),
        "email": _txt(inst.get("email")),
        "telefone": _txt(inst.get("telefone_formatado") or inst.get("telefone")),
    }
    for key in JUSTIFICATIVA_DOCXTPL_KEYS:
        ctx.setdefault(key, "")
    return ctx
