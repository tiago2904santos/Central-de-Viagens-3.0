import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from django.test import override_settings
from django.urls import NoReverseMatch
from django.urls import reverse

from cadastros.models import Cidade
from cadastros.models import Estado
from cadastros.selectors import get_estado_by_sigla
from cadastros.selectors import get_municipio_by_id
from cadastros.selectors import listar_capitais
from cadastros.selectors import listar_municipios
from cadastros.services_importacao import importar_base_geografica
from cadastros.services_importacao import importar_estados_csv
from core.navigation import build_navigation


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class BaseGeograficaInternaTests(TestCase):
    def _write_csv(self, content: str) -> Path:
        t = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".csv",
            encoding="utf-8-sig",
            newline="",
        )
        try:
            t.write(content)
        finally:
            t.close()
        return Path(t.name)

    def test_estado_importado_com_nome_sigla_codigo(self):
        p = self._write_csv("COD,NOME,SIGLA\n41,Paraná,PR\n")
        r = importar_estados_csv(p, dry_run=False)
        p.unlink(missing_ok=True)
        e = Estado.objects.get(sigla="PR")
        self.assertEqual(e.nome, "PARANÁ")
        self.assertEqual(e.codigo_ibge, 41)
        self.assertGreaterEqual(r.criados, 1)

    def test_municipio_importado_ibge_coords_estado(self):
        e = self._write_csv("COD,NOME,SIGLA\n41,PARANÁ,PR\n")
        m = self._write_csv(
            "id_municipio;uf;municipio;longitude;latitude\n"
            "4113700;PR;Londrina;-51.1628;-23.3045\n",
        )
        importar_base_geografica(e, municipios_code_path=m, dry_run=False)
        e.unlink(missing_ok=True)
        m.unlink(missing_ok=True)
        c = Cidade.objects.get(codigo_ibge=4113700)
        self.assertEqual(c.nome, "LONDRINA")
        self.assertEqual(c.estado.sigla, "PR")
        self.assertIsNotNone(c.latitude)
        self.assertIsNotNone(c.longitude)

    def test_capital_marcada_e_curitiba_londrina(self):
        e = self._write_csv("COD,NOME,SIGLA\n41,PARANÁ,PR\n")
        m = self._write_csv(
            "id_municipio;uf;municipio;longitude;latitude\n"
            "4106902;PR;Curitiba;-49.27;-25.42\n"
            "4113700;PR;Londrina;-51.16;-23.30\n",
        )
        importar_base_geografica(e, municipios_code_path=m, dry_run=False)
        e.unlink(missing_ok=True)
        m.unlink(missing_ok=True)
        self.assertTrue(
            Cidade.objects.get(nome="CURITIBA", estado__sigla="PR").capital,
        )
        self.assertFalse(
            Cidade.objects.get(nome="LONDRINA", estado__sigla="PR").capital,
        )

    def test_nao_duplica_estados(self):
        p = self._write_csv(
            "COD,NOME,SIGLA\n"
            "41,Paraná,PR\n"
            "41,PARANÁ,PR\n",
        )
        importar_estados_csv(p, dry_run=False)
        p.unlink(missing_ok=True)
        self.assertEqual(Estado.objects.filter(sigla="PR").count(), 1)

    def test_nao_duplica_municipios_mesmo_ibge(self):
        est = self._write_csv("COD,NOME,SIGLA\n41,PARANÁ,PR\n")
        mun = self._write_csv(
            "id_municipio;uf;municipio\n4113700;PR;Londrina\n4113700;PR;Londrina\n",
        )
        importar_base_geografica(est, municipios_code_path=mun, dry_run=False)
        est.unlink(missing_ok=True)
        mun.unlink(missing_ok=True)
        self.assertEqual(Cidade.objects.filter(codigo_ibge=4113700).count(), 1)

    def test_dry_run_nao_persiste_via_servico(self):
        est = self._write_csv("COD,NOME,SIGLA\n41,PARANÁ,PR\n")
        mun = self._write_csv("id_municipio;uf;municipio\n4106902;PR;Curitiba\n")
        n_e, n_c = Estado.objects.count(), Cidade.objects.count()
        importar_base_geografica(est, municipios_code_path=mun, dry_run=True)
        est.unlink(missing_ok=True)
        mun.unlink(missing_ok=True)
        self.assertEqual(Estado.objects.count(), n_e)
        self.assertEqual(Cidade.objects.count(), n_c)

    def test_comando_importar_base_geografica_dry_run_stdout(self):
        est = self._write_csv("COD,NOME,SIGLA\n41,PARANÁ,PR\n")
        mun = self._write_csv("id_municipio;uf;municipio\n4106902;PR;Curitiba\n")
        buf = StringIO()
        call_command(
            "importar_base_geografica",
            "--estados",
            str(est),
            "--municipios-code",
            str(mun),
            "--dry-run",
            stdout=buf,
        )
        est.unlink(missing_ok=True)
        mun.unlink(missing_ok=True)
        self.assertIn("Criados", buf.getvalue())

    def test_selectors_capitais_e_sigla(self):
        e_pr = Estado.objects.create(nome="PARANÁ", sigla="PR", codigo_ibge=41)
        Cidade.objects.create(
            nome="CURITIBA",
            estado=e_pr,
            codigo_ibge=4106902,
            capital=True,
        )
        Cidade.objects.create(
            nome="LONDRINA",
            estado=e_pr,
            codigo_ibge=4113700,
            capital=False,
        )
        caps = list(listar_capitais())
        self.assertEqual(len(caps), 1)
        self.assertEqual(caps[0].nome, "CURITIBA")
        st = get_estado_by_sigla("pr")
        self.assertEqual(st.pk, e_pr.pk)
        cid = get_municipio_by_id(caps[0].pk)
        self.assertTrue(cid.capital)
        muns = listar_municipios(uf="PR", capital=True)
        self.assertEqual(muns.count(), 1)

    def test_rotas_publicas_estados_cidades_nao_existem(self):
        for name in (
            "cadastros:estados_index",
            "cadastros:estado_create",
            "cadastros:cidades_index",
            "cadastros:cidades_export_csv",
        ):
            with self.subTest(name=name):
                with self.assertRaises(NoReverseMatch):
                    reverse(name)

    def test_hub_cadastros_sem_estados_cidades(self):
        response = self.client.get(reverse("cadastros:index"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn("estados/", html)
        self.assertNotIn("cidades/", html)

    def test_menu_lateral_sem_estados_cidades(self):
        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.get("/cadastros/")
        request.resolver_match = None
        nav = build_navigation(request)
        cad = next(x for x in nav if x.get("id") == "cadastros")
        labels = [c["label"] for c in cad.get("children", [])]
        self.assertNotIn("Estados", labels)
        self.assertNotIn("Cidades", labels)
