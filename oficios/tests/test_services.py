from django.test import TestCase
from django.utils import timezone

from cadastros.models import Cargo
from cadastros.models import Servidor
from cadastros.models import Viatura
from oficios.forms import OficioDadosViajantesForm
from oficios.models import ModeloMotivoOficio
from oficios.models import Oficio
from oficios.services import atualizar_oficio_dados_viajantes
from oficios.services import avaliar_oficio_dados_viajantes
from oficios.services import build_oficio_document_payload
from oficios.services import criar_oficio_dados_viajantes
from oficios.services import get_next_available_numero_oficio


class OficioServicesTests(TestCase):
    def setUp(self):
        self.cargo = Cargo.objects.create(nome="Analista")
        self.servidor = Servidor.objects.create(nome="Servidor Um", cargo=self.cargo, cpf="12345678901")
        self.viatura = Viatura.objects.create(placa="ABC1234", modelo="Viatura 1")
        self.modelo = ModeloMotivoOficio.objects.create(nome="PADRAO SERVICO", texto="Texto padrão")

    def test_criar_oficio_dados_viajantes_salva_m2m_e_status(self):
        form = OficioDadosViajantesForm(
            data={
                "protocolo": "12.345.678-9",
                "modelo_motivo": str(self.modelo.pk),
                "motivo": "Motivo",
                "servidores": [str(self.servidor.pk)],
                "custeio": Oficio.CUSTEIO_UNIDADE_DPC,
                "custeio_observacao": "",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        oficio = criar_oficio_dados_viajantes(form, action="save_draft")
        self.assertEqual(oficio.protocolo, "123456789")
        self.assertEqual(oficio.numero, 1)
        self.assertEqual(oficio.ano, timezone.localdate().year)
        self.assertEqual(oficio.status, Oficio.STATUS_RASCUNHO)
        self.assertEqual(list(oficio.servidores.all()), [self.servidor])

    def test_get_next_available_numero_reaproveita_menor_lacuna(self):
        ano = timezone.localdate().year
        primeiro = Oficio.objects.create(numero=1, ano=ano, custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        Oficio.objects.create(numero=2, ano=ano, custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        primeiro.delete()
        self.assertEqual(get_next_available_numero_oficio(ano), 1)

    def test_atualizar_oficio_dados_viajantes_preserva_transporte_data_e_numero(self):
        oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            status=Oficio.STATUS_RASCUNHO,
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
            viatura=self.viatura,
            motorista=self.servidor,
        )
        data_original = oficio.data_criacao
        oficio.servidores.add(self.servidor)
        form = OficioDadosViajantesForm(
            data={
                "protocolo": "12.345.678-4",
                "motivo": "Motivo novo",
                "servidores": [str(self.servidor.pk)],
                "custeio": Oficio.CUSTEIO_ONUS_LIMITADO,
                "custeio_observacao": "",
            },
            instance=oficio,
        )
        self.assertTrue(form.is_valid(), form.errors)
        atualizado = atualizar_oficio_dados_viajantes(oficio, form, action="save_continue")
        atualizado.refresh_from_db()
        self.assertEqual(atualizado.numero, 1)
        self.assertEqual(atualizado.ano, 2026)
        self.assertEqual(atualizado.data_criacao, data_original)
        self.assertEqual(atualizado.viatura, self.viatura)
        self.assertEqual(atualizado.motorista, self.servidor)
        self.assertEqual(list(atualizado.servidores.all()), [self.servidor])
        self.assertEqual(atualizado.status, Oficio.STATUS_GERADO)

    def test_avaliar_oficio_dados_viajantes_incomplete_e_complete(self):
        incompleto = Oficio.objects.create(custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        avaliacao_incompleta = avaliar_oficio_dados_viajantes(incompleto)
        self.assertEqual(avaliacao_incompleta["status"], "incomplete")
        self.assertIn("Informe o motivo.", avaliacao_incompleta["pendencias"])
        self.assertIn("Selecione ao menos um viajante.", avaliacao_incompleta["pendencias"])

        completo = Oficio.objects.create(motivo="Motivo", custeio=Oficio.CUSTEIO_UNIDADE_DPC)
        completo.servidores.add(self.servidor)
        avaliacao_completa = avaliar_oficio_dados_viajantes(completo)
        self.assertEqual(avaliacao_completa["status"], "complete")
        self.assertEqual(avaliacao_completa["pendencias"], [])

    def test_build_oficio_document_payload_formata_protocolo(self):
        oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            protocolo="123456789",
            motivo="Motivo",
            status=Oficio.STATUS_RASCUNHO,
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
        )
        payload = build_oficio_document_payload(oficio)
        self.assertEqual(payload["protocolo"], "12.345.678-9")
