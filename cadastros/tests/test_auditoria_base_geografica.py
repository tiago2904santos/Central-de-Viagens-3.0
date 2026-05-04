import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from cadastros.geografia import dedupe_capitais_por_uf
from cadastros.geografia import eh_capital
from cadastros.models import Cidade
from cadastros.models import Estado
from cadastros.services_importacao import importar_cidades_csv
from cadastros.services_importacao import importar_estados_csv


class GeografiaEhCapitalTests(TestCase):
    def test_curitiba_eh_capital(self):
        self.assertTrue(eh_capital("CURITIBA", "PR"))
        self.assertTrue(eh_capital("  curitiba  ", "pr"))

    def test_londrina_nao_eh_capital(self):
        self.assertFalse(eh_capital("LONDRINA", "PR"))

    def test_espacos_e_caixa(self):
        self.assertTrue(eh_capital("  SÃO PAULO ", "sp"))


class ImportadorCapitaisTests(TestCase):
    def setUp(self):
        self._estados = Path(
            tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix=".csv",
                encoding="utf-8-sig",
                newline="",
            ).name,
        )
        self._estados.write_text("COD,NOME,SIGLA\n41,PARANÁ,PR\n", encoding="utf-8-sig")
        importar_estados_csv(self._estados, dry_run=False)

    def tearDown(self):
        self._estados.unlink(missing_ok=True)

    def test_uma_capital_por_uf_quando_existe_no_csv(self):
        m = Path(
            tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix=".csv",
                encoding="utf-8-sig",
                newline="",
            ).name,
        )
        m.write_text(
            "id_municipio;uf;municipio;longitude;latitude\n"
            "1;PR;Curitiba;-49.0;-25.0\n"
            "2;PR;Londrina;-51.0;-23.0\n",
            encoding="utf-8-sig",
        )
        r = importar_cidades_csv(m, dry_run=False, fonte_municipio_code=True)
        m.unlink(missing_ok=True)
        self.assertTrue(r.capitais_marcadas >= 1)
        self.assertEqual(Cidade.objects.filter(estado__sigla="PR", capital=True).count(), 1)

    def test_corrige_capital_indevido(self):
        est = Estado.objects.get(sigla="PR")
        Cidade.objects.create(nome="LONDRINA", estado=est, capital=True, codigo_ibge=999)
        m = Path(
            tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix=".csv",
                encoding="utf-8-sig",
                newline="",
            ).name,
        )
        m.write_text(
            "id_municipio;uf;municipio\n999;PR;Londrina\n",
            encoding="utf-8-sig",
        )
        r = importar_cidades_csv(m, dry_run=False, fonte_municipio_code=True)
        m.unlink(missing_ok=True)
        lon = Cidade.objects.get(codigo_ibge=999)
        self.assertFalse(lon.capital)
        self.assertGreaterEqual(r.capitais_corrigidas, 1)


class FixDuplicadosNormalizadosTests(TestCase):
    def test_remove_ascii_duplicate_keeps_ibge(self):
        sc = Estado.objects.create(nome="SANTA CATARINA", sigla="SC", codigo_ibge=42)
        dup = Cidade.objects.create(nome="FLORIANOPOLIS", estado=sc, uf="SC", capital=False)
        good = Cidade.objects.create(
            nome="FLORIANÓPOLIS",
            estado=sc,
            uf="SC",
            capital=True,
            codigo_ibge=4450,
        )
        out = StringIO()
        call_command(
            "sanear_base_geografica",
            "--fix-duplicados-normalizados",
            stdout=out,
        )
        self.assertFalse(Cidade.objects.filter(pk=dup.pk).exists())
        self.assertTrue(Cidade.objects.filter(pk=good.pk).exists())
        self.assertEqual(Cidade.objects.filter(estado=sc).count(), 1)


class DedupeCapitaisPorUfTests(TestCase):
    def test_duas_grafias_florianopolis_remantem_uma_capital(self):
        sc = Estado.objects.create(nome="SANTA CATARINA", sigla="SC", codigo_ibge=42)
        Cidade.objects.create(nome="FLORIANOPOLIS", estado=sc, uf="SC", capital=True)
        Cidade.objects.create(nome="FLORIANÓPOLIS", estado=sc, uf="SC", capital=True, codigo_ibge=4450)
        n = dedupe_capitais_por_uf()
        self.assertGreaterEqual(n, 1)
        self.assertEqual(Cidade.objects.filter(estado=sc, capital=True).count(), 1)


class AuditoriaCommandTests(TestCase):
    def test_auditar_executa_sem_erro(self):
        buf = StringIO()
        call_command("auditar_base_geografica", stdout=buf)
        self.assertIn("Resumo", buf.getvalue())

    def test_sanear_dry_run_fix_capitais(self):
        buf = StringIO()
        call_command("sanear_base_geografica", "--dry-run", "--fix-capitais", stdout=buf)
        self.assertIn("Corrigir capitais", buf.getvalue())

    def test_estado_com_duas_capitais_aparece_na_auditoria(self):
        pr = Estado.objects.create(nome="PARANÁ", sigla="PR", codigo_ibge=41)
        Cidade.objects.create(nome="CURITIBA", estado=pr, uf="PR", capital=True, codigo_ibge=1)
        Cidade.objects.create(nome="MARINGÁ", estado=pr, uf="PR", capital=True, codigo_ibge=2)
        buf = StringIO()
        call_command("auditar_base_geografica", stdout=buf)
        out = buf.getvalue()
        self.assertIn("mais de uma capital", out.lower())
        self.assertIn("PR", out)

    def test_duplicidade_nome_estado_secao_na_auditoria(self):
        buf = StringIO()
        call_command("auditar_base_geografica", stdout=buf)
        self.assertIn("Duplicidade por nome + estado", buf.getvalue())

    def test_sanear_fix_capitais_deixa_somente_oficiais(self):
        pr = Estado.objects.create(nome="PARANÁ", sigla="PR", codigo_ibge=41)
        sp = Estado.objects.create(nome="SÃO PAULO", sigla="SP", codigo_ibge=35)
        Cidade.objects.create(nome="LONDRINA", estado=pr, uf="PR", capital=True, codigo_ibge=1)
        Cidade.objects.create(nome="CURITIBA", estado=pr, uf="PR", capital=False, codigo_ibge=2)
        Cidade.objects.create(nome="CAMPINAS", estado=sp, uf="SP", capital=True, codigo_ibge=3)
        Cidade.objects.create(nome="SÃO PAULO", estado=sp, uf="SP", capital=False, codigo_ibge=4)
        call_command("sanear_base_geografica", "--fix-capitais", stdout=StringIO())
        self.assertFalse(Cidade.objects.get(nome="LONDRINA").capital)
        self.assertTrue(Cidade.objects.get(nome="CURITIBA").capital)
        self.assertFalse(Cidade.objects.get(nome="CAMPINAS").capital)
        self.assertTrue(Cidade.objects.get(nome="SÃO PAULO").capital)
        self.assertEqual(Cidade.objects.filter(capital=True).count(), 2)
