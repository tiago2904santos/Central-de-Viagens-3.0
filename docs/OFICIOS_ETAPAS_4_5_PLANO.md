# Plano técnico — Etapas 4 e 5 do wizard de Ofício

Documento de auditoria, contrato funcional e ordem de implementação.  
**Estado da última revisão:** baseline antes da implementação das etapas Justificativa (4) e Documentos (5).

---

## 1. Contrato funcional do wizard (alvo)

| Etapa | Nome | Key sugerida | URL alvo |
|-------|------|--------------|----------|
| 1 | Dados e viajantes | `dados_viajantes` | `/oficios/<pk>/dados-viajantes/` |
| 2 | Transporte | `transporte` | `/oficios/<pk>/transporte/` |
| 3 | Roteiro e diárias | `roteiro` | `/oficios/<pk>/roteiro/` |
| 4 | Justificativa | `justificativa` | `/oficios/<pk>/justificativa/` |
| 5 | Documentos / Resumo final | `documentos` | `/oficios/<pk>/documentos/` |

- **Etapa 4 = Justificativa** (condicional/obrigatória conforme regra de prazo).
- **Etapa 5 = Documentos / Resumo final** (validação, DOCX/PDF, finalização).
- **Compatibilidade:** a rota existente `oficios:wizard_resumo` (`/oficios/<pk>/resumo/`) deve redirecionar para a etapa 5 ou renderizar o mesmo conteúdo, sem quebrar bookmarks.
- **Downloads:** manter `path("<int:pk>/documentos/<str:formato>/", baixar_documento)` — registrar a **tela** `/<pk>/documentos/` **antes** ou garantir padrões distintos (três segmentos na URL de download evitam colisão com a lista `/documentos/`).

---

## 2. Estado atual — rotas (`oficios/urls.py`)

| Rota | Name | Observação |
|------|------|------------|
| `<pk>/dados-viajantes/` | `dados_viajantes` | OK |
| `<pk>/transporte/` | `transporte` | OK |
| `<pk>/roteiro/` | `wizard_roteiro` | OK |
| `<pk>/resumo/` | `wizard_resumo` | Hoje é o “passo 4” no stepper (título “Resumo do ofício”); virará compatibilidade com etapa 5 |
| `<pk>/documentos/<formato>/` | `baixar_documento` | Download; não é tela do wizard |
| **Ausente** | — | `/justificativa/` |
| **Ausente** | — | `/documentos/` (GET tela resumo) |

---

## 3. Estado atual — stepper (`oficios/presenters.py`)

- Cinco entradas: `dados_viajantes`, `transporte`, `roteiro`, **`resumo`** (número 4), **`documentos`** (número 5).
- O passo **documentos** aponta para `reverse("oficios:detalhe", …)` — placeholder, não é fluxo do wizard.
- **Não existe** passo `justificativa`; o número 4 é “Resumo do ofício”.
- Headers (`apresentar_oficio_wizard_header`): não inclui `justificativa`; etapa 4 textual = “Resumo do ofício”.

**Lacuna:** inserir etapa **Justificativa** como 4; renumerar **Documentos** (resumo final) como 5; remover ou substituir key `resumo` por `justificativa` + `documentos` com URLs corretas.

---

## 4. Fluxo atual — após etapa 3

- `wizard_roteiro`: em `save_continue` válido → **sempre** `redirect("oficios:wizard_resumo")`.
- **Lacuna:** decisão condicional — se justificativa obrigatória → `wizard_justificativa`; senão → etapa 5 (`wizard_documentos` ou temporariamente `wizard_resumo`).

---

## 5. App `justificativas` — lacunas

- `models.py`: apenas TODOs; sem schema persistido.
- `services.py`: vazio.
- Sem forms/selectors/presenters/testes de domínio.

---

## 6. Onde estão as datas de saída (`roteiros/models.py`)

- **`Roteiro.saida_dt`:** DateTimeField — primeira saída “global” do roteiro quando preenchida.
- **`RoteiroTrecho.saida_dt`:** DateTimeField por trecho; ordenação por `ordem`.
- **Identificar a primeira saída (contrato):**
  1. Se `roteiro.saida_dt` estiver preenchido → usar esse datetime (normalizado para data na regra).
  2. Caso contrário, entre trechos do roteiro ordenados por `ordem`, usar o primeiro `saida_dt` não nulo.

---

## 7. Regra exata — 10 dias corridos

**Campo de referência da data do ofício:** `Oficio.data_criacao` (**DateField** de domínio).  
**Não usar** `created_at` / `updated_at` do `TimeStampedModel` para esta regra.

Seja `D0 = oficio.data_criacao` e `S = primeira_data_saida` (extraída da primeira saída efetiva em datetime, depois `.date()` em UTC local conforme implementação).

Antecedência em dias (inteiro):

`delta = (S - D0).days`

- **Justificativa obrigatória** quando `delta <= prazo_dias` (padrão **10**, inclusive o 10º dia), **ou** quando a saída é **anterior** à data de criação (`delta < 0` → tratar como obrigatória).
- **Não obrigatória** quando `delta > prazo_dias`.
- **Indeterminado / não avaliável:** sem roteiro vinculado ou sem `saida_dt` resolvível — **não** marcar obrigatória pela regra de prazo; etapa roteiro segue incompleta até haver dados.

**Configuração:** `cadastros.ConfiguracaoSistema.prazo_justificativa_dias` existe no 3.0; service deve usar `get_singleton()` com fallback **10** (sem criar campo novo).

---

## 8. Comportamento da etapa 4 quando **exigida**

- Stepper: etapa acessível; status **incompleta** até texto válido quando obrigatória.
- Formulário: texto obrigatório; modelo opcional.
- “Salvar e continuar” só avança para etapa 5 se regra satisfeita (texto preenchido).
- DOCX/PDF/finalização (etapa futura): bloqueados se obrigatória e vazia.

---

## 9. Comportamento da etapa 4 quando **não exigida**

- Após etapa 3, fluxo pode **pular** direto para etapa 5.
- Stepper: exibir **“Não exigida”** / **“Dispensada”** (rótulo equivalente) para o passo justificativa.
- Tela pode permitir justificativa **opcional**; avanço sem texto permitido.

---

## 10. Etapa 5 — validação consolidada

- Avaliar: dados/viajantes, transporte, roteiro/diárias, justificativa (se obrigatória), prontidão documental.
- Listar **pendências** objetivas.
- Ações: Voltar, DOCX, PDF, Salvar rascunho, **Finalizar ofício** (POST `action=finalizar`).
- **Finalizar** só se `validar_oficio_para_documento` (ou equivalente) retornar completo.

---

## 11. Artefatos a criar ou alterar (por camada)

| Área | Criar / alterar |
|------|-----------------|
| Docs | Este arquivo; depois `OFICIOS_REGRAS_NEGOCIO`, `JUSTIFICATIVAS_PLANO` |
| `justificativas/` | `services` (regra), `models`, `forms`, `selectors`, `presenters`, `admin`, `tests/` |
| `oficios/` | `urls`, `views`, `presenters`, `services` (validação unificada), testes wizard |
| Templates | `wizard_justificativa.html`, `wizard_documentos.html`; partials se necessário |
| Estáticos | `static/css/oficios.css` (etapas 4–5) |

---

## 12. Testes a criar (visão geral)

- **Justificativas:** regra de dias, timezone aware, trechos, ausência de roteiro.
- **Models:** OneToOne, modelo padrão, normalização de texto.
- **Services/forms:** rascunho vs finalizada, snapshots, completude.
- **Ofícios:** redirects etapa 3→4/5, GET etapa 4/5, stepper, bloqueio download e finalizar.

---

## 13. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Quebrar DOCX/PDF | Alterar validação/redirect; não alterar pipeline de bytes sem necessidade |
| Quebrar wizard | Manter nomes de URL antigos com redirect (`wizard_resumo`) |
| Duplicar Justificativa | `OneToOne` com `Oficio` |
| Regra no template | Toda decisão em **service** |
| Mudar regra sem teste | Testes por cenário na pasta `justificativas/tests` e `oficios/tests` |
| `data_criacao` vs `created_at` | Usar apenas **`data_criacao`** na regra |
| Timezone | Datetimes aware; comparar `.date()` de forma consistente |

---

## 14. Ordem de implementação recomendada

1. Regra pura + testes (`justificativas/services.py`).
2. Models + migrations + admin + testes de model.
3. Forms/selectors/services/presenters + testes.
4. Integração wizard: URLs, views, redirect roteiro, stepper, template mínimo etapa 4.
5. UI premium etapa 4.
6. Etapa 5 `/documentos/` + compat `resumo`.
7. Validação unificada + bloqueios download/finalizar.
8. Documentação final + auditoria frontend + regressão.

---

## 15. Pendências identificadas (baseline)

- Stepper e URLs não refletem Justificativa + Documentos como produto final.
- Validação documental incompleta (sem roteiro/transporte/justificativa).
- App `justificativas` sem dados persistidos.
