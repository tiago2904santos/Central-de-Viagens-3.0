"""
Mapa oficial de capitais (UF → nome) e regras de comparação para a base geográfica interna.
"""

from __future__ import annotations

import unicodedata

CAPITAIS_POR_UF = {
    "AC": "RIO BRANCO",
    "AL": "MACEIÓ",
    "AP": "MACAPÁ",
    "AM": "MANAUS",
    "BA": "SALVADOR",
    "CE": "FORTALEZA",
    "DF": "BRASÍLIA",
    "ES": "VITÓRIA",
    "GO": "GOIÂNIA",
    "MA": "SÃO LUÍS",
    "MT": "CUIABÁ",
    "MS": "CAMPO GRANDE",
    "MG": "BELO HORIZONTE",
    "PA": "BELÉM",
    "PB": "JOÃO PESSOA",
    "PR": "CURITIBA",
    "PE": "RECIFE",
    "PI": "TERESINA",
    "RJ": "RIO DE JANEIRO",
    "RN": "NATAL",
    "RS": "PORTO ALEGRE",
    "RO": "PORTO VELHO",
    "RR": "BOA VISTA",
    "SC": "FLORIANÓPOLIS",
    "SP": "SÃO PAULO",
    "SE": "ARACAJU",
    "TO": "PALMAS",
}


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_nome_municipio(text: str) -> str:
    """Maiúsculas e espaços internos colapsados (preserva caracteres Unicode válidos)."""
    return " ".join((text or "").strip().split()).upper()


def nome_normalizado_duplicidade(nome: str) -> str:
    """
    Chave para agrupar municípios do mesmo estado que são o mesmo lugar com grafia diferente.

    Usa maiúsculas, colapso de espaços e remoção de acentos (ex.: FLORIANOPOLIS ≡ FLORIANÓPOLIS).
    """
    return _strip_accents(_normalize_nome_municipio(nome))


def capital_esperada_para_uf(sigla: str) -> str | None:
    return CAPITAIS_POR_UF.get((sigla or "").strip().upper()[:2])


def dedupe_capitais_por_uf() -> int:
    """
    Garante no máximo uma `Cidade` com `capital=True` por UF.

    Quando vários nomes normalizam como a capital (ex.: FLORIANOPOLIS vs FLORIANÓPOLIS),
    mantém-se preferencialmente o nome canônico do mapa; na empate, prioriza-se `codigo_ibge`
    preenchido e menor `pk`.

    Retorna quantos registros tiveram `capital` alterado para False.
    """
    from cadastros.models import Cidade
    from cadastros.models import Estado

    corrigidos = 0
    for sigla, canon_raw in CAPITAIS_POR_UF.items():
        canon = _normalize_nome_municipio(canon_raw)
        est = Estado.objects.filter(sigla=sigla).first()
        if not est:
            continue
        candidatos = [c for c in Cidade.objects.filter(estado=est) if eh_capital(c.nome, sigla)]
        if len(candidatos) <= 1:
            continue
        exact = [c for c in candidatos if _normalize_nome_municipio(c.nome) == canon]
        if exact:
            keeper = exact[0]
        else:
            keeper = sorted(
                candidatos,
                key=lambda c: (c.codigo_ibge is None, c.pk),
            )[0]
        for c in candidatos:
            if c.pk != keeper.pk and c.capital:
                c.capital = False
                c.save(update_fields=["capital", "updated_at"])
                corrigidos += 1
    return corrigidos


def eh_capital(nome: str, uf: str) -> bool:
    """
    Indica se o município `nome` é a capital oficial da UF `uf`.

    Comparação insensível a acentos (ex.: variações de encoding ainda batem com o mapa).
    """
    sigla = (uf or "").strip().upper()[:2]
    if len(sigla) != 2:
        return False
    esperado = CAPITAIS_POR_UF.get(sigla)
    if not esperado:
        return False
    a = _normalize_nome_municipio(nome)
    b = _normalize_nome_municipio(esperado)
    return _strip_accents(a) == _strip_accents(b)
