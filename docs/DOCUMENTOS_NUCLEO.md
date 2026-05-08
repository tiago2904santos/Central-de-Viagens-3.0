# Documentos Núcleo V1

## Objetivo

Consolidar `documentos/services` como infraestrutura documental reutilizável, sem CRUD completo de domínio e sem dependência de runtime em `legacy/`.

## API pública

- `DocumentoTipo`, `DocumentoFormato`, `DocumentoTipoDefinicao`;
- `DocumentoRegistry`, `default_document_registry`;
- `DocumentTemplateDefinition`, `DocumentTemplateRegistry`, `default_template_registry`;
- `ValidationResult`, `DocumentValidatorRegistry`, `ensure_required_fields`;
- `extract_placeholders`, `ensure_required_placeholders`, `ensure_no_unresolved_placeholders`;
- `DocumentRenderRequest`, `DocumentRenderResult`, `DocumentRenderer`, `NoopDocumentRenderer`, `render_document`;
- `build_document_filename`;
- `build_download_response`;
- exceções de núcleo (`DocumentError` e subclasses).

## Fluxo técnico padrão

1. app de domínio (ex.: `oficios`) monta `payload`;
2. valida campos obrigatórios e regras específicas por tipo;
3. seleciona tipo/formato suportado no registry;
4. resolve template e placeholders obrigatórios;
5. chama `render_document(...)` com renderer apropriado;
6. retorna download com `build_download_response(...)`.

## Consumo futuro por Ofícios

`oficios/services.py` deve orquestrar:

- validação funcional do ofício (número, assunto, período, assinatura etc.);
- construção de payload;
- chamada ao núcleo em `documentos/services`;
- retorno HTTP pela view apenas com resposta final e mensagens.

Assim, regras documentais ficam desacopladas de request/template HTML e permanecem reutilizáveis por `termos`, `justificativas`, `planos_trabalho` e `ordens_servico`.

## Fora de escopo desta fase

- CRUD completo de Ofícios;
- geração DOCX final de produção;
- conversão PDF por stack externa obrigatória;
- templates DOCX definitivos de cada domínio;
- mudanças visuais em Roteiros.
