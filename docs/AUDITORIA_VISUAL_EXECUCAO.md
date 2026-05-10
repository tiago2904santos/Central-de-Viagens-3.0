# Auditoria Visual de Execução — Design System

> Atualizado em 2026-05-10. Pós-Fase 16.  
> Branch de referência: `ajuste/cadastros-ui-funcional-servidor-viatura`  
> Nota atual: **7/10** → alvo: **10/10** (8 prompts de fechamento em execução)

---

## Status geral pós-Fase 16

| Categoria | Status | Detalhe |
|-----------|--------|---------|
| Shell global (`base.html`) | ✅ RESOLVIDO | `app-shell > app-main > content-wrap` — único e padronizado |
| Tokens primitivos (`tokens.css`) | ✅ RESOLVIDO | Completos: espaçamento, radius, cores, sombras, tipografia |
| Tokens `--space-7` | ✅ RESOLVIDO | Definido como `28px` em `tokens.css` |
| Tokens semânticos `--app-*` | ✅ RESOLVIDO | Criados em `theme.css`/`tokens.css` |
| Shell de página (`app-page`) | ✅ RESOLVIDO | Canônico em Cadastros, Ofícios, Roteiros, Dashboard |
| Hero de página (`app-page-hero`) | ✅ RESOLVIDO | Componente híbrido com `__stage`, `__body`, `__ribbon` |
| API de botões HTML | ✅ RESOLVIDO | `action_button.html` emite `.btn` + `.app-btn` em paralelo |
| Aliases CSS de listas | ✅ RESOLVIDO | `.app-list-toolbar`, `.app-list-grid`, `.app-list__row`, `.app-badge` |
| Aliases CSS de cards | ✅ RESOLVIDO | `.app-card` como joint selector de todas as variantes de card |
| Aliases CSS de seções | ✅ RESOLVIDO | `.app-section`, `.app-panel` e sub-elementos definidos |
| Aliases CSS de forms | ✅ RESOLVIDO | `.app-form-field`, `.app-form-grid`, `.app-form-section` definidos |
| Aliases CSS de wizard | ✅ RESOLVIDO | `.app-wizard`, `.app-stepper` e sub-elementos definidos |
| Wizard de Ofícios (HTML) | ✅ RESOLVIDO | `wizard_base.html` e etapas emitem classes `app-wizard__*` |
| Templates legados removidos | ✅ RESOLVIDO | 6 arquivos deletados (ver seção 3) |
| `steppers.css` removido | ✅ RESOLVIDO | Conteúdo absorvido por `stages.css` / `forms.css` |
| Auditoria inline | ✅ RESOLVIDO | Zero violações (`style=`, `onclick=`, `<script>` inline) |
| `form_field.html` help/error | ⚠️ PARCIAL | `app-form-field` OK; help/error ainda em `field-help`/`field-error` |
| Roteiros CSS orphan | ⚠️ PARCIAL | `.app-page-hero__roteiros-*` em `roteiros-list.css` sem uso nos templates |
| `page-header` legado CSS | ⚠️ PARCIAL | Alias mínimo em `layout.css`; sem remoção formal/documentação |
| `forms.css` separação domínio | ⚠️ PARCIAL | 2092 linhas; 50+ seletores `.oficio-*`, `.motivo-*`, `.roteiro-*` presentes |
| Dashboard decisão arquitetural | ⚠️ PARCIAL | `dashboard-login-inspired` usa 100% CSS vars mas não é declarado como exceção |
| Script de auditoria | ⚠️ PARCIAL | Detecta inline corretamente; falta categorias ERRO/AVISO/EXCEÇÃO |

---

## 1. CSS global importado por `style.css`

Ordem de importação atual (17 arquivos):

| # | Arquivo | Responsabilidade |
|---|---------|-----------------|
| 1 | `tokens.css` | Primitivos: cores, sombras, espaçamento, radius, tipografia, z-index, controles |
| 2 | `theme.css` | Tokens semânticos por tema (light/dark), `--app-*` aliases, sidebar, hero |
| 3 | `auth.css` | Layout exclusivo da tela de autenticação |
| 4 | `base.css` | Reset, body, tipografia base, inputs/selects globais |
| 5 | `layout.css` | `app-shell`, `app-main`, `content-wrap`, `page-header` (alias legado) |
| 6 | `sidebar.css` | Sidebar institucional |
| 7 | `buttons.css` | `.btn` / `.app-btn` e variantes |
| 8 | `forms.css` | Form global + componentes de domínio (candidato à separação — Prompt 5) |
| 9 | `lists.css` | `.list-page`, `.simple-list`, aliases `.app-list-*` |
| 10 | `cards.css` | `.card`, `.module-card`, `.document-card`, `.app-card`, `.app-section`, `.app-panel` |
| 11 | `app-ui.css` | `.app-page-hero`, badges, chips, status-pill |
| 12 | `dashboard.css` | Shell e grid exclusivos do dashboard (usa 100% CSS vars) |
| 13 | `app-page.css` | `.app-page`, `.app-page__shell` e variantes de surface |
| 14 | `stages.css` | Stepper/stages do wizard de Ofícios |
| 15 | `documents.css` | Cards e superfícies de documentos gerados (PDF/DOCX) |
| 16 | `utilities.css` | Classes utilitárias de espaçamento, display, cores pontuais |
| 17 | `domain.css` | Componentes de domínio: rota, trechos, destinos, resumo |

**Pendência:** `oficios.css` ainda não existe; previsto no Prompt 5 para absorver regras `.oficio-*` de `forms.css`.

---

## 2. CSS extra carregado por página (`extra_css`)

| Template | CSS extra carregado | Justificativa |
|----------|---------------------|---------------|
| `roteiros/roteiro_form_page.html` | `domain.css`, `roteiros.css` | Editor Leaflet + autosave: CSS específico de domínio e mapa |
| `roteiros/index.html` | `roteiros-list.css` | Cards de roteiro com layout de diárias: específico de domínio |
| Todos os outros módulos | Nenhum | Apenas `style.css` global — padrão correto |

**Pendência Prompt 6:** auditar se `roteiros-list.css` / `roteiros.css` contêm regras globais que deveriam estar em `app-page.css` / `lists.css`. Limpar classes orphan.

---

## 3. Arquivos removidos nas Fases 1–16

| Arquivo | Status | Observação |
|---------|--------|------------|
| `static/css/steppers.css` | ✅ REMOVIDO | Conteúdo absorvido por `stages.css` + `forms.css` |
| `templates/registration/login.html` | ✅ REMOVIDO | View usa `core/login.html` |
| `templates/oficios/form.html` | ✅ REMOVIDO | View usa wizard (`wizard_base.html`) |
| `templates/roteiros/form.html` | ✅ REMOVIDO | View usa `roteiro_form_page.html` |
| `templates/components/steppers/stepper.html` | ✅ REMOVIDO | Substituído por `wizard_stepper.html` |
| `templates/components/steppers/stepper_actions.html` | ✅ REMOVIDO | Substituído por `wizard_actions.html` |

---

## 4. Headers de página — estado atual

| Componente | Localização | Status |
|------------|------------|--------|
| `.app-page-hero` + `__stage`, `__body`, `__ribbon` | `app-ui.css`, todos os módulos | ✅ Padrão canônico oficial |
| `components/layout/page_header.html` | `layout/page_header.html` | ⚠️ Emite `page-header app-page__header` — alias em migração |
| `components/cards/page_header.html` | `cards/page_header.html` | ⚠️ Emite `page-card` — componente diferente, não é header de página |
| `.page-header` em `layout.css` | `layout.css` | ⚠️ Alias legado com comentário; sem remoção formal |

**Pendência Prompt 3:** confirmar usos de `page_header.html` e `page-header`; remover ou isolar definitivamente.

---

## 5. Formulários — estado atual

| Item | Estado |
|------|--------|
| `form_field.html` — classe raiz | ✅ Emite `field app-form-field` |
| `form_field.html` — help text | ⚠️ Ainda usa `field-help` (não `app-form-help`) |
| `form_field.html` — erro | ⚠️ Ainda usa `field-error` (não `app-form-error`) |
| `.app-form-label` | ⚠️ Definido em CSS mas não emitido por `form_field.html` |
| `.app-form-section` | ✅ CSS definido; templates de Cadastros emitem `form-section app-form-section` |
| `.app-form-grid` | ✅ CSS definido; templates de Cadastros emitem `form-grid app-form-grid` |
| `.app-wizard` / `.app-stepper` | ✅ CSS definido; `wizard_base.html` e `wizard_stepper.html` emitem classes canônicas |

**Pendência Prompt 4:** atualizar `form_field.html` para emitir `app-form-label`, `app-form-help`, `app-form-error`.

---

## 6. `forms.css` — composição atual (2092 linhas)

| Categoria | Estimativa de linhas | Destino |
|-----------|---------------------|---------|
| Regras de formulário globais (`.field`, `.form-grid`, `.app-form-*`) | ~800 | Permanecem em `forms.css` |
| Wizard global (`.app-wizard`, `.app-stepper`) | ~150 | Permanecem em `forms.css` |
| Picker de equipe (`.oficio-equipe-picker__*`) | ~200 | → `oficios.css` |
| Motivos (`.motivo-card__*`) | ~150 | → `oficios.css` |
| Multiselect (`.app-multiselect__*`) | ~200 | Avaliar: global ou domínio |
| Componentes de rota/roteiro (`.route-*`) | ~300 | → `roteiros.css` ou `domain.css` |
| Estilos de Ofício sem prefixo claro | ~292 | → `oficios.css` |

**Pendência Prompt 5:** criar `static/css/oficios.css`, mover seletores de domínio, atualizar `style.css`.

---

## 7. Dashboard — estado atual

| Aspecto | Status |
|---------|--------|
| CSS variables | ✅ 100% usa `var(--*)` — sem cores hardcoded |
| Classes `app-*` em `dashboard.html` | ✅ `app-page`, `app-page__shell`, `app-section`, `app-card` adicionados em paralelo |
| Shell `dashboard-login-inspired` | ⚠️ Mantido; não declarado como EXCEÇÃO oficial nos docs |
| Auditoria configurada para reconhecer excepção | ⚠️ Ainda não configurado |

**Pendência Prompt 7:** declarar `dashboard-login-inspired` como exceção oficial em `DESIGN_SYSTEM.md` e configurar o script de auditoria para classificá-lo como EXCEÇÃO, não ERRO.

---

## 8. Módulos por nível de conformidade (pós-Fase 16)

### ✅ Conformidade alta
- `templates/cadastros/**` — `app-page`, `app-page-hero`, `app-form-shell`, `app-form-section`, `app-form-grid`, `action_button.html`
- `templates/oficios/**` — wizard com `app-wizard__*`, `app-stepper__*`, `app-btn`
- `templates/roteiros/**` — `app-page`, `app-page-hero`, `app-list-grid`, `app-btn`
- `templates/core/dashboard.html` — `app-page`, `app-section`, `app-card` adicionados

### ⚠️ Conformidade parcial (dívida pontual)
- `form_field.html` — raiz ok; help/error ainda em classes legadas
- `roteiros-list.css` — classes orphan `.app-page-hero__roteiros-*` (sem uso nos templates)
- `layout.css` — `page-header` como alias, sem declaração formal de exceção

### ⚪ Módulos placeholder (aguardam conteúdo antes de migrar padrão)
- `planos_trabalho`, `justificativas`, `termos`, `ordens_servico`, `eventos`, `prestacoes_contas`
- Todos usam `app-page`/`app-page-hero` como shell — conformidade base ok

---

## 9. Resultado do script de auditoria

```
python scripts/audit_frontend_standards.py
== Auditoria Frontend (suspeitas) ==
Nenhuma suspeita encontrada.
```

Zero violações de `style=""`, `onclick=`, `<script>` inline detectadas. ✅

**Pendência Prompt 2:** expandir script com categorias ERRO / AVISO / EXCEÇÃO; detectar `page-header` legado, cores hex hardcoded fora de tokens, seletores de domínio em CSS global.

---

## 10. Inconsistências entre documentação e código (pós-Fase 16)

| Documento | O que diz | Estado atual |
|-----------|-----------|-------------|
| `docs/COMPONENTES.md` | Pode referenciar `list_page.html` + `document_card` para Cadastros | Cadastros usam `list_page_simple.html` + `simple_list_row.html` |
| `docs/DESIGN_SYSTEM.md` | Descreve tokens e API visual | Parcialmente atualizado; falta seção de exceções e API final de forms |
| `docs/PADRAO_TEMPLATES.md` | Documenta stack de templates | Pode estar desatualizado após remoção de 6 arquivos legados |

**Pendência Prompt 8:** atualizar todos os três documentos com estado final real.

---

## 11. Pendências finais para fechamento 10/10

Execução em 8 prompts sequenciais:

| # | Branch | Escopo | Arquivos principais |
|---|--------|--------|---------------------|
| **P1** | `chore/finaliza-auditoria-visual-design-system` | ✅ **Este documento** — auditoria pós-fase 16 reescrita | `docs/AUDITORIA_VISUAL_EXECUCAO.md` |
| **P2** | `chore/auditoria-frontend-rigorosa` | Fortalecer script: ERRO/AVISO/EXCEÇÃO; detectar `page-header`, hex hardcoded, seletores de domínio em CSS global | `scripts/audit_frontend_standards.py` |
| **P3** | `refactor/consolida-headers-design-system` | Confirmar usos de `page-header`; encerrar legado ou documentar como exceção mínima; checar `cards/page_header.html` | `layout.css`, `app-ui.css`, `DESIGN_SYSTEM.md` |
| **P4** | `refactor/forms-semanticos-design-system` | `form_field.html`: label→`app-form-label`, help→`app-form-help`, error→`app-form-error`; aliases CSS | `form_field.html`, `forms.css`, `DESIGN_SYSTEM.md` |
| **P5** | `refactor/separa-css-dominio-forms` | Criar `oficios.css`; mover `.oficio-*`, `.motivo-*` de `forms.css`; atualizar `style.css` | `forms.css`, `oficios.css` (novo), `style.css` |
| **P6** | `refactor/revisa-css-extra-roteiros` | Auditar `roteiros-list.css` + `roteiros.css`; limpar classes orphan; mover regras globais se houver | `roteiros-list.css`, `roteiros.css`, `app-page.css`, `lists.css` |
| **P7** | `refactor/dashboard-design-system-final` | Declarar `dashboard-login-inspired` como EXCEÇÃO oficial; garantir zero hex hardcoded; configurar auditor | `dashboard.css`, `dashboard.html`, `DESIGN_SYSTEM.md` |
| **P8** | `chore/fechamento-design-system-visual` | Rodar checklist completo; corrigir pequenos problemas; fechar documentação (`DESIGN_SYSTEM.md`, `COMPONENTES.md`) | Todos os docs |

---

## 12. Critério de aceite 10/10

- [ ] `python scripts/audit_frontend_standards.py` → zero ERROS (AVISOs e EXCEÇÕEs documentadas são OK)
- [ ] `python manage.py check` → OK
- [ ] Tokens `--app-*` são a API pública consumida pelos componentes
- [ ] `forms.css` não concentra CSS de domínio (`.oficio-*`, `.motivo-*` movidos)
- [ ] `page-header` legado: removido ou isolado como alias mínimo documentado
- [ ] Dashboard: decisão arquitetural formalizada em `DESIGN_SYSTEM.md`
- [ ] `form_field.html` emite `app-form-label`, `app-form-help`, `app-form-error`
- [ ] `roteiros-list.css` sem classes orphan
- [ ] `docs/DESIGN_SYSTEM.md` reflete API visual final
- [ ] `docs/COMPONENTES.md` reflete componentes reais em uso
- [ ] Fluxos críticos intactos: wizard de ofício, autosave de roteiros, PDF/DOCX, pickers, sidebar

---

## Histórico de fases executadas

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Inventário e auditoria inicial | ✅ |
| 2 | Tokens `--app-*`, `--space-7` | ✅ |
| 3 | Shell canônico `app-page` / `app-page__shell` | ✅ |
| 4 | Hero canônico `app-page-hero` | ✅ |
| 5 | `action_button.html` emite `.app-btn` | ✅ |
| 6 | `form_field.html` emite `.app-form-field` (raiz) | ✅ |
| 7 | Aliases `.app-list-*` em `lists.css` | ✅ |
| 8 | Aliases `.app-card`, `.app-section`, `.app-panel` em `cards.css` | ✅ |
| 9 | Migração `oficios/index.html` para padrão canônico | ✅ |
| 10 | Migração `roteiros/index.html` para padrão canônico | ✅ |
| 11 | Migração Cadastros (8 forms) para `app-form-section`/`app-form-grid` | ✅ |
| 12 | Wizard de Ofícios: `app-wizard__*`, `app-stepper__*` | ✅ |
| 13 | `wizard_roteiro.html` com classes canônicas | ✅ |
| 14 | Dashboard: `app-page`, `app-section`, `app-card` em paralelo | ✅ |
| 15 | Aliases `.app-form-*`, `.app-wizard`, `.app-stepper` em `forms.css` | ✅ |
| 16 | Remoção de 6 arquivos legados | ✅ |
