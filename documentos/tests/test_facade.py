import hashlib
from unittest import mock

from django.test import SimpleTestCase

from documentos.services.exceptions import DocumentValidationError
from documentos.services.facade import DocumentoFacade
from documentos.services.templates import DocumentTemplateDefinition
from documentos.services.templates import DocumentTemplateRegistry
from documentos.services.types import DocumentoFormato
from documentos.services.types import DocumentoTipo


class FacadeTests(SimpleTestCase):
    def test_gerar_docx_requires_payload_fields(self):
        facade = DocumentoFacade()
        with self.assertRaises(DocumentValidationError):
            facade.gerar(
                tipo=DocumentoTipo.OFICIO,
                formato=DocumentoFormato.DOCX,
                payload={},
            )

    def test_gerar_docx_returns_hash(self):
        registry = DocumentTemplateRegistry()
        registry.register(
            DocumentTemplateDefinition(
                tipo=DocumentoTipo.OFICIO,
                formato=DocumentoFormato.DOCX,
                template_path="oficio.docx",
                required_placeholders=("institucional", "oficio"),
            ),
        )
        facade = DocumentoFacade(template_registry=registry)
        payload = {
            "institucional": {"nome_orgao": "X"},
            "oficio": {"numero_formatado": "1/2026"},
            "justificativa": {"exigida": False, "texto": ""},
        }
        flat = {"oficio": "1/2026", "protocolo": "P"}
        with mock.patch.object(facade, "_render_docx", return_value=b"fake-docx") as m_docx:
            out = facade.gerar(
                tipo=DocumentoTipo.OFICIO,
                formato=DocumentoFormato.DOCX,
                payload=payload,
                reference="ref",
                docxtpl_context=flat,
            )
        m_docx.assert_called_once()
        self.assertEqual(m_docx.call_args[0][1], flat)
        self.assertEqual(out.hash_sha256, hashlib.sha256(b"fake-docx").hexdigest())
        self.assertTrue(out.nome_arquivo.endswith(".docx"))
