# Auditoria Visual de Execução — Design System

> Gerado em 2026-05-10. Branch: `chore/design-audit-inventory`.
> Serve como mapa de dívida para as Fases 2–16 da padronização do design system.

---

## 1. CSS global importado por `style.css`

Ordem de importação (17 arquivos):

| # | Arquivo | Responsabilidade |
|---|---------|-----------------|
| 1 | `tokens.css` | Primitivos: cores, sombras, espaçamento, radius, tipografia, z-index, controles |
| 2 | `theme.css` | Tokens semânticos por tema (light/dark), sidebar, hero, botões por tema |
| 3 | `auth.css` | Layout exclusivo da tela de autenticação |
| 4 | `base.css` | Reset, body, tipografia base, inputs/selects globais |
| 5 | `layout.css` | Shell (`app-shell`, `app-main`, `content-wrap`), page-header legado |
| 6 | `sidebar.css` | Sidebar institucional |
| 7 | `buttons.css` | `.btn` / `.app-btn` e variantes |
| 8 | `forms.css` | `.app-form-shell`, `.form-section`, `.form-grid`, `.field`, componentes de domínio |
| 9 | `lists.css` | `.list-page`, `.list-toolbar`, `.list-grid`, `.simple-list` |
| 10 | `cards.css` | `.card`, `.module-card`, `.document-card`, `.summary-card`, `.page-card` |
| 11 | `app-ui.css` | `.app-page-hero` (hero híbrido), badges, chips, status-pill |
| 12 | `dashboard.css` | Shell e grid exclusivos do dashboard |
| 13 | `app-page.css` | `.app-page`, `.app-page__shell` e variantes de surface para páginas internas |
| 14 | `stages.css` | Stepper/stages do wizard de Ofícios |
| 15 | `documents.css` | Cards e superfícies de documentos gerados (PDF/DOCX) |
| 16 | `utilities.css` | Classes utilitárias de espaçamento, display, cores pontuais |
| 17 | `domain.css` | Componentes de domínio: rota, trechos, destinos, resumo |

**Arquivo não importado em `style.css` mas existente:** `steppers.css` — verificar se é legado ou carregado via `extra_css` em algum template.

---

## 2. CSS extra carregado por página (`extra_css`)

| Módulo / Template | CSS extra carregado |
|-------------------|---------------------|
| `roteiros/roteiro_form_page.html` | `roteiros.css` (editor + mapa Leaflet) |
| `roteiros/index.html` | `roteiros-list.css` (card de roteiro + diárias) |
| Outros módulos | Nenhum CSS extra identificado — usam apenas `style.css` global |

---

## 3. Shells e cabeçalhos existentes (gramáticas concorrentes)

| Gramática | Onde é usada | Status |
|-----------|-------------|--------|
| `app-shell > app-main > content-wrap` | `base.html` — **todos os módulos** | ✅ Canônico global |
| `app-page > app-page__shell` | Cadastros, Ofícios, Roteiros (via componentes) | ✅ Canônico de página interna |
| `app-page-hero` | `list_page_simple.html`, `list_page.html`, alguns módulos | ✅ Em uso, mas concorre com nomenclatura interna |
| `page-header` | `layout.css` + `components/layout/page_header.html` | ⚠️ Legado ativo — sem migração concluída |
| `components/cards/page_header.html` | Componente alternativo de header | ⚠️ Duplicação suspeita com `layout/page_header.html` |
| `oficio-wizard` / `oficio-wizard__*` | `wizard_base.html` e etapas internas | ⚠️ Gramática própria, fora do padrão global |
| `dashboard-login-inspired` / classes próprias | `core/dashboard.html` | ⚠️ Shell isolado, fora do padrão global |
| `auth-*` | `core/login.html` | ✅ Aceitável como exceção de feature |

---

## 4. Componentes compartilhados existentes

### `templates/components/`

```
buttons/
  action_button.html       ← emite .btn .btn-{variant} (não emite .app-btn ainda)
  button_group.html

cards/
  card.html
  document_card.html
  module_card.html
  page_header.html         ← duplicação suspeita com layout/page_header.html
  summary_card.html

domain/
  (componentes específicos de rota, trechos, destinos)

feedback/
  alerts.html
  confirm_delete_block.html
  empty_state.html
  module_placeholder.html

forms/
  card_toggle.html
  form_actions.html
  form_field.html          ← emite .field (não emite .app-form-field ainda)
  form_page.html
  form_section.html
  input_with_action.html
  oficio_motorista_split_field.html  ← componente de domínio na pasta genérica

layout/
  app_shell.html
  header.html
  page_header.html         ← possível conflito com cards/page_header.html
  sidebar.html
  topbar.html

lists/
  list_empty.html
  list_filters.html
  list_grid.html
  list_page.html
  list_page_simple.html    ← usa .app-page / .app-page-hero (mais próximo do padrão)
  list_toolbar.html
  simple_list.html
  simple_list_row.html     ← emite botões crus, não via action_button.html

modals/
  modal.html

steppers/
  stepper.html
  stepper_actions.html
```

---

## 5. Classes semânticas existentes vs. classes legacy paralelas

| Camada | Classe canônica atual | Legacy paralela | Situação |
|--------|----------------------|-----------------|----------|
| Shell global | `app-shell`, `app-main`, `content-wrap` | — | ✅ Único |
| Página interna | `app-page`, `app-page__shell` | — | ✅ Único |
| Header de página | `app-page-hero`, `app-page-hero__*` | `page-header` | ⚠️ Dois padrões ativos |
| Botão base | `.app-btn` (CSS) | `.btn` (HTML dominante) | ⚠️ CSS tem alias, HTML não usa |
| Botão variante | `.app-btn--primary` (CSS) | `.btn-primary` (HTML dominante) | ⚠️ Mesmo problema |
| Form shell | `.app-form-shell` | `.form-shell` (alias em CSS) | ✅ Alias já existe |
| Form section | `.form-section` | — | ⚠️ Sem prefixo `app-` |
| Form field | `.field` | — | ⚠️ Sem prefixo `app-` |
| Form label | `label` HTML puro | — | ⚠️ Sem classe semântica |
| Form help | `.field-help` | — | ⚠️ Sem prefixo `app-` |
| Form error | `.field-error` | — | ⚠️ Sem prefixo `app-` |
| Form grid | `.form-grid` | — | ⚠️ Sem prefixo `app-` |
| Lista shell | `.list-page` | — | ⚠️ Sem prefixo `app-` |
| Lista toolbar | `.list-toolbar` | — | ⚠️ Sem prefixo `app-` |
| Lista row | `.simple-list__item` | — | ⚠️ Sem prefixo `app-` |
| Card base | `.card` | — | ⚠️ Genérico demais |
| Card módulo | `.module-card` | — | ⚠️ Sem prefixo `app-` |
| Card documento | `.document-card` | — | ⚠️ Sem prefixo `app-` |
| Status | `.status-chip` | — | ⚠️ Sem prefixo `app-` |
| Tokens semânticos | `--color-*`, `--theme-*`, `--route-*` | — | ⚠️ Sem camada `--app-*` |

---

## 6. Tokens com problema

| Token | Usado em | Definido em `tokens.css`? | Ação |
|-------|----------|--------------------------|------|
| `--space-7` | `app-page.css`, `dashboard.css` | ❌ Não existe | Criar alias `--space-7: 28px` em `tokens.css` ou substituir por `clamp` |
| `--space-7` | `auth.css` | ❌ Não existe (mas tem fallback `28px`) | Manter fallback e criar token |
| `--route-card-bg` | `forms.css` | Definido em `theme.css` | ✅ OK, mas é token de domínio em CSS global |
| `--route-section-bg` | `forms.css` | Definido em `theme.css` | ⚠️ Idem — candidato a extração para `roteiros.css` |
| `--app-body-bg` | `theme.css`, `app-page.css` | Definido em `theme.css` | ✅ OK |
| `--app-featured-bg` | `app-page.css` | Definido em `theme.css` | ✅ OK |
| Nenhum `--app-bg`, `--app-surface`, etc. | — | ❌ Não existe | Criar em **Fase 2** |

---

## 7. Arquivos com maior risco de duplicação ou conflito

| Arquivo | Risco | Detalhe |
|---------|-------|---------|
| `forms.css` (1900 linhas) | 🔴 Alto | Mistura regras genéricas com `.oficio-wizard__*`, `.motivo-card__*`, `.oficio-equipe-picker__*`, `.app-multiselect__*` |
| `cards.css` + `app-page.css` | 🟡 Médio | Sobreposição em `.page-card` e `.document-card-body` |
| `layout/page_header.html` + `cards/page_header.html` | 🟡 Médio | Dois componentes com o mesmo nome, finalidade parecida |
| `roteiros-list.css` | 🟡 Médio | Contém regras de hero/header/lista que poderiam ser globais |
| `theme.css` | 🟡 Médio | Mistura tokens semânticos genéricos com `--route-*` e `--sidebar-*` específicos |
| `steppers.css` | 🟡 Médio | Não importado em `style.css` — verificar se é legado ou `extra_css` |

---

## 8. Templates legados ou suspeitos

| Template | Status provável | Evidência |
|----------|-----------------|-----------|
| `templates/registration/login.html` | 🔴 Legado | Views ativas usam `core/login.html` |
| `templates/oficios/form.html` | 🔴 Legado | Views de Ofícios usam o wizard (`wizard_base.html`) |
| `templates/roteiros/form.html` | 🔴 Legado | View de Roteiros usa `roteiro_form_page.html` |
| `templates/components/cards/page_header.html` | 🟡 Suspeito | Coexiste com `components/layout/page_header.html` |

---

## 9. Inconsistências entre documentação e código ativo

| Doc | O que diz | O que o código faz |
|-----|-----------|--------------------|
| `docs/COMPONENTES.md` | Servidores e Viaturas usam `list_page.html` + `document_card` | Código ativo usa `list_page_simple.html` + `simple_list_row.html` |
| `docs/DESIGN_SYSTEM.md` | Descreve tokens e padrão visual | Parcialmente divergente do estado atual dos tokens |
| `docs/PADRAO_TEMPLATES.md` | Documenta stack de templates | Pode estar desatualizado após migrações recentes |

---

## 10. Módulos por nível de conformidade com o design system

### ✅ Conformidade alta (referência para migração)
- `templates/cadastros/**` — usa `app-page`, `app-page-hero`, `app-form-shell`, `form-section`, componentes compartilhados

### 🟡 Conformidade parcial
- `templates/oficios/detail.html` — usa `app-page` mas tem elementos próprios
- `templates/oficios/confirm_delete.html` — estrutura ok, detalhes visuais próprios
- `templates/roteiros/detail.html` — usa padrão de page mas com gramática de domínio própria

### 🔴 Baixa conformidade (maior dívida)
- `templates/oficios/index.html` — usa classes de vocabulário de Roteiros (`app-page-hero__roteiros-*`) sem importar `roteiros-list.css`
- `templates/oficios/wizard_base.html` e etapas — gramática `oficio-wizard__*` própria
- `templates/roteiros/index.html` — carrega `roteiros-list.css` com regras de shell que deveriam ser globais
- `templates/roteiros/roteiro_form_page.html` — carrega `roteiros.css` com mistura de global + editor
- `templates/core/dashboard.html` — shell isolado `dashboard-login-inspired`

### ⚪ Placeholders (aguardam padrão global antes de migrar)
- `templates/planos_trabalho/index.html`
- `templates/justificativas/index.html`
- `templates/termos/index.html`
- `templates/ordens_servico/index.html`
- `templates/eventos/index.html`
- `templates/prestacoes_contas/index.html`

---

## 11. Hotspots priorizados para as próximas fases

| Prioridade | Hotspot | Fase alvo |
|-----------|---------|-----------|
| 🔴 P1 | Criar tokens `--app-*` em `tokens.css`/`theme.css` | Fase 2 |
| 🔴 P1 | Definir `--space-7: 28px` em `tokens.css` | Fase 2 |
| 🔴 P1 | `action_button.html` emitir `.app-btn .app-btn--*` junto de `.btn` | Fase 5 |
| 🔴 P1 | `form_field.html` emitir `.app-form-field` junto de `.field` | Fase 6 |
| 🟡 P2 | Extrair regras de domínio de `forms.css` para `roteiros.css`/`oficios.css` | Fases 11–13 |
| 🟡 P2 | Corrigir `templates/oficios/index.html` — remover dependência de vocabulário de Roteiros | Fase 9 |
| 🟡 P2 | Consolidar `page_header.html` (eliminar duplicação `layout/` vs `cards/`) | Fase 3 |
| 🟡 P2 | Confirmar se `steppers.css` é legado ou ativo | Fase 1 (ação imediata) |
| 🟢 P3 | Confirmar e remover templates legados (`registration/login.html`, `oficios/form.html`, `roteiros/form.html`) | Fase 16 |
| 🟢 P3 | Atualizar `docs/COMPONENTES.md` para refletir `list_page_simple.html` | Fase 8 |

---

## 12. Resultado de `python scripts/audit_frontend_standards.py`

```
== Auditoria Frontend (suspeitas) ==
Nenhuma suspeita encontrada.
```

Nenhuma violação de CSS inline, JS inline ou event handlers inline detectada. ✅

---

## 13. Verificação de `steppers.css`

`static/css/steppers.css` existe mas **não é importado em `style.css`** e **não é referenciado em nenhum template** via `extra_css`. Conclusão: **provável legado** — candidato a remoção na Fase 16 (após confirmar que o conteúdo foi absorvido por `stages.css` ou `forms.css`).

---

## Resumo executivo

| Categoria | Situação |
|-----------|----------|
| Shell global (`base.html`) | ✅ Padronizado e único |
| Tokens primitivos | ✅ Completos em `tokens.css` |
| Tokens semânticos `--app-*` | ❌ Inexistentes — criar na Fase 2 |
| `--space-7` | ❌ Usado mas não definido — corrigir na Fase 2 |
| API de botões no HTML | ❌ `.app-btn` no CSS mas HTML usa `.btn` |
| API de form fields no HTML | ❌ `.app-form-field` ausente, HTML usa `.field` |
| Headers de página | ⚠️ Dois padrões ativos (`app-page-hero` e `page-header`) |
| `forms.css` | ⚠️ 1900 linhas, mistura global + domínio |
| Temas | ✅ Light/dark funcionando com 4 modos |
| Templates legados suspeitos | ⚠️ 3 confirmados, aguardam limpeza na Fase 16 |
| Audit de padrões frontend | ✅ Zero violações |
| Testes | ✅ Passando (verificar em cada fase) |
