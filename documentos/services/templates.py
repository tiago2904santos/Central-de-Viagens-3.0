from dataclasses import dataclass

from .exceptions import DocumentTemplateNotFound
from .types import DocumentoFormato
from .types import DocumentoTipo


@dataclass(frozen=True)
class DocumentTemplateDefinition:
    tipo: DocumentoTipo
    formato: DocumentoFormato
    template_path: str
    required_placeholders: tuple[str, ...] = ()


class DocumentTemplateRegistry:
    def __init__(self):
        self._items: dict[tuple[DocumentoTipo, DocumentoFormato], DocumentTemplateDefinition] = {}

    def register(self, definition: DocumentTemplateDefinition) -> None:
        key = (definition.tipo, definition.formato)
        self._items[key] = definition

    def get(self, tipo: DocumentoTipo, formato: DocumentoFormato) -> DocumentTemplateDefinition:
        key = (tipo, formato)
        if key not in self._items:
            raise DocumentTemplateNotFound(
                f"Template não encontrado para tipo={tipo.value} e formato={formato.value}",
            )
        return self._items[key]


def build_default_template_registry() -> DocumentTemplateRegistry:
    registry = DocumentTemplateRegistry()
    for tipo in DocumentoTipo:
        registry.register(
            DocumentTemplateDefinition(
                tipo=tipo,
                formato=DocumentoFormato.DOCX,
                template_path=f"documentos/{tipo.value}.docx",
                required_placeholders=(),
            ),
        )
    return registry


default_template_registry = build_default_template_registry()
