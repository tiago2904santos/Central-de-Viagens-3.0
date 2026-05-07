"""
Contratos de modelo para o app `oficios`.

Este módulo existe para registrar, com precisão técnica, o escopo da próxima
implementação de domínio sem criar schema por adivinhação nesta fase.
"""

# TODO(fase-oficios-model): definir entidade principal de Ofício com número,
# protocolo, status e referências opcionais para roteiro/evento conforme
# mapeamento funcional em `docs/LEGACY_VIEWS_MAP.md`.
#
# TODO(fase-oficios-model): modelar vínculo explícito entre Ofício e
# justificativa/termo/plano/ordem via contratos de domínio, após aprovação do
# schema em documento de arquitetura.
#
# TODO(fase-oficios-model): estabelecer estratégia de snapshots de consistência
# documental sem acoplar diretamente ao núcleo `documentos/services/`.
