from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Mapping

from django.conf import settings

from documentos.services.adapters.docxtpl_render import render_docx_bytes
from documentos.services.adapters.libreoffice_pdf import convert_docx_to_pdf_libreoffice
from documentos.services.exceptions import DocumentValidationError
from documentos.services.filenames import build_document_filename
from documentos.services.registry import default_document_registry
from documentos.services.resources_paths import resolve_resource_docx
from documentos.services.responses import get_content_type_for_format
from documentos.services.templates import DocumentTemplateDefinition
from documentos.services.templates import canonical_required_keys
from documentos.services.templates import default_template_registry
from documentos.services.types import DocumentoFormato
from documentos.services.types import DocumentoTipo
from documentos.services.libreoffice_resolve import resolve_libreoffice_binary
from documentos.services.validators import DocumentValidatorRegistry
from documentos.services.validators import ensure_required_fields

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentoGerado:
    tipo: DocumentoTipo
    formato: DocumentoFormato
    nome_arquivo: str
    content_type: str
    conteudo: bytes
    hash_sha256: str


class DocumentoFacade:
    def __init__(
        self,
        *,
        template_registry=default_template_registry,
        document_registry=default_document_registry,
        validator_registry: DocumentValidatorRegistry | None = None,
    ):
        self._templates = template_registry
        self._document_registry = document_registry
        self._validators = validator_registry or DocumentValidatorRegistry()

    def gerar(
        self,
        *,
        tipo: DocumentoTipo,
        formato: DocumentoFormato,
        payload: Mapping[str, object],
        reference: str | None = None,
        docxtpl_context: Mapping[str, object] | None = None,
    ) -> DocumentoGerado:
        if not self._document_registry.has(tipo):
            from documentos.services.exceptions import UnsupportedDocumentType

            raise UnsupportedDocumentType(f"Tipo documental não suportado: {tipo.value}")
        type_def = self._document_registry.get(tipo)
        if not type_def.supports_format(formato):
            from documentos.services.exceptions import UnsupportedDocumentFormat

            raise UnsupportedDocumentFormat(
                f"Formato {formato.value} não permitido para {tipo.value}",
            )
        template_def = self._templates.get(tipo, formato)
        self._validate_payload(tipo, payload)
        docx_ctx = docxtpl_context if docxtpl_context is not None else payload
        if formato == DocumentoFormato.DOCX:
            conteudo = self._render_docx(template_def, docx_ctx)
        else:
            conteudo = self._render_pdf(tipo, template_def, payload, docxtpl_context=docxtpl_context)

        digest = hashlib.sha256(conteudo).hexdigest()
        nome = build_document_filename(tipo, formato, reference=reference)
        return DocumentoGerado(
            tipo=tipo,
            formato=formato,
            nome_arquivo=nome,
            content_type=get_content_type_for_format(formato),
            conteudo=conteudo,
            hash_sha256=digest,
        )

    def _validate_payload(
        self,
        tipo: DocumentoTipo,
        payload: Mapping[str, object],
    ) -> None:
        v = self._validators.validate(tipo, payload)
        if not v.ok:
            raise DocumentValidationError("; ".join(v.errors))
        req = ensure_required_fields(payload, canonical_required_keys(tipo))
        if not req.ok:
            raise DocumentValidationError("; ".join(req.errors))

    def _render_docx(
        self,
        template_def: DocumentTemplateDefinition,
        payload: Mapping[str, object],
    ) -> bytes:
        path = resolve_resource_docx(template_def.template_path)
        if not path.exists():
            raise FileNotFoundError(f"Template DOCX ausente: {path}")
        return render_docx_bytes(template_path=path, context=payload)

    def _render_pdf(
        self,
        tipo: DocumentoTipo,
        template_def: DocumentTemplateDefinition,
        payload: Mapping[str, object],
        *,
        docxtpl_context: Mapping[str, object] | None = None,
    ) -> bytes:
        engine = (
            getattr(settings, "DOCUMENTOS_DEFAULT_PDF_ENGINE", "weasyprint") or "weasyprint"
        ).lower()
        if engine == "libreoffice":
            return self._pdf_via_libreoffice(tipo, payload, docxtpl_context=docxtpl_context)
        if engine == "weasyprint":
            from documentos.services.adapters.simple_pdf_fallback import render_simple_pdf_bytes
            from documentos.services.adapters.weasyprint_pdf import render_pdf_bytes_weasyprint

            # Ofício: o HTML do WeasyPrint não recebe o dict plano do docxtpl; gera-se o PDF a partir
            # do mesmo DOCX preenchido que o utilizador valida (LibreOffice), salvo desactivação explícita.
            if (
                getattr(settings, "DOCUMENTOS_OFICIO_PDF_VIA_DOCX", True)
                and tipo == DocumentoTipo.OFICIO
                and docxtpl_context is not None
            ):
                return self._pdf_via_libreoffice(tipo, payload, docxtpl_context=docxtpl_context)

            simple_ok = getattr(settings, "DOCUMENTOS_SIMPLE_PDF_FALLBACK", False)

            try:
                return render_pdf_bytes_weasyprint(
                    html_template_name=template_def.template_path,
                    context=payload,
                    stylesheet_paths=template_def.stylesheet_paths,
                )
            except (OSError, RuntimeError) as exc:
                lo = resolve_libreoffice_binary()
                if lo:
                    try:
                        logger.warning(
                            "WeasyPrint indisponível (%s); tentando LibreOffice em %s.",
                            exc,
                            lo,
                        )
                        return self._pdf_via_libreoffice(
                            tipo,
                            payload,
                            libreoffice_binary=lo,
                            docxtpl_context=docxtpl_context,
                        )
                    except Exception as lo_exc:
                        logger.warning("LibreOffice falhou: %s", lo_exc, exc_info=True)
                        if simple_ok:
                            logger.warning("Emitindo PDF simplificado (fallback de desenvolvimento).")
                            return render_simple_pdf_bytes(tipo=tipo, payload=payload)
                        raise RuntimeError(
                            "WeasyPrint e LibreOffice falharam. Verifique a instalação do LibreOffice "
                            "ou defina DOCUMENTOS_SIMPLE_PDF_FALLBACK=true para PDF texto simples em dev."
                        ) from lo_exc
                if simple_ok:
                    logger.warning(
                        "WeasyPrint indisponível (%s); LibreOffice não encontrado; PDF simplificado.",
                        exc,
                    )
                    return render_simple_pdf_bytes(tipo=tipo, payload=payload)
                raise RuntimeError(
                    "WeasyPrint não carregou as bibliotecas GTK/Pango/Cairo e o LibreOffice "
                    "não foi encontrado. Opções: instalar o GTK3 runtime para Windows "
                    "(projeto GTK-for-Windows-Runtime-Environment-Installer no GitHub), "
                    "ou instalar o LibreOffice (o app tenta detectar soffice.exe automaticamente), "
                    "ou no .env: DOCUMENTOS_DEFAULT_PDF_ENGINE=libreoffice e "
                    "DOCUMENTOS_LIBREOFFICE_BINARY apontando para soffice.exe, "
                    "ou em desenvolvimento Windows use DOCUMENTOS_SIMPLE_PDF_FALLBACK=true "
                    "(habilitado por padrão em config.settings.dev)."
                ) from exc
        raise DocumentValidationError(f"Motor PDF desconhecido: {engine}")

    def _pdf_via_libreoffice(
        self,
        tipo: DocumentoTipo,
        payload: Mapping[str, object],
        *,
        libreoffice_binary: str | None = None,
        docxtpl_context: Mapping[str, object] | None = None,
    ) -> bytes:
        docx_def = self._templates.get(tipo, DocumentoFormato.DOCX)
        docx_ctx = docxtpl_context if docxtpl_context is not None else payload
        docx_bytes = self._render_docx(docx_def, docx_ctx)
        binary = (libreoffice_binary or "").strip() or resolve_libreoffice_binary()
        if not binary:
            raise DocumentValidationError(
                "Motor PDF = libreoffice, mas nenhum executável foi encontrado. "
                "Defina DOCUMENTOS_LIBREOFFICE_BINARY no .env ou instale o LibreOffice.",
            )
        return convert_docx_to_pdf_libreoffice(docx_bytes=docx_bytes, libreoffice_binary=binary)


def build_default_facade() -> DocumentoFacade:
    return DocumentoFacade()
