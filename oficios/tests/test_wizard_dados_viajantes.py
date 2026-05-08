from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cadastros.models import Cargo
from cadastros.models import Servidor
from cadastros.models import Unidade
from cadastros.models import Viatura
from oficios.models import Oficio


class OficioWizardDadosViajantesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester_wizard_dados",
            password="123456",
        )
        self.client.force_login(self.user)
        self.cargo = Cargo.objects.create(nome="Analista Wizard")
        self.unidade = Unidade.objects.create(nome="Unidade Wizard", sigla="UW")
        self.servidor = Servidor.objects.create(nome="Servidor Wizard", cargo=self.cargo, cpf="12345678901")
        self.outro_servidor = Servidor.objects.create(
            nome="Outro Servidor Wizard",
            cargo=self.cargo,
            cpf="98765432100",
        )
        self.viatura = Viatura.objects.create(placa="ABC1234", modelo="Viatura Wizard")

    def _payload(self, **overrides):
        data = {
            "data_criacao": "2026-05-08",
            "protocolo": "proto 7",
            "status": Oficio.STATUS_RASCUNHO,
            "assunto": "Assunto inicial",
            "motivo": "Motivo inicial",
            "roteiro": "",
            "solicitante": str(self.unidade.pk),
            "custeio": Oficio.CUSTEIO_UNIDADE_DPC,
            "custeio_observacao": "",
            "servidores": [str(self.servidor.pk)],
            "action": "save_draft",
        }
        data.update(overrides)
        return data

    def test_get_novo_renderiza_wizard(self):
        response = self.client.get(reverse("oficios:novo"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "oficios/wizard_dados_viajantes.html")
        self.assertContains(response, "Cadastro de ofício")
        self.assertContains(response, "Dados e viajantes")
        self.assertContains(response, "Transporte")
        self.assertContains(response, "Roteiro e diárias")
        self.assertContains(response, "Resumo do ofício")
        self.assertContains(response, "Documentos")
        self.assertContains(response, "N° do Ofício")
        self.assertContains(response, "Gerado automaticamente ao salvar")
        self.assertNotContains(response, 'href="#"')
        self.assertNotContains(response, "oficio-wizard__aside")

    def test_post_novo_save_draft_cria_e_redireciona_para_etapa(self):
        response = self.client.post(reverse("oficios:novo"), data=self._payload(action="save_draft"))

        self.assertEqual(response.status_code, 302)
        oficio = Oficio.objects.get()
        self.assertEqual(response.url, reverse("oficios:dados_viajantes", args=[oficio.pk]))
        self.assertEqual(oficio.numero, 1)
        self.assertEqual(oficio.ano, timezone.localdate().year)
        self.assertEqual(oficio.numero_formatado, f"01/{timezone.localdate().year}")
        self.assertEqual(oficio.protocolo, "PROTO 7")
        self.assertEqual(oficio.assunto, "Assunto inicial")
        self.assertEqual(oficio.motivo, "Motivo inicial")
        self.assertEqual(oficio.solicitante, self.unidade)
        self.assertEqual(list(oficio.servidores.all()), [self.servidor])

    def test_post_novo_save_continue_cria_e_redireciona_para_detalhe(self):
        response = self.client.post(reverse("oficios:novo"), data=self._payload(action="save_continue"))

        self.assertEqual(response.status_code, 302)
        oficio = Oficio.objects.get()
        self.assertEqual(response.url, reverse("oficios:detalhe", args=[oficio.pk]))

    def test_get_dados_viajantes_renderiza_oficio_existente(self):
        oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            assunto="Assunto existente",
            motivo="Motivo existente",
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
        )
        oficio.servidores.add(self.servidor)

        response = self.client.get(reverse("oficios:dados_viajantes", args=[oficio.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "oficios/wizard_dados_viajantes.html")
        self.assertContains(response, "Assunto existente")
        self.assertContains(response, "oficio-stepper")
        self.assertContains(response, "01/2026")

    def test_post_dados_viajantes_atualiza_sem_apagar_transporte(self):
        oficio = Oficio.objects.create(
            numero=1,
            ano=2026,
            assunto="Antigo",
            motivo="Antigo",
            custeio=Oficio.CUSTEIO_UNIDADE_DPC,
            viatura=self.viatura,
            motorista=self.servidor,
        )
        oficio.servidores.add(self.servidor)

        response = self.client.post(
            reverse("oficios:dados_viajantes", args=[oficio.pk]),
            data=self._payload(
                numero="8",
                assunto="Assunto atualizado",
                motivo="Motivo atualizado",
                servidores=[str(self.outro_servidor.pk)],
                action="save_draft",
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("oficios:dados_viajantes", args=[oficio.pk]))
        oficio.refresh_from_db()
        self.assertEqual(oficio.numero, 1)
        self.assertEqual(oficio.ano, 2026)
        self.assertEqual(oficio.assunto, "Assunto atualizado")
        self.assertEqual(oficio.motivo, "Motivo atualizado")
        self.assertEqual(list(oficio.servidores.all()), [self.outro_servidor])
        self.assertEqual(oficio.viatura, self.viatura)
        self.assertEqual(oficio.motorista, self.servidor)

    def test_get_editar_redireciona_para_dados_viajantes(self):
        oficio = Oficio.objects.create(numero=1, ano=2026, custeio=Oficio.CUSTEIO_UNIDADE_DPC)

        response = self.client.get(reverse("oficios:editar", args=[oficio.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("oficios:dados_viajantes", args=[oficio.pk]))

    def test_numero_automatico_reaproveita_numero_excluido(self):
        ano = timezone.localdate().year
        self.client.post(reverse("oficios:novo"), data=self._payload(action="save_draft"))
        self.client.post(reverse("oficios:novo"), data=self._payload(protocolo="proto 8", action="save_draft"))
        primeiro = Oficio.objects.get(numero=1, ano=ano)
        primeiro.delete()

        self.client.post(reverse("oficios:novo"), data=self._payload(protocolo="proto 9", action="save_draft"))

        self.assertTrue(Oficio.objects.filter(numero=1, ano=ano, protocolo="PROTO 9").exists())

    def test_completude_e_pendencias_aparecem_no_fluxo(self):
        oficio = Oficio.objects.create(custeio=Oficio.CUSTEIO_UNIDADE_DPC)

        response = self.client.get(reverse("oficios:dados_viajantes", args=[oficio.pk]))

        self.assertContains(response, "Incompleta")
        self.assertContains(response, "Informe o assunto.")
        self.assertContains(response, "Informe o motivo.")
        self.assertContains(response, "Selecione ao menos um viajante.")

        oficio.assunto = "Assunto"
        oficio.motivo = "Motivo"
        oficio.save()
        oficio.servidores.add(self.servidor)
        response = self.client.get(reverse("oficios:dados_viajantes", args=[oficio.pk]))

        self.assertContains(response, "Concluída")
        self.assertNotContains(response, "Pendências para concluir esta etapa")

    def test_index_renderiza_card_com_numero_do_oficio(self):
        ano = timezone.localdate().year
        Oficio.objects.create(numero=1, ano=ano, assunto="Assunto card", custeio=Oficio.CUSTEIO_UNIDADE_DPC)

        response = self.client.get(reverse("oficios:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "N° do Ofício")
        self.assertContains(response, f"01/{ano}")
        self.assertContains(response, "Assunto card")

    def test_templates_do_wizard_nao_usam_href_falso_css_ou_script_inline(self):
        template_paths = [
            Path("templates/oficios/wizard_base.html"),
            Path("templates/oficios/wizard_dados_viajantes.html"),
            Path("templates/oficios/partials/wizard_stepper.html"),
            Path("templates/oficios/partials/wizard_actions.html"),
        ]
        for template_path in template_paths:
            content = template_path.read_text(encoding="utf-8")
            self.assertNotIn('href="#"', content)
            self.assertNotIn('style="', content)
            self.assertNotIn("<script", content)
