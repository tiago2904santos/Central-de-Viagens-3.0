from django.test import TestCase

from cadastros.models import ConfiguracaoSistema
from oficios.docxtpl_context import build_oficio_docxtpl_context
from oficios.models import Oficio


class BuildOficioCapitalizacaoTests(TestCase):
    def setUp(self):
        ConfiguracaoSistema.get_singleton()

    def test_sem_roteiro_orgao_destino_legivel(self):
        oficio = Oficio.objects.create()
        ctx = build_oficio_docxtpl_context(oficio)
        self.assertEqual(ctx["orgao_destino"], "Gabinete do Delegado Geral Adjunto")
        self.assertIn(" do ", f" {ctx['orgao_destino']} ")

    def test_unidade_cabecalho_legivel(self):
        cfg = ConfiguracaoSistema.get_singleton()
        cfg.unidade = "DELEGACIA REGIONAL DE POLÍCIA DE LONDRINA"
        cfg.save(update_fields=["unidade"])
        oficio = Oficio.objects.create()
        ctx = build_oficio_docxtpl_context(oficio)
        self.assertEqual(ctx["unidade_cabecalho"], ctx["unidade"])
        self.assertIn(" de ", f" {ctx['unidade_cabecalho']} ")
