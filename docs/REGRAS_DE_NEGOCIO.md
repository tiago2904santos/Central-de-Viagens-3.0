# Regras de Negocio

## Cadastros

O app `cadastros` centraliza dados-base reutilizados por documentos e fluxos futuros.

Entidades ativas do modulo:

- `Unidade`: nome e sigla.
- `Estado`: **base interna** (UF: nome, sigla, `codigo_ibge` quando houver). Não há CRUD na interface do usuário; carga via `importar_base_geografica` (ver `docs/IMPORTACAO_BASE_GEOGRAFICA.md`). Uso futuro: roteiros, documentos, selects internos.
- `Cidade`: no código o model chama-se `Cidade` e **representa o município** na base geográfica. Pertence a um `Estado`; **nome + estado** é único; `uf` espelha a sigla; `capital` (mapa interno de capitais); `codigo_ibge` e coordenadas quando a fonte tiver. **Não** há listagem, criação, edição ou exclusão na interface do usuário; carga somente via management command. O guia `docs/IMPORTACAO_CIDADES.md` descreve o importador de municípios isolado, quando aplicável.
- `Cargo`: nome unico e em maiusculo.
- `Combustivel`: nome unico e em maiusculo.
- `Servidor`: nome unico e em maiusculo, cargo, CPF, RG opcional e unidade opcional.
- `Viatura`: placa unica (AAA1234 ou AAA1A23), modelo, combustivel e tipo (`CARACTERIZADA`/`DESCARACTERIZADA`).

## Regras obrigatorias

- Nao existe cadastro de `Motorista`.
- `Servidor` nao possui matricula.
- `Viatura` nao possui marca nem unidade.
- Cadastros nao possuem ativo/inativo.
- Exclusao e fisica.
- Quando existir vinculo relevante, exclusao deve ser bloqueada com mensagem clara.

Mensagem padrao de bloqueio:

```text
Não foi possível excluir este cadastro porque ele está vinculado a outros registros.
```

## Mascaras visuais

- CPF: `000.000.000-00` (armazenado em digitos).
- RG: `00.000.000-0` (armazenado normalizado).
- Placa: `AAA-1234` ou `AAA1A23` na tela; armazenada sem hifen e em maiusculo.

## Roteiros

`Roteiro` e uma entidade reutilizavel e avulsa. Ele pode existir sozinho e nao depende de Evento, Oficio, Plano de Trabalho, Ordem de Servico ou Evento.

Regras da base:

- roteiros poderao ser reutilizados futuramente por documentos e fluxos;
- Evento, quando existir, sera apenas agrupador opcional;
- nao existe ativo/inativo;
- exclusao futura sera fisica;
- se houver vinculo futuro com documentos, a exclusao devera ser bloqueada;
- origem e destino usam `Cidade` do app `cadastros`;
- cada `Cidade` pertence a um `Estado`;
- trechos pertencem ao roteiro;
- nao ha calculo de distancia, tempo ou diarias nesta etapa.

## Base geografica

- `Estado` e `Cidade` (município) são **dados internos**: não há telas públicas `/cadastros/estados/` nem `/cadastros/cidades/`, nem exportar/importar CSV na UI.
- `Estado` não é texto solto de UF: existe como entidade com constraints e integridade.
- Toda `Cidade` referencia um `Estado` via FK (`PROTECT`), para preservar integridade quando houver uso em roteiros ou outros fluxos.
- Capitais são marcadas por mapa interno UF → nome oficial, com comparação de texto normalizada (acentos).
- Roteiros e demais módulos usarão `Cidade` / selectors internos para origem e destino.
- Não existe ativo/inativo para estado nem município.
- Arquivos CSV reais em `dados/` não entram no repositório; a importação é operação técnica (`python manage.py importar_base_geografica`).
