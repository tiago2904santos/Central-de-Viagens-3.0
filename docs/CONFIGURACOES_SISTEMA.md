# Configuracoes do sistema

## Visao geral

`ConfiguracaoSistema` e um singleton (`pk=1`, acesso por `get_singleton()`) mantido em `cadastros`. Ele centraliza somente os dados institucionais que fazem sentido no sistema 3.0 para documentos DOCX/PDF futuros.

Configuracoes contem apenas:

- Divisao.
- Unidade.
- Endereco dos documentos: CEP, logradouro, numero, bairro, cidade endereco e UF.
- Contato: telefone e email.
- Assinantes documentais.

Nao existem em Configuracoes:

- Nome orgao.
- Sigla orgao.
- Sede separada.
- Chefia.
- Prazos e numeracao.
- Assinatura de termo.
- Segundo assinante de oficio.

## Normalizacao

Textos institucionais e de endereco sao normalizados em maiusculo no backend. CEP e telefone sao persistidos apenas com digitos; a mascara e aplicada na UI e nas propriedades de exibicao.

## CEP e sede documental

A tela chama a API interna autenticada:

```text
/cadastros/api/cep/<cep>/
```

A API remove caracteres nao numericos, exige 8 digitos, consulta ViaCEP com timeout curto e retorna JSON padronizado. Erros retornam 400 para CEP invalido, 404 para CEP nao encontrado e 502 para falha externa.

Ao salvar, o service `salvar_configuracao_sistema()` tenta resolver `cidade_sede_padrao` por `uf + cidade_endereco`, usando comparacao tolerante a acentos. A sede documental nao e campo separado: ela e derivada de `cidade_endereco / uf`.

## Assinaturas documentais

`AssinaturaConfiguracao` guarda assinantes por `configuracao`, `tipo` e `ordem`, apontando para `Servidor`. O campo `ativo` e tecnico: fica `True` quando ha servidor configurado e `False` quando o slot esta vazio.

Tipos suportados na tela e no service:

- `OFICIO`: ordem 1.
- `JUSTIFICATIVA`: ordem 1.
- `PLANO_TRABALHO`: ordem 1.
- `ORDEM_SERVICO`: ordem 1.

A persistencia usa `update_or_create`, preservando a chave unica `configuracao + tipo + ordem`, e remove assinaturas extras da configuracao ao salvar.

## Contexto documental

`cadastros.selectors.build_configuracao_context()` retorna `divisao`, `unidade`, endereco, contato, `sede_documental` derivada de cidade/UF e as quatro assinaturas documentais ativas em um dicionario reutilizavel por geradores futuros.

## Etapas futuras

- Integrar `build_configuracao_context()` nos geradores DOCX/PDF.
- Consumir assinaturas configuradas nas regras de renderizacao de documentos.
- Definir politica de assinatura digital/autenticacao quando o modulo de assinaturas for implementado.
