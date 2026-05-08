from django.test import SimpleTestCase

from documentos.services.exceptions import DocumentRendererUnavailable
from documentos.services.renderers import DocumentRenderRequest
from documentos.services.renderers import DocxRenderer
from documentos.services.renderers import render_document
from documentos.services.types import DocumentoFormato
from documentos.services.types import DocumentoTipo


class RenderersTests(SimpleTestCase):
    def test_render_document_raises_when_renderer_unavailable(self):
        request = DocumentRenderRequest(
            tipo=DocumentoTipo.OFICIO,
            formato=DocumentoFormato.DOCX,
            payload={"numero": "10"},
            template_content="Ofício {{numero}}",
        )
        with self.assertRaises(DocumentRendererUnavailable):
            render_document(request)

    def test_render_document_returns_content_when_renderer_supports_format(self):
        request = DocumentRenderRequest(
            tipo=DocumentoTipo.OFICIO,
            formato=DocumentoFormato.DOCX,
            payload={"numero": "10"},
        )
        result, filename = render_document(
            request,
            renderer=DocxRenderer(adapter=lambda req: f"Ofício {req.payload['numero']}".encode("utf-8")),
            template_content="Ofício {{numero}}",
            reference="A-1",
        )
        self.assertEqual(result.content, "Ofício 10".encode("utf-8"))
        self.assertIn("oficio_a-1_", filename)
