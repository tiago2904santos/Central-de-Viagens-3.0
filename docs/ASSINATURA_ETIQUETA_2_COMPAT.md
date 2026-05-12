# Assinatura com etiqueta eletrónica — compatibilidade com o CV 2.0 (auditoria)

Este documento regista o estado do repositório **Central de Viagens 3.0** na fase de auditoria para alinhar a etiqueta visual de assinatura ao comportamento conceitual do CV 2.0 (`feature/gestao-completa-assinaturas`), **sem** importar código legacy nem referenciar paths do 2.0 em runtime.

## Estado atual — `documentos.DocumentoArtefato`

- `arquivo` (`FileField`): PDF (ou outro) gerado; `upload_to=documentos/gerados/...`
- `arquivo_assinado` (`FileField`, opcional): versão assinada; `upload_to=documentos/assinados/...`
- `hash_sha256`: digest SHA-256 do ficheiro original
- `hash_sha256_assinado`: digest após assinatura (quando aplicável)
- `assinatura_backend`: identificador textual do motor (ex.: fluxo pyHanko existente)
- `assinado_em`: data/hora da conclusão da assinatura
- `formato`, `tipo`, relações opcionais (`oficio`, `servidor`), metadados de geração

**Conclusão:** o modelo já suporta persistência de PDF original, PDF assinado e hashes; a integração da etiqueta deve atualizar `arquivo_assinado`, `hash_sha256_assinado`, `assinatura_backend` (valor previsto: `etiqueta_pdf`) e `assinado_em`.

## Estado atual — app `assinaturas`

### `INSTALLED_APPS`

- `assinaturas` está registado em `config.settings.base`.

### Modelos (`assinaturas/models.py`)

- `ConfiguracaoChaveAssinatura`: chaves PKCS#12/11 para assinatura criptográfica (pyHanko).
- `AssinaturaDigital`: FK a `DocumentoArtefato`, `status`, hashes (`hash_documento`, `hash_documento_assinado`), `appearance`, `evidencias`, dados de signatário criptográfico (`signer_subject`, `signer_serial`), `signature_field_name`, FK opcional `chave`.
- `EventoAssinatura`: histórico de eventos por assinatura.

**Em falta para a etiqueta + verificação por código (fases seguintes):** `codigo_verificacao`, dados do assinante humano (nome, CPF, email), método de autenticação, IP, user-agent, posição do carimbo (JSON + página), `url_validacao`.

### Rotas (`assinaturas/urls.py` + `config/urls.py`)

- Prefixo `/assinaturas/`: página índice, APIs JSON `api/documentos/<uuid>/verificar/` e `api/documentos/<uuid>/assinar/` (fluxo atual via `assinar_pdf_final` / pyHanko).

### Serviços existentes

- `assinaturas/services/recording.py`: cria `AssinaturaDigital` após `atualizar_apos_assinatura` com meta do signing.
- `assinaturas/services/verification.py`: valida assinaturas **embutidas** no PDF (pyHanko) e confronta hash persistido.

**Risco:** PDFs assinados apenas com etiqueta visual + metadados podem não passar na validação criptográfica atual; será necessário ramificar por `assinatura_backend` ou equivalente nas fases finais.

### Admin

- Registo de `ConfiguracaoChaveAssinatura`, `AssinaturaDigital` com inline de eventos.

### Templates / estilos

- `templates/base.html` inclui `static/css/style.css` (imports modulares). Novas telas de assinatura/verificação devem reutilizar tokens e evitar CSS solto nos templates.

## Dependências (`requirements/base.txt`)

- Já presentes: `pypdf` (intervalo atual `<6`), `reportlab`, `qrcode`, `Pillow`, `pyhanko`, etc.
- **Plano técnico:** alinhar `pypdf` e `reportlab` às versões pedidas para o carimbo (`pypdf>=6.10,<7`, `reportlab>=4.4,<5`) e correr testes de `documentos` e `assinaturas` após o bump.

## Asset de marca d’água

- **Destino:** `static/img/assinatura/cv-watermark.png` (a criar na fase 2; conteúdo equivalente ao do 2.0, copiado para dentro deste repositório).

## Lista de ficheiros previstos (próximas fases)

| Fase | Criar / alterar |
|------|-----------------|
| Dependências | `requirements/base.txt` |
| Serviços | `assinaturas/services/hash.py`, `codigos.py`, `carimbo_pdf.py` (complementar a `keys.py`, `recording.py`, `verification.py`) |
| Estático | `static/img/assinatura/cv-watermark.png` |
| Modelo | `assinaturas/models.py`, migração `assinaturas/migrations/` |
| Serviço artefato | `assinaturas/services/assinatura_artefato.py`, `assinaturas/services/__init__.py` |
| HTTP | `assinaturas/urls.py`, `assinaturas/views.py` |
| Templates | `templates/assinaturas/verificar_codigo.html`, `templates/assinaturas/assinar_artefato.html` |
| CSS | `static/css/style.css` ou novo ficheiro importado (classes `assinatura-*`) |
| Integração UI | templates em `documentos/`, `oficios/`, outros domínios onde `DocumentoArtefato` apareça |
| Testes | `assinaturas/tests/test_carimbo_pdf.py`, `test_codigos.py`, `test_assinatura_artefato.py`, `test_views_verificacao.py`, ajustes em `documentos/tests/` se necessário |
| Comando | `assinaturas/management/commands/diagnosticar_assinatura_pdf.py` |
| Documentação | atualizações a este ficheiro após hardening |

## Riscos

1. **Dois backends de assinatura:** pyHanko (existente) vs etiqueta PDF; conflitos de expectativa na API de verificação e na UI.
2. **Upgrade `pypdf`:** possível impacto em `documentos.services.signing` e dependências; mitigar com testes completos.
3. **Exposição pública de PDFs:** rotas de verificação por código vs servir PDF inline — equilibrar transparência e vazamento de dados; documentar decisão nas fases 6–9.
4. **Re-assinatura:** artefato já com `arquivo_assinado`; definir se nova etiqueta substitui ou bloqueia (produto).

## Critérios de aceite finais (resumo)

- Etiqueta com dimensões e estilo conforme especificação (155×54 pt, QR 42 pt, cores, fontes Times, watermark local, posição padrão última página, margem inferior mínima).
- Código de verificação no formato `CV-AAAA-XXXXXX-XXXX`, único na BD.
- `DocumentoArtefato` atualizado com ficheiro assinado e hashes; `AssinaturaDigital` como registo principal (sem model duplicado tipo `AssinaturaDocumento`).
- Página pública de verificação por código; PDFs servidos com `Content-Type: application/pdf` e `Content-Disposition: inline` onde aplicável.
- Tela de posicionamento exige autenticação; PDF final gerado no servidor (ReportLab/PyPDF), não por captura do browser.
- Alteração do bytes do PDF assinado invalida a verificação de integridade.
- `python manage.py check` e testes `assinaturas` + `documentos` (e `oficios` quando integrado) passam.
- Nenhum import nem path runtime para o repositório 2.0 ou `legacy/`.

## Nota legal / produto

Assinatura eletrónica interna com etiqueta e hash de integridade **não** equivale a certificado ICP-Brasil; integração futura com certificado qualificado seria outro epic.
