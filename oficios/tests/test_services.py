from django.test import TestCase

from cadastros.models import Cargo
from cadastros.models import Servidor
from cadastros.models import Unidade
from cadastros.models import Viatura
from oficios.forms import OficioForm
from oficios.models import Oficio
from oficios.services import atualizar_oficio
from oficios.services import build_oficio_document_payload
from oficios.services import criar_oficio


class OficioServicesTests(TestCase):
    def setUp(self):
        self.cargo = Cargo.objects.create(nome="Analista")
        self.unidade = Unidade.objects.create(nome="DPC", sigla="DPC")
        self.servidor = Servidor.objects.create(nome="Servidor Um", cargo=self.cargo, cpf="12345678901")
        self.viatura = Viatura.objects.create(placa="ABC1234", modelo="Viatura 1")

    def test_criar_oficio_persiste(self):
        form = OficioForm(
            data={
                "numero": "1",
                "ano": "2026",
                "data_criacao": "2026-05-08",
                "protocolo": "abc 123",
                "assunto": "Teste",
                "motivo": "Motivo",
                "status": Oficio.STATUS_RASCUNHO,
                "solicitante": str(self.unidade.pk),
                "servidores": [str(self.servidor.pk)],
                "viatura": str(self.viatura.pk),
                "motorista": str(self.servidor.pk),
                "custeio": Oficio.CUSTEIO_UNIDADE_DPC,
                "custeio_observacao": "",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        oficio = criar_oficio(form)
        self.assertIsNotNone(oficio.pk)
        self.assertEqual(oficio.protocolo, "ABC 123")

    def test_atualizar_oficio_altera(self):
        oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            assunto="Assunto antigo",
            status=Oficio.STATUS_RASCUNHO,
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
        )
        form = OficioForm(
            data={
                "numero": "1",
                "ano": "2026",
                "data_criacao": "2026-05-08",
                "protocolo": "protocolo x",
                "assunto": "Assunto novo",
                "motivo": "Motivo novo",
                "status": Oficio.STATUS_FINALIZADO,
                "solicitante": "",
                "servidores": [],
                "viatura": "",
                "motorista": "",
                "custeio": Oficio.CUSTEIO_ONUS_LIMITADO,
                "custeio_observacao": "",
            },
            instance=oficio,
        )
        self.assertTrue(form.is_valid(), form.errors)
        atualizado = atualizar_oficio(oficio, form)
        self.assertEqual(atualizado.assunto, "Assunto novo")
        self.assertEqual(atualizado.status, Oficio.STATUS_FINALIZADO)

    def test_build_oficio_document_payload_retorna_chaves_esperadas(self):
        oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            protocolo="PROTO 1",
            assunto="Assunto",
            motivo="Motivo",
            status=Oficio.STATUS_RASCUNHO,
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
            viatura=self.viatura,
            motorista=self.servidor,
        )
        oficio.servidores.add(self.servidor)
        payload = build_oficio_document_payload(oficio)
        expected_keys = {
            "numero",
            "ano",
            "numero_formatado",
            "protocolo",
            "assunto",
            "motivo",
            "data_criacao",
            "status",
            "roteiro",
            "servidores",
            "viatura",
            "motorista",
            "custeio",
        }
        self.assertEqual(set(payload.keys()), expected_keys)
