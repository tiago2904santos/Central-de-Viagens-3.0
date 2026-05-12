from __future__ import annotations

import hashlib

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import Client
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from cadastros.models import Servidor
from documentos.models import DocumentoArtefato


def _pdf():
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<<>>>>endobj\n"
        b"4 0 obj<</Length 21>>stream\nBT /F1 12 Tf ET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000214 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\n"
        b"startxref\n310\n"
        b"%%EOF\n"
    )


@override_settings(DOCUMENTOS_PERSIST_ARTEFATOS=True)
class AssinarArtefatoViewTests(TestCase):
    def setUp(self):
        raw = _pdf()
        digest = hashlib.sha256(raw).hexdigest()
        self.servidor = Servidor.objects.create(nome="Servidor Teste")
        self.art = DocumentoArtefato.objects.create(
            tipo="t",
            formato="pdf",
            servidor=self.servidor,
            hash_sha256=digest,
            arquivo=ContentFile(raw, name="a.pdf"),
        )
        self.user = get_user_model().objects.create_user(username="sig_v", password="p" * 12)

    def test_get_exige_login(self):
        c = Client()
        url = reverse("assinaturas:assinatura-assinar-artefato", kwargs={"artefato_id": self.art.pk})
        r = c.get(url)
        self.assertEqual(r.status_code, 302)

    def test_get_autenticado_200(self):
        c = Client()
        c.force_login(self.user)
        url = reverse("assinaturas:assinatura-assinar-artefato", kwargs={"artefato_id": self.art.pk})
        r = c.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "sig-x")

    def test_post_redireciona_verificacao(self):
        c = Client()
        c.force_login(self.user)
        url = reverse("assinaturas:assinatura-assinar-artefato", kwargs={"artefato_id": self.art.pk})
        r = c.post(
            url,
            {
                "sig_x": "0.37",
                "sig_y": "0.8",
                "sig_w": "0.269",
                "sig_h": "0.067",
                "sig_page": "-1",
                "nome_assinante": "Nome POST",
                "cpf_assinante": "12345678901",
                "email_assinante": "x@y.z",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn("/assinaturas/verificar/", r.headers.get("Location", ""))
