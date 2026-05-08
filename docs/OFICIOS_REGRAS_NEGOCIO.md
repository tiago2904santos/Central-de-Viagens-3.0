# Regras de negócio de Ofícios

## REG-OF-001 — Numeração anual incremental por menor lacuna
- Descrição: ao criar ofício sem número, o sistema reserva o próximo número disponível no ano, com retry para concorrência.
- Origem no legacy: `eventos/models.py` (`Oficio.get_next_available_numero`, `Oficio.save`).
- Arquivos/funções: model `Oficio`.
- Estado no 3.0: parcial (incremento simples).
- Adaptação correta: mover para service transacional e manter constraint `(ano, numero)`.
- Prioridade: Alta.
- Riscos: colisão de número em concorrência.
- Testes necessários: concorrência e criação sequencial no mesmo ano.

## REG-OF-002 — Protocolo canônico e visual
- Descrição: protocolo é persistido em dígitos e exibido em máscara `XX.XXX.XXX-X`.
- Origem no legacy: `core/utils/masks.py`, `eventos/models.py`.
- Arquivos/funções: `normalize_protocolo`, `format_protocolo`, `Oficio.clean`.
- Estado no 3.0: parcial.
- Adaptação correta: normalizador único + validação de tamanho + formatter em presenter.
- Prioridade: Alta.
- Riscos: inconsistência entre persistência e UI.
- Testes necessários: entrada mascarada, entrada sem máscara e exibição.

## REG-OF-003 — Custeio “outra instituição” exige detalhamento
- Descrição: quando custeio for externo, o nome da instituição é obrigatório.
- Origem no legacy: `eventos/models.py` (`Oficio.clean`).
- Arquivos/funções: `custeio_tipo`, `nome_instituicao_custeio`.
- Estado no 3.0: implementado no form mínimo.
- Adaptação correta: manter em form + service e refletir no payload documental.
- Prioridade: Alta.
- Riscos: documento incompleto juridicamente.
- Testes necessários: validação condicional no form e persistência.

## REG-OF-004 — Motorista carona exige protocolo específico
- Descrição: quando motorista for carona, protocolo do motorista torna-se obrigatório e validado.
- Origem no legacy: `eventos/models.py`.
- Arquivos/funções: `motorista_carona`, `motorista_protocolo`.
- Estado no 3.0: não implementado.
- Adaptação correta: regra explícita em fase de transporte.
- Prioridade: Média.
- Riscos: inconsistência documental de deslocamento.
- Testes necessários: cenário carona com/sem protocolo.

## REG-OF-005 — Assunto automático (autorização vs convalidação)
- Descrição: tipo de assunto é inferido por comparação entre data do ofício e primeira saída.
- Origem no legacy: `Oficio.compute_assunto_tipo`.
- Arquivos/funções: método de domínio.
- Estado no 3.0: não implementado.
- Adaptação correta: regra em service/presenter, sem lógica em template.
- Prioridade: Média.
- Riscos: emissão com assunto incorreto.
- Testes necessários: casos antes/depois da saída.

## REG-OF-006 — Modo de roteiro (salvo vs próprio)
- Descrição: ofício pode usar roteiro existente do evento ou roteiro próprio no ofício.
- Origem no legacy: `Oficio.roteiro_modo`, `views.py` step3.
- Arquivos/funções: model + views/forms.
- Estado no 3.0: parcial (apenas vínculo de roteiro).
- Adaptação correta: manter roteiro opcional com fonte explícita e sync seguro.
- Prioridade: Alta.
- Riscos: perda de coerência entre rota exibida e documento.
- Testes necessários: ambos modos e troca de modo.

## REG-OF-007 — Trechos de ida e retorno com semânticas distintas
- Descrição: ida fica em coleção de trechos; retorno em campos dedicados.
- Origem no legacy: `OficioTrecho` + campos `retorno_*` em `Oficio`.
- Arquivos/funções: model e lógica de resumo.
- Estado no 3.0: não implementado.
- Adaptação correta: estruturar entidades de trecho e retorno sem duplicidade.
- Prioridade: Alta.
- Riscos: cálculo incorreto de período/diárias.
- Testes necessários: múltiplos trechos, retorno ausente/presente.

## REG-OF-008 — Diárias calculadas por período e destino
- Descrição: quantidade/valor/extenso dependem de datas, trecho e tipo de destino.
- Origem no legacy: `eventos/services/diarias.py`, `views.py`.
- Arquivos/funções: cálculo de diárias e endpoints.
- Estado no 3.0: não implementado.
- Adaptação correta: service puro no domínio com saída para payload documental.
- Prioridade: Alta.
- Riscos: impacto financeiro e retrabalho manual.
- Testes necessários: cenários PR/fora PR, ida/volta e períodos distintos.

## REG-OF-009 — Justificativa por prazo mínimo
- Descrição: ofício exige justificativa quando antecedência é menor que o prazo configurado.
- Origem no legacy: `eventos/services/justificativa.py`, `ConfiguracaoSistema.prazo_justificativa_dias`.
- Arquivos/funções: funções de prazo e presença de justificativa.
- Estado no 3.0: não implementado.
- Adaptação correta: regra em service com configuração central.
- Prioridade: Alta.
- Riscos: descumprimento normativo.
- Testes necessários: antecedência acima/abaixo do limite.

## REG-OF-010 — Geração de Termo por modalidade
- Descrição: termo pode ser rápido, automático com viatura ou automático sem viatura.
- Origem no legacy: `TermoAutorizacao`, `services/documentos/termo_autorizacao.py`.
- Arquivos/funções: inferência de modo e template variant.
- Estado no 3.0: não implementado.
- Adaptação correta: app `termos` desacoplado, consumindo núcleo documental.
- Prioridade: Alta.
- Riscos: lote documental inconsistente.
- Testes necessários: cada modalidade e seleção por servidor.

## REG-OF-011 — PT e OS reutilizam contexto do Ofício
- Descrição: plano de trabalho e ordem de serviço derivam parte do contexto de ofício/evento/roteiro.
- Origem no legacy: `PlanoTrabalho`, `OrdemServico`, `views_global.py`, services documentais.
- Arquivos/funções: resolução de contexto e downloads.
- Estado no 3.0: não implementado.
- Adaptação correta: entidades independentes com vínculo opcional.
- Prioridade: Média.
- Riscos: acoplamento excessivo ou duplicação de dados.
- Testes necessários: geração com e sem vínculo de ofício.

## REG-OF-012 — Geração documental condicionada a status de prontidão
- Descrição: documento só é gerado se tipo, formato, template, backend e validações estiverem OK.
- Origem no legacy: `eventos/services/documentos/validators.py`.
- Arquivos/funções: `get_document_generation_status`.
- Estado no 3.0: parcial via núcleo V1.1.
- Adaptação correta: manter status preditivo e erros explícitos.
- Prioridade: Alta.
- Riscos: download de documento inválido.
- Testes necessários: estados available/pending/unavailable.

## REG-OF-013 — Placeholders obrigatórios e não resolvidos
- Descrição: placeholders necessários devem existir e nenhum placeholder pode escapar sem substituição.
- Origem no legacy: `renderer.py` + template mapping.
- Arquivos/funções: extração/substituição placeholder.
- Estado no 3.0: implementado no núcleo documental.
- Adaptação correta: manter contrato no núcleo e reforçar nos tipos documentais.
- Prioridade: Alta.
- Riscos: documento com marcadores visíveis.
- Testes necessários: missing placeholder e unresolved placeholder.

## REG-OF-014 — Assinaturas e contexto institucional por tipo documental
- Descrição: cada documento usa assinatura/configuração específica.
- Origem no legacy: `ConfiguracaoSistema`, `AssinaturaConfiguracao`, `context.py`.
- Arquivos/funções: builders institucionais e assinatura por tipo.
- Estado no 3.0: base existente em `cadastros`.
- Adaptação correta: selector central institucional + consumo por payload.
- Prioridade: Alta.
- Riscos: assinatura incorreta em documento oficial.
- Testes necessários: fallback, ausência de assinatura e troca de tipo.

## REG-OF-015 — PDF depende de ambiente e fallback
- Descrição: geração PDF depende de backend e pode falhar por ambiente; erro deve ser explícito.
- Origem no legacy: `eventos/services/documentos/backends.py`, `renderer.py`.
- Arquivos/funções: disponibilidade DOCX/PDF e fallback COM.
- Estado no 3.0: contrato parcialmente previsto.
- Adaptação correta: manter check de disponibilidade e mensagens claras.
- Prioridade: Média.
- Riscos: produção sem PDF operacional.
- Testes necessários: backend indisponível e fallback.

## REG-OF-016 — Autosave em formulários longos
- Descrição: alterações em wizard são salvas automaticamente com debounce e beacon.
- Origem no legacy: `static/js/oficio_wizard.js`, `views.py`.
- Arquivos/funções: `createAutosave`.
- Estado no 3.0: não implementado.
- Adaptação correta: autosave opcional por página, sem acoplamento global.
- Prioridade: Média.
- Riscos: perda de dados em formulários extensos.
- Testes necessários: autosave por input, navegação e abandono de página.

