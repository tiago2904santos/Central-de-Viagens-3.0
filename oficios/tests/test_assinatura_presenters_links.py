from __future__ import annotations

import hashlib

from django.core.files.base import ContentFile
from django.test import TestCase

from assinaturas.presenters import assinatura_urls_artefato
from cadastros.models import Servidor
from documentos.models import DocumentoArtefato


def _pdf():
    return b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


class AssinaturaPresentersLinksTests(TestCase):
    def test_urls_reversiveis_sem_assinatura(self):
        raw = _pdf()
        d = hashlib.sha256(raw).hexdigest()
        srv = Servidor.objects.create(nome="S")
        art = DocumentoArtefato.objects.create(
            tipo="t",
            formato="pdf",
            servidor=srv,
            hash_sha256=d,
            arquivo=ContentFile(raw, name="p.pdf"),
        )
        u = assinatura_urls_artefato(art)
        self.assertIn("/assinaturas/artefatos/", u["assinar"])
        self.assertIn("/pdf-original/", u["pdf_original"])
