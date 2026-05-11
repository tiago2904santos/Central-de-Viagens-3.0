"""Termo PDF inline por servidor."""

from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cadastros.models import Cargo
from cadastros.models import Servidor
from cadastros.models import Unidade
from oficios.models import Oficio


class TermoServidorPdfInlineTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester_termo_inline", password="123456")
        self.client.force_login(self.user)
        self.cargo = Cargo.objects.create(nome="Cargo T")
        self.unidade = Unidade.objects.create(nome="Unidade T", sigla="UT")
        self.servidor_no = Servidor.objects.create(
            nome="Fora do oficio",
            cargo=self.cargo,
            cpf="11111111111",
            unidade=self.unidade,
        )
        self.servidor_ok = Servidor.objects.create(
            nome="No oficio",
            cargo=self.cargo,
            cpf="22222222222",
            unidade=self.unidade,
        )
        self.oficio = Oficio.objects.create(numero=1, ano=2026, custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        self.oficio.servidores.add(self.servidor_ok)

    @mock.patch("termos.views.validar_oficio_para_documento", return_value={"pendencias": ["x"]})
    def test_redirect_quando_oficio_incompleto(self, _m):
        url = reverse("termos:termo_servidor_pdf_inline", args=[self.oficio.pk, self.servidor_ok.pk])
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 302)

    @mock.patch("termos.views.validar_oficio_para_documento", return_value={"pendencias": []})
    def test_servidor_fora_do_oficio_retorna_404(self, _m_val):
        url = reverse("termos:termo_servidor_pdf_inline", args=[self.oficio.pk, self.servidor_no.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @mock.patch("termos.views.validar_oficio_para_documento", return_value={"pendencias": []})
    @mock.patch("termos.views.gerar_termo_um")
    def test_inline_com_sha256(self, m_gerar, _m_val):
        m_gerar.return_value = SimpleNamespace(
            conteudo=b"%PDF-1.4\n",
            hash_sha256="deadbeef",
            content_type="application/pdf",
            nome_arquivo="t.pdf",
        )
        url = reverse("termos:termo_servidor_pdf_inline", args=[self.oficio.pk, self.servidor_ok.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("inline", response["Content-Disposition"])
        self.assertEqual(response["X-Document-SHA256"], "deadbeef")
        _ = b"".join(response.streaming_content)
