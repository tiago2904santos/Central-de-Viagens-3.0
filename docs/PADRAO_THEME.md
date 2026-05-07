# Padrao Theme

## Objetivo

Padronizar o sistema com apenas dois temas oficiais (`dark` e `light`), com superfícies sólidas e sem transparência estrutural.

## Contrato técnico

- Preferência do usuário: `dark` e `light` (UI e `localStorage`).
- Atributo `data-theme` no `html` usa aliases legados por compatibilidade:
  - `dark` -> `dark-dark`
  - `light` -> `light-light`
- Persistência: `localStorage` na chave `cv-theme`.
- Inicialização antecipada: `static/js/core/theme-init.js` no `head` do `base.html`.
- Interação do usuário: `static/js/theme-toggle.js`.

## Compatibilidade legada

O sistema normaliza automaticamente temas antigos:

- `dark-dark` -> `dark`
- `dark-light` -> `dark`
- `light-dark` -> `dark`
- `light-light` -> `light`

Após normalização, o valor salvo no `localStorage` passa a ser somente `dark` ou `light`, enquanto o DOM continua compatível com estilos legados.

## Responsabilidades por arquivo

- `templates/base.html`: carrega `theme-init.js` antes do CSS e `theme-toggle.js` com `defer`.
- `static/js/core/theme-init.js`: resolve tema inicial e normaliza valor legado.
- `static/js/theme-toggle.js`: aplica tema selecionado e persiste em `localStorage`.
- `static/css/theme.css`: define tokens por tema (escuro/claro) e aliases legados.
- `templates/components/layout/sidebar.html`: expõe apenas 2 opções de tema na UI.

## Regras visuais obrigatórias

- Superfícies principais devem ser sólidas.
- Não usar transparência em `background` de card/painel/seção/input/select/textarea.
- Transparência permitida somente para `box-shadow`, `focus-ring`, borda sutil e elementos decorativos não estruturais.
- Priorizar token semântico em vez de hardcode.

## Hierarquia de superfícies (Roteiros)

1. Superfície principal: `--route-card-bg`
2. Blocos internos: `--route-card-inner-bg`
3. Labels/cards clicáveis internos: `--route-card-inner-bg`
4. Campos preenchíveis: `--color-card`

## Checklist mínimo de validação

### Tema Escuro
- [ ] `/roteiros/`
- [ ] `/roteiros/novo/`
- [ ] `/roteiros/<id>/editar/`
- [ ] dashboard
- [ ] uma lista documental
- [ ] um formulário documental

### Tema Claro
- [ ] `/roteiros/`
- [ ] `/roteiros/novo/`
- [ ] `/roteiros/<id>/editar/`
- [ ] dashboard
- [ ] uma lista documental
- [ ] um formulário documental
