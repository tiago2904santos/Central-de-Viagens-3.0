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

Não depende de coluna no CSV. Há um mapa interno **UF → nome da capital**; o nome do município importado é comparado de forma **normalizada** (maiúsculas, espaços, remoção de acentos para comparação). Ex.: **Curitiba/PR** → `capital=True`; **Londrina/PR** → `capital=False`.

## Duplicidade e consistência

- Estado: `sigla` e `nome` únicos; `codigo_ibge` único quando preenchido.
- Cidade: par **nome + estado** único; `codigo_ibge` único quando preenchido.
- Reimportar a mesma combinação nome+estado ou o mesmo `codigo_ibge` não cria registro duplicado; em `municipio_code` pode haver atualização de `capital` e coordenadas em registros existentes.

## Cidade → Estado

A relação principal é `Cidade.estado` (ForeignKey). O campo `uf` é mantido por compatibilidade e **deve** coincidir com `estado.sigla` (preenchido no `save` do modelo).

## Roteiros

A base geográfica servirá para **origem e destino** em `Cidade` em regras futuras de roteiro, sem cálculo de distância ou diárias nesta etapa.
