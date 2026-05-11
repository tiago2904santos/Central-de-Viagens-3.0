import hashlib
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from cadastros.models import Cargo
from cadastros.models import Servidor
from documentos.models import DocumentoArtefato
from oficios.models import Oficio


def _minimal_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _validacao_limpa():
    return {"status": "complete", "pendencias": [], "checks": {}}


@override_settings(DOCUMENTOS_PERSIST_ARTEFATOS=True, SIGNATURE_BACKEND="disabled")
class WizardAssinarPdfOficioTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="wiz_sign_u", password="w" * 12)
        self.client.force_login(self.user)
        self.cargo = Cargo.objects.create(nome="Cargo WizS")
        self.servidor = Servidor.objects.create(nome="Serv WizS", cargo=self.cargo, cpf="99888777666")
        self.oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            protocolo="10.20.30-4",
            motivo="mot",
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
        )
        self.oficio.servidores.add(self.servidor)

    @mock.patch("oficios.views.validar_oficio_para_documento", return_value=_validacao_limpa())
    @mock.patch("oficios.views.gerar_resposta_documento_oficio")
    def test_get_pagina_assinatura_200_sem_attachment(self, m_gerar, _m_val):
        raw = _minimal_pdf_bytes()

        def _gerar(oficio, _fmt):
            digest = hashlib.sha256(raw).hexdigest()
            DocumentoArtefato.objects.create(
                tipo="oficio",
                formato="pdf",
                oficio=oficio,
                hash_sha256=digest,
                arquivo=ContentFile(raw, name="oficio_wiz.pdf"),
            )
            return HttpResponse(raw, content_type="application/pdf")

        m_gerar.side_effect = _gerar

        url = reverse("oficios:wizard_assinar_pdf_oficio", args=[self.oficio.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r["Content-Type"])
        disp = r.get("Content-Disposition") or ""
        self.assertNotIn("attachment", disp.lower())
        self.assertContains(r, "Confirmar assinatura")
        self.assertTemplateUsed(r, "oficios/wizard_assinatura_pdf.html")
        m_gerar.assert_called_once()

    @mock.patch("documentos.services.signing.workflow.assinar_pdf_final")
    @mock.patch("oficios.views.validar_oficio_para_documento", return_value=_validacao_limpa())
    @mock.patch("oficios.views.gerar_resposta_documento_oficio")
    def test_get_nao_chama_assinar_pdf_final(self, m_gerar, _m_val, m_final):
        raw = _minimal_pdf_bytes()

        def _gerar(oficio, _fmt):
            digest = hashlib.sha256(raw).hexdigest()
            DocumentoArtefato.objects.create(
                tipo="oficio",
                formato="pdf",
                oficio=oficio,
                hash_sha256=digest,
                arquivo=ContentFile(raw, name="oficio_wiz.pdf"),
            )
            return HttpResponse(raw, content_type="application/pdf")

        m_gerar.side_effect = _gerar
        url = reverse("oficios:wizard_assinar_pdf_oficio", args=[self.oficio.pk])
        self.client.get(url)
        m_final.assert_not_called()

    @mock.patch("oficios.views.validar_oficio_para_documento", return_value=_validacao_limpa())
    @mock.patch("oficios.views.gerar_resposta_documento_oficio")
    def test_post_assina_e_redireciona_documentos(self, m_gerar, _m_val):
        raw = _minimal_pdf_bytes()

        def _gerar(oficio, _fmt):
            digest = hashlib.sha256(raw).hexdigest()
            DocumentoArtefato.objects.create(
                tipo="oficio",
                formato="pdf",
                oficio=oficio,
                hash_sha256=digest,
                arquivo=ContentFile(raw, name="oficio_wiz.pdf"),
            )
            return HttpResponse(raw, content_type="application/pdf")

        m_gerar.side_effect = _gerar
        url = reverse("oficios:wizard_assinar_pdf_oficio", args=[self.oficio.pk])
        r = self.client.post(url, follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("oficios:wizard_documentos", args=[self.oficio.pk]), r["Location"])
        art = DocumentoArtefato.objects.filter(oficio=self.oficio, formato="pdf").order_by("-criado_em").first()
        self.assertIsNotNone(art)
        self.assertTrue((art.hash_sha256_assinado or "").strip())

    @mock.patch("oficios.views.gerar_resposta_documento_oficio", return_value=HttpResponse(b"x", content_type="application/pdf"))
    @mock.patch("oficios.views.validar_oficio_para_documento", return_value=_validacao_limpa())
    def test_verificar_json_sem_pdf_previo_422(self, _m_val, _m_gerar):
        url = reverse("oficios:wizard_verificar_pdf_oficio", args=[self.oficio.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 422)
        self.assertFalse(r.json().get("ok"))


class WizardDocumentosAssinarPdfLinkTests(TestCase):
    def test_template_assinar_pdf_e_anchor_get(self):
        tpl = Path(settings.BASE_DIR) / "templates" / "oficios" / "wizard_documentos.html"
        s = tpl.read_text(encoding="utf-8")
        idx = s.index("Assinar PDF")
        window = s[max(0, idx - 500) : idx + 20]
        self.assertIn("href=", window)
        self.assertIn("wizard_assinar_pdf_oficio", window)
        self.assertNotIn("formaction", window)
        self.assertNotIn('type="submit"', window)
