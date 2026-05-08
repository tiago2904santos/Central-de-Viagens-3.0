from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cadastros.models import Cargo
from cadastros.models import Servidor
from cadastros.models import Unidade
from oficios.models import Oficio


class OficioViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester_oficios",
            password="123456",
        )
        self.client.force_login(self.user)
        self.cargo = Cargo.objects.create(nome="Analista Teste")
        self.unidade = Unidade.objects.create(nome="Unidade Teste", sigla="UT")
        self.servidor = Servidor.objects.create(nome="Servidor Teste", cargo=self.cargo, cpf="12345678901")

    def test_get_index_retorna_200(self):
        response = self.client.get(reverse("oficios:index"))
        self.assertEqual(response.status_code, 200)

    def test_get_novo_retorna_200(self):
        response = self.client.get(reverse("oficios:novo"))
        self.assertEqual(response.status_code, 200)

    def test_post_novo_valido_cria_oficio_e_redireciona(self):
        response = self.client.post(
            reverse("oficios:novo"),
            data={
                "numero": "1",
                "ano": "2026",
                "data_criacao": "2026-05-08",
                "protocolo": "abc 1",
                "assunto": "Assunto",
                "motivo": "Motivo",
                "status": Oficio.STATUS_RASCUNHO,
                "solicitante": str(self.unidade.pk),
                "servidores": [str(self.servidor.pk)],
                "viatura": "",
                "motorista": "",
                "custeio": Oficio.CUSTEIO_UNIDADE_DPC,
                "custeio_observacao": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Oficio.objects.count(), 1)
        oficio = Oficio.objects.order_by("pk").first()
        self.assertEqual(oficio.numero, 1)
        self.assertEqual(oficio.ano, timezone.localdate().year)

    def test_get_detalhe_retorna_200(self):
        oficio = Oficio.objects.create(numero=1, ano=2026, custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        response = self.client.get(reverse("oficios:detalhe", args=[oficio.pk]))
        self.assertEqual(response.status_code, 200)

    def test_get_editar_redireciona_para_dados_viajantes(self):
        oficio = Oficio.objects.create(numero=1, ano=2026, custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        response = self.client.get(reverse("oficios:editar", args=[oficio.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("oficios:dados_viajantes", args=[oficio.pk]))

    def test_post_editar_redireciona_sem_alterar(self):
        oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            assunto="Assunto antigo",
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
        )
        response = self.client.post(
            reverse("oficios:editar", args=[oficio.pk]),
            data={
                "numero": "2",
                "ano": "2026",
                "data_criacao": "2026-05-08",
                "protocolo": "abc 2",
                "assunto": "Assunto novo",
                "motivo": "Motivo novo",
                "status": Oficio.STATUS_FINALIZADO,
                "solicitante": str(self.unidade.pk),
                "servidores": [str(self.servidor.pk)],
                "viatura": "",
                "motorista": "",
                "custeio": Oficio.CUSTEIO_UNIDADE_DPC,
                "custeio_observacao": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("oficios:dados_viajantes", args=[oficio.pk]))
        oficio.refresh_from_db()
        self.assertEqual(oficio.numero, 1)
        self.assertEqual(oficio.assunto, "Assunto antigo")

    def test_post_excluir_remove(self):
        oficio = Oficio.objects.create(numero=1, ano=2026, custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        response = self.client.post(reverse("oficios:excluir", args=[oficio.pk]))
        self.assertEqual(response.status_code, 302)
        detail_response = self.client.get(reverse("oficios:detalhe", args=[oficio.pk]))
        self.assertEqual(detail_response.status_code, 404)
