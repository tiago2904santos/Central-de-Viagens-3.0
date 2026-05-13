# Relatório — Fase 1 (Ofícios, documentos e assinaturas)

Resumo das alterações integradas (P1, P2, P3, P4, P7, P5, P6) e validação final.

## Validação automática

- `python manage.py check` (com `DJANGO_SETTINGS_MODULE=config.settings.test` quando aplicável).
- `python manage.py makemigrations --check --dry-run`.
- `python manage.py test`.

## Correções manuais do cadastro de Ofícios

### 1. Sede na etapa 3 sem origem salva

- **Problema:** Roteiro persistido sem origem deixava a sede vazia no GET.
- **Solução:** Resolver sede a partir de `ConfiguracaoSistema` e aplicar em `roteiro_logic` quando origem vazia.
- **Ficheiros:** `cadastros/services.py`, `roteiros/roteiro_logic.py`, `oficios/tests/test_wizard_roteiro_diarias.py`
- **Teste manual:** Configurar sede; abrir ofício sem origem; confirmar pré-preenchimento.
- **Pendências:** Coordenadas na cidade da sede para o mapa.

### 2. Rota sem coordenadas

- **Problema:** Erro genérico sem município/UF.
- **Solução:** `RouteCoordinateError` contextual.
- **Ficheiros:** `roteiros/services/routing/*`, `roteiros/tests/test_routing.py`
- **Teste manual:** Cidade sem lat/lng; ver mensagem explícita.

### 3. Tempos HH:mm

- **Problema:** UX de tempos e passo de 1 minuto.
- **Solução:** Máscara live, ±15 min, minutos no hidden.
- **Ficheiros:** `static/js/pages/roteiros/editor/index.js`, `templates/roteiros/partials/roteiro/retorno.html`

### 4. Capitalização DOCX

- **Problema:** `title()` agressivo.
- **Solução:** `format_institucional_rodape_linha` e contextos DOCX.
- **Ficheiros:** `documentos/services/formatters.py`, `oficios/docxtpl_context.py`, `termos/services.py`, testes associados.

### 5. Rodapé wizard e finalização

- **Problema:** Voltar sem POST; completude vs assinatura.
- **Solução:** `wizard_back` / `wizard_next` / `save_draft_list`; `oficio_esta_completo_para_finalizar`; chips na lista.
- **Ficheiros:** `oficios/views.py`, `oficios/services.py`, `oficios/selectors.py`, `oficios/presenters.py`, templates wizard, `roteiros/.../actions.html`, `static/css/oficios.css`
- **Pendências:** Etapa 6 central mantém link GET «Voltar para documentos».

### 6. Página pública de assinatura

- **Problema:** Overflow e PDF pouco nítido.
- **Solução:** CSS de painel; PDF.js com DPR até 2.
- **Ficheiros:** `static/css/signature-public.css`, `static/js/pages/assinatura-pdf.js`

### 7. Etiqueta PDF

- **Problema:** Hash visível como código; URL cortada.
- **Solução:** Filtrar prefixo SHA-256 de 12 hex; quebra de URL; rótulo «Validação» quando URL contém `verificar`; `code_short` vazio no workflow de etiqueta.
- **Ficheiros:** `documentos/services/signing/label_overlay.py`, `workflow.py`, `documentos/tests/test_signature_label.py`
- **Pendências:** Fluxo `carimbo_pdf` para assinatura por pedido.

**Data:** 2026-05-12.

## Nota sobre a suíte completa

python manage.py test em todo o projecto falhou em testes de cadastros (URLs estado_delete / vistas protegidas por login) não relacionados com esta fase. Os módulos **oficios**, **roteiros**, **documentos**, **assinaturas** e **justificativas** passaram em conjunto (357 testes, 1 skipped).

