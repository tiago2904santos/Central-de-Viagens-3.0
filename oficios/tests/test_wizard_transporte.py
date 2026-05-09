from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cadastros.models import Cargo
from cadastros.models import Combustivel
from cadastros.models import Servidor
from cadastros.models import Unidade
from cadastros.models import Viatura
from oficios.models import Oficio


class OficioWizardTransporteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester_wizard_transporte",
            password="123456",
        )
        self.client.force_login(self.user)
        self.cargo = Cargo.objects.create(nome="Motorista Cargo")
        self.comb = Combustivel.objects.create(nome="Flex")
        self.servidor = Servidor.objects.create(nome="Motorista Servidor", cargo=self.cargo, cpf="11122233344")
        self.unidade_m = Unidade.objects.create(nome="ASCOM Central", sigla="ASCOM")
        self.motorista_viatura = Servidor.objects.create(
            nome="João da Silva",
            cargo=self.cargo,
            cpf="22233344455",
            unidade=self.unidade_m,
        )
        self.viatura = Viatura.objects.create(
            placa="ABC1234",
            modelo="Renault Duster",
            combustivel=self.comb,
            tipo=Viatura.TIPO_DESCARACTERIZADA,
        )
        self.viatura.motoristas.add(self.motorista_viatura)

    def _oficio_com_etapa1_minima(self):
        url_novo = self.client.get(reverse("oficios:novo")).url
        self.client.post(
            url_novo,
            data={
                "protocolo": "12.345.678-9",
                "motivo": "Motivo transporte",
                "custeio": Oficio.CUSTEIO_UNIDADE_DPC,
                "custeio_observacao": "",
                "servidores": [str(self.servidor.pk)],
                "action": "save_continue",
            },
        )
        return Oficio.objects.get()

    def _payload_transporte(self, **overrides):
        data = {
            "porte_transporte_armas": "sim",
            "motorista_modo": Oficio.MOTORISTA_MODO_SERVIDOR,
            "transporte_placa_manual": "",
            "transporte_modelo_manual": "",
            "transporte_combustivel_manual": "",
            "transporte_tipo_manual": "",
            "motorista": "",
            "motorista_manual_nome": "",
            "motorista_manual_rg": "",
            "motorista_manual_cpf": "",
            "motorista_manual_cargo": "",
            "motorista_manual_unidade": "",
            "motorista_manual_observacao": "",
            "viatura": "",
            "action": "save_draft",
        }
        data.update(overrides)
        return data

    def test_get_transporte_renderiza(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.get(reverse("oficios:transporte", args=[oficio.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "oficios/wizard_transporte.html")
        self.assertContains(response, "Viatura")
        self.assertContains(response, "Motorista")
        self.assertContains(response, "Cadastrar nova viatura")
        self.assertContains(response, reverse("cadastros:viatura_create"))
        self.assertContains(response, "Digite placa, modelo, unidade ou motorista")
        self.assertContains(response, "BUSCAR VIATURA")

    def test_post_save_draft_viatura_cadastrada(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.post(
            reverse("oficios:transporte", args=[oficio.pk]),
            data=self._payload_transporte(
                viatura=str(self.viatura.pk),
                action="save_draft",
            ),
        )
        self.assertEqual(response.status_code, 302)
        oficio.refresh_from_db()
        self.assertEqual(oficio.viatura_id, self.viatura.pk)

    def test_post_save_draft_viatura_manual(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.post(
            reverse("oficios:transporte", args=[oficio.pk]),
            data=self._payload_transporte(
                transporte_placa_manual="XYZ9876",
                transporte_modelo_manual="MODELO LIVRE",
                transporte_combustivel_manual=str(self.comb.pk),
                transporte_tipo_manual=Viatura.TIPO_DESCARACTERIZADA,
                porte_transporte_armas="nao",
                action="save_draft",
            ),
        )
        self.assertEqual(response.status_code, 302)
        oficio.refresh_from_db()
        self.assertIsNone(oficio.viatura_id)
        self.assertEqual(oficio.transporte_placa_manual, "XYZ9876")
        self.assertEqual(oficio.transporte_modelo_manual, "MODELO LIVRE")
        self.assertFalse(oficio.porte_transporte_armas)

    def test_post_motorista_servidor(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.post(
            reverse("oficios:transporte", args=[oficio.pk]),
            data=self._payload_transporte(
                motorista=str(self.servidor.pk),
                motorista_modo=Oficio.MOTORISTA_MODO_SERVIDOR,
                action="save_draft",
            ),
        )
        self.assertEqual(response.status_code, 302)
        oficio.refresh_from_db()
        self.assertEqual(oficio.motorista_id, self.servidor.pk)

    def test_post_motorista_manual(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.post(
            reverse("oficios:transporte", args=[oficio.pk]),
            data=self._payload_transporte(
                motorista_modo=Oficio.MOTORISTA_MODO_MANUAL,
                motorista_manual_nome="Externo Silva",
                motorista_manual_rg="MG1234567",
                action="save_draft",
            ),
        )
        self.assertEqual(response.status_code, 302)
        oficio.refresh_from_db()
        self.assertIsNone(oficio.motorista_id)
        self.assertEqual(oficio.motorista_manual_nome, "EXTERNO SILVA")

    def test_save_continue_redireciona_roteiro(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.post(
            reverse("oficios:transporte", args=[oficio.pk]),
            data=self._payload_transporte(action="save_continue"),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("oficios:wizard_roteiro", args=[oficio.pk]))

    def test_api_viatura_legacy_apenas_placa(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.get(
            reverse("oficios:api_viatura_por_placa", args=[oficio.pk]),
            data={"placa": "ABC-1234"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["found"])
        self.assertEqual(payload["id"], self.viatura.pk)

    def test_api_busca_q_retorna_por_placa(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.get(
            reverse("oficios:api_viatura_por_placa", args=[oficio.pk]),
            data={"q": "ABC1"},
        )
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.json()["results"]]
        self.assertIn(self.viatura.pk, ids)

    def test_api_busca_q_retorna_por_modelo(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.get(
            reverse("oficios:api_viatura_por_placa", args=[oficio.pk]),
            data={"q": "Duster"},
        )
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.json()["results"]]
        self.assertIn(self.viatura.pk, ids)

    def test_api_busca_q_retorna_por_unidade(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.get(
            reverse("oficios:api_viatura_por_placa", args=[oficio.pk]),
            data={"q": "ASCOM"},
        )
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.json()["results"]]
        self.assertIn(self.viatura.pk, ids)

    def test_api_busca_q_retorna_por_motorista(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.get(
            reverse("oficios:api_viatura_por_placa", args=[oficio.pk]),
            data={"q": "Silva"},
        )
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.json()["results"]]
        self.assertIn(self.viatura.pk, ids)

    def test_api_busca_q_curto_retorna_vazio(self):
        oficio = self._oficio_com_etapa1_minima()
        response = self.client.get(
            reverse("oficios:api_viatura_por_placa", args=[oficio.pk]),
            data={"q": "A"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_post_transporte_nao_apaga_dados_viajantes(self):
        oficio = self._oficio_com_etapa1_minima()
        self.assertEqual(oficio.motivo, "Motivo transporte")
        self.client.post(
            reverse("oficios:transporte", args=[oficio.pk]),
            data=self._payload_transporte(motorista=str(self.servidor.pk)),
        )
        oficio.refresh_from_db()
        self.assertEqual(oficio.motivo, "Motivo transporte")
