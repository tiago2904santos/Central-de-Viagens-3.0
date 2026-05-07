# Plano de Implementação — Justificativas

## Escopo

Estruturar o app `justificativas` para fluxo global e por Ofício, com regras de prazo e modelos de texto.

## Dependências

- `oficios` para vínculo contextual.
- `documentos/services/` para geração quando houver artefato documental.

## Arquivos-alvo (fases futuras)

- `justificativas/models.py`
- `justificativas/forms.py`
- `justificativas/selectors.py`
- `justificativas/services.py`
- `justificativas/presenters.py`
- `justificativas/views.py`

## Ordem recomendada

1. Definir schema de justificativa + modelos de texto.
2. Implementar serviços de regra de prazo e obrigatoriedade.
3. Implementar forms e validações de vínculo.
4. Implementar CRUD e integração com Ofício.
