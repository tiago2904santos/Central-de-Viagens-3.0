from dataclasses import dataclass
from typing import Mapping
from typing import Protocol

from .types import DocumentoTipo


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()


class DocumentValidator(Protocol):
    tipo: DocumentoTipo

    def validate(self, payload: Mapping[str, object]) -> ValidationResult:
        ...


def ensure_required_fields(payload: Mapping[str, object], required_fields: tuple[str, ...]) -> ValidationResult:
    errors: list[str] = []
    for field in required_fields:
        value = payload.get(field)
        if value in (None, "", []):
            errors.append(f"Campo obrigatório ausente: {field}")
    return ValidationResult(ok=not errors, errors=tuple(errors))


class NoopDocumentValidator:
    def __init__(self, tipo: DocumentoTipo):
        self.tipo = tipo

    def validate(self, payload: Mapping[str, object]) -> ValidationResult:
        _ = payload
        return ValidationResult(ok=True, errors=())
# Validadores de documentos serao implementados aqui.
