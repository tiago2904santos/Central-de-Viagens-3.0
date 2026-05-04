# Importação da base geográfica (Estados e municípios)

**Estados** e **municípios** (model `Cidade`) são **dados internos** do sistema. O usuário comum **não** acessa CRUD desses registros pela interface; a carga é feita apenas por **management command**. Os dados alimentam roteiros, destinos, regras futuras de documentos e selects internos (`cadastros.selectors`).

Não há página pública de listagem/edição, nem botão de exportar CSV de municípios na aplicação.

A carga em lote usa CSVs; o comando recomendado orquestra estados e `municipio_code.csv`.

## Arquivos

| Arquivo | Uso |
|--------|-----|
| `estados.csv` | UF: colunas `COD` (código IBGE do estado), `NOME`, `SIGLA`. |
| `municipio_code.csv` | Municípios: separador `;`, colunas `id_municipio`, `uf`, `municipio`, opcional `longitude` e `latitude`. |
| `municipios.csv` | Alternativa: colunas `COD UF` (código IBGE do **estado**), `COD` (código do município), `NOME`. Exige estados já importados com `codigo_ibge` correspondente. |

Arquivos grandes em `dados/` devem permanecer fora do Git (não commitar `dados/estados.csv`, `dados/municipio_code.csv`, etc.).

## Comando recomendado

```bash
python manage.py importar_base_geografica --estados dados/estados.csv --municipios-code dados/municipio_code.csv
```

Alternativa com `municipios.csv` (IBGE):

```bash
python manage.py importar_base_geografica --estados dados/estados.csv --municipios dados/municipios.csv
```

## Opções

- `--dry-run`: simula contagem e validações **sem** gravar.
- `--encoding` (padrão `utf-8-sig`).

## Comando legado (só cidades)

```bash
python manage.py importar_cidades caminho/arquivo.csv
```

Útil para reimportar só municípios; ainda é necessário ter **Estados** cadastrados quando o CSV for formato simples (`nome,uf` / `municipio,uf`).

## O que é salvo

- **Estados:** `nome` e `sigla` em maiúsculas; `codigo_ibge` a partir de `COD` quando existir. Não há ativo/inativo.
- **Cidades:** `nome` (maiúsculas), vínculo `estado` por **sigla da UF** no CSV, `uf` espelhando `estado.sigla`, `codigo_ibge` quando a fonte tiver código, `latitude`/`longitude` quando informados, `capital` conforme regra abaixo.

## Capitais

O mapa oficial UF → nome da capital está centralizado em **`cadastros/geografia.py`** (`CAPITAIS_POR_UF`, função `eh_capital(nome, uf)`). O importador define `capital` **somente** com base nesse mapa e pode **corrigir** `capital=True` indevido em reimportações (`capitais_corrigidas` no resumo).

Não depende de coluna no CSV. A comparação usa nome normalizado (maiúsculas, espaços) e **insensível a acentos** para bater com o mapa. Ex.: **Curitiba/PR** → `capital=True`; **Londrina/PR** → `capital=False`.

O campo `id_municipio` / `codigo_ibge` no CSV é o **código do próprio arquivo**; pode não coincidir com o código IBGE oficial de 7 dígitos. Para base “oficial” IBGE, use fonte e colunas adequadas.

## Auditoria e saneamento

Antes de usar a base em **Roteiros**, recomenda-se conferir consistência:

```bash
python manage.py auditar_base_geografica
```

Para recalcular todas as capitais segundo o mapa oficial (sem alterar outros campos):

```bash
python manage.py sanear_base_geografica --dry-run --fix-capitais
python manage.py sanear_base_geografica --fix-capitais
```

Mescla opcional de duplicados **nome + estado** (prioriza registro com `codigo_ibge`), repontando vínculos de roteiros quando necessário:

```bash
python manage.py sanear_base_geografica --dry-run --fix-duplicados
python manage.py sanear_base_geografica --fix-duplicados
```

Duplicados **mesmo estado** com nomes que só diferem por acento ou grafia leve (mesmo nome sem acento), quando aparecem como duas linhas no banco:

```bash
python manage.py sanear_base_geografica --dry-run --fix-duplicados-normalizados
python manage.py sanear_base_geografica --fix-duplicados-normalizados
```

Mantém o registro mais completo (`codigo_ibge`, depois coordenadas), reponta vínculos de roteiros e remove o duplicado.

### Mais de uma “capital” por UF (mesmo município, grafias diferentes)

Se o CSV ou dados antigos criarem duas linhas que equivalem à capital (ex.: `FLORIANOPOLIS` sem acento e `FLORIANÓPOLIS` com código), **ambas** podiam receber `capital=True` porque `eh_capital` compara nomes sem acento. A função `dedupe_capitais_por_uf()` (chamada ao final da importação `municipio_code` e após `sanear --fix-capitais`) mantém só um registro como capital por UF, preferindo o **nome canônico** do mapa oficial e, na falta dele, o registro com `codigo_ibge` preenchido.

Para remover duplicata ortográfica (ex.: `FLORIANOPOLIS` vs `FLORIANÓPOLIS` no mesmo estado), use **`--fix-duplicados-normalizados`** (ver comandos acima).

## Duplicidade e consistência

- Estado: `sigla` e `nome` únicos; `codigo_ibge` único quando preenchido.
- Cidade: par **nome + estado** único; `codigo_ibge` único quando preenchido.
- Reimportar a mesma combinação nome+estado ou o mesmo `codigo_ibge` não cria registro duplicado; em `municipio_code` pode haver atualização de `capital` e coordenadas em registros existentes.
- Conflito (mesmo nome+estado com **outro** `codigo_ibge` já gravado) incrementa `conflitos` no resumo e não cria linha duplicada silenciosa.

## Cidade → Estado

A relação principal é `Cidade.estado` (ForeignKey). O campo `uf` é mantido por compatibilidade e **deve** coincidir com `estado.sigla` (preenchido no `save` do modelo).

## Roteiros

A base geográfica servirá para **origem e destino** em `Cidade` em regras futuras de roteiro, sem cálculo de distância ou diárias nesta etapa.
