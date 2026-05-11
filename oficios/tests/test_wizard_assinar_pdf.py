import hashlib
from unittest import mock

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
    def test_assinar_sem_artefato_previo_chama_geracao(self, m_gerar, _m_val):
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
        r = self.client.post(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        m_gerar.assert_called_once()

    @mock.patch("oficios.views.gerar_resposta_documento_oficio", return_value=HttpResponse(b"x", content_type="application/pdf"))
    @mock.patch("oficios.views.validar_oficio_para_documento", return_value=_validacao_limpa())
    def test_verificar_json_sem_pdf_previo_422(self, _m_val, _m_gerar):
        url = reverse("oficios:wizard_verificar_pdf_oficio", args=[self.oficio.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 422)
        self.assertFalse(r.json().get("ok"))
