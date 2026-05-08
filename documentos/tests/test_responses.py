from datetime import datetime

from django.test import SimpleTestCase

from documentos.services.exceptions import UnsupportedDocumentFormat
from documentos.services.responses import build_download_response
from documentos.services.responses import get_content_type_for_format
from documentos.services.types import DocumentoFormato
from documentos.services.types import DocumentoTipo


class ResponsesTests(SimpleTestCase):
    def test_build_download_response_sets_headers(self):
        response = build_download_response(
            content=b"conteudo",
            tipo=DocumentoTipo.OFICIO,
            formato=DocumentoFormato.DOCX,
            reference="AB-99",
            now=datetime(2026, 5, 8, 10, 40, 0),
        )
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        self.assertIn("oficio_ab-99_20260508-104000.docx", response["Content-Disposition"])

    def test_build_download_response_sets_pdf_content_type(self):
        response = build_download_response(
            content=b"pdf",
            tipo=DocumentoTipo.OFICIO,
            formato=DocumentoFormato.PDF,
            reference="AB-99",
            now=datetime(2026, 5, 8, 10, 40, 0),
        )
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(".pdf", response["Content-Disposition"])

    def test_get_content_type_for_format_raises_when_unsupported(self):
        with self.assertRaises(UnsupportedDocumentFormat):
            get_content_type_for_format("txt")  # type: ignore[arg-type]
