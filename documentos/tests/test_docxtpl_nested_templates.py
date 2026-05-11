"""Smoke tests dos modelos DOCX com placeholders aninhados (Jinja no docxtpl)."""

from __future__ import annotations

from django.test import SimpleTestCase

from documentos.services.adapters.docxtpl_render import render_docx_bytes
from documentos.services.resources_paths import resolve_resource_docx


class DocxtplNestedTemplatesSmokeTests(SimpleTestCase):
    def test_plano_trabalho_docx_renders(self):
        path = resolve_resource_docx("plano_trabalho.docx")
        self.assertTrue(path.is_file())
        out = render_docx_bytes(
            template_path=path,
            context={"oficio": {"numero_formatado": "99/2026"}},
        )
        self.assertTrue(out.startswith(b"PK"))

    def test_ordem_servico_docx_renders(self):
        path = resolve_resource_docx("ordem_servico.docx")
        self.assertTrue(path.is_file())
        out = render_docx_bytes(
            template_path=path,
            context={"oficio": {"numero_formatado": "1/2026"}},
        )
        self.assertTrue(out.startswith(b"PK"))

    def test_termo_autorizacao_docx_renders(self):
        path = resolve_resource_docx("termo_autorizacao.docx")
        self.assertTrue(path.is_file())
        out = render_docx_bytes(
            template_path=path,
            context={
                "oficio": {"numero_formatado": "10/2026"},
                "termo": {
                    "variante": "semipreenchido",
                    "participante": {"nome": "Servidor Teste", "cpf": "000.000.000-00"},
                },
            },
        )
        self.assertTrue(out.startswith(b"PK"))
