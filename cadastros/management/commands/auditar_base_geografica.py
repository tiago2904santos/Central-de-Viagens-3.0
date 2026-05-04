from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models import Q

from cadastros.geografia import CAPITAIS_POR_UF
from cadastros.geografia import eh_capital
from cadastros.models import Cidade
from cadastros.models import Estado


class Command(BaseCommand):
    help = "Audita consistência da base geográfica interna (Estados e Cidade/município)."

    def handle(self, *args, **options):
        self._bloco_resumo()
        self._bloco_capitais_lista()
        self._bloco_estados_sem_capital()
        self._bloco_estados_multi_capital()
        self._bloco_dup_nome_estado()
        self._bloco_dup_codigo_ibge()
        self._bloco_sem_estado()
        self._bloco_uf_divergente()
        self._bloco_suspeitos()

    def _bloco_resumo(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Resumo"))
        self.stdout.write(f"  Total de estados:              {Estado.objects.count()}")
        self.stdout.write(f"  Total de cidades/municípios:   {Cidade.objects.count()}")
        self.stdout.write(f"  Total com capital=True:        {Cidade.objects.filter(capital=True).count()}")
        self.stdout.write("")

    def _bloco_capitais_lista(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Capitais marcadas (capital=True)"))
        qs = (
            Cidade.objects.filter(capital=True)
            .select_related("estado")
            .order_by("estado__sigla", "nome")
        )
        if not qs.exists():
            self.stdout.write("  (nenhuma)")
        else:
            self.stdout.write(f"  {'UF':<4} {'Estado':<22} {'Cidade':<28} {'codigo_ibge'}")
            for c in qs:
                est = c.estado
                self.stdout.write(
                    f"  {c.uf:<4} {(est.nome if est else '?')[:22]:<22} {c.nome[:28]:<28} {c.codigo_ibge or '—'}",
                )
        self.stdout.write("")

    def _bloco_estados_sem_capital(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Estados sem nenhuma cidade com capital=True"))
        sem = []
        for est in Estado.objects.order_by("sigla"):
            if not Cidade.objects.filter(estado=est, capital=True).exists():
                sem.append(est)
        if not sem:
            self.stdout.write("  (nenhum)")
        else:
            for est in sem:
                self.stdout.write(f"  {est.sigla} — {est.nome}")
        self.stdout.write("")

    def _bloco_estados_multi_capital(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Estados com mais de uma capital (capital=True)"))
        qs = (
            Estado.objects.annotate(n_cap=Count("cidades", filter=Q(cidades__capital=True)))
            .filter(n_cap__gt=1)
            .order_by("sigla")
        )
        if not qs.exists():
            self.stdout.write("  (nenhum)")
        else:
            for est in qs:
                caps = Cidade.objects.filter(estado=est, capital=True).values_list("nome", "codigo_ibge")
                self.stdout.write(f"  {est.sigla} ({est.nome}): {est.n_cap} capitais — {list(caps)}")
        self.stdout.write("")

    def _bloco_dup_nome_estado(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Duplicidade por nome + estado"))
        dup = (
            Cidade.objects.values("nome", "estado_id")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        if not dup.exists():
            self.stdout.write("  (nenhuma)")
        else:
            for row in dup:
                cidades = Cidade.objects.filter(nome=row["nome"], estado_id=row["estado_id"]).values_list(
                    "id",
                    "codigo_ibge",
                    "capital",
                )
                self.stdout.write(f'  "{row["nome"]}" estado_id={row["estado_id"]}: {list(cidades)}')
        self.stdout.write("")

    def _bloco_dup_codigo_ibge(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Duplicidade por codigo_ibge"))
        dup = (
            Cidade.objects.exclude(codigo_ibge__isnull=True)
            .values("codigo_ibge")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        if not dup.exists():
            self.stdout.write("  (nenhuma)")
        else:
            for row in dup:
                cod = row["codigo_ibge"]
                regs = Cidade.objects.filter(codigo_ibge=cod).values_list("id", "nome", "estado_id")
                self.stdout.write(f"  codigo_ibge={cod}: {list(regs)}")
        self.stdout.write("")

    def _bloco_sem_estado(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Cidades sem estado (FK)"))
        # estado é obrigatório no modelo atual; mantemos verificação defensiva
        qs = Cidade.objects.filter(estado__isnull=True)
        self.stdout.write(f"  Total: {qs.count()}")
        self.stdout.write("")

    def _bloco_uf_divergente(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Cidades com UF diferente de estado.sigla"))
        divergentes = []
        for c in Cidade.objects.select_related("estado").iterator():
            if c.estado and c.uf != c.estado.sigla:
                divergentes.append((c.pk, c.nome, c.uf, c.estado.sigla))
        if not divergentes:
            self.stdout.write("  (nenhuma)")
        else:
            for item in divergentes:
                self.stdout.write(f"  pk={item[0]} {item[1]} uf={item[2]} estado.sigla={item[3]}")
        self.stdout.write("")

    def _bloco_suspeitos(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Registros suspeitos"))
        sus_cap_mal = []
        sem_ibge = []
        sem_coords = []
        for c in Cidade.objects.select_related("estado").iterator():
            uf = c.uf or (c.estado.sigla if c.estado else "")
            if c.capital and not eh_capital(c.nome, uf):
                sus_cap_mal.append((c.pk, c.nome, uf, c.codigo_ibge))
            if c.codigo_ibge is None:
                sem_ibge.append((c.pk, c.nome, uf))
            if c.latitude is None or c.longitude is None:
                sem_coords.append((c.pk, c.nome, uf))

        self.stdout.write("  capital=True fora do mapa oficial (eh_capital=False):")
        if not sus_cap_mal:
            self.stdout.write("    (nenhum)")
        else:
            for t in sus_cap_mal:
                self.stdout.write(f"    pk={t[0]} {t[1]}/{t[2]} ibge={t[3]}")

        self.stdout.write(f"  Sem codigo_ibge: {len(sem_ibge)} registro(s) (mostrar até 15)")
        for t in sem_ibge[:15]:
            self.stdout.write(f"    pk={t[0]} {t[1]}/{t[2]}")
        if len(sem_ibge) > 15:
            self.stdout.write(f"    ... e mais {len(sem_ibge) - 15}")

        self.stdout.write(f"  Sem latitude ou longitude: {len(sem_coords)} registro(s) (mostrar até 10)")
        for t in sem_coords[:10]:
            self.stdout.write(f"    pk={t[0]} {t[1]}/{t[2]}")
        if len(sem_coords) > 10:
            self.stdout.write(f"    ... e mais {len(sem_coords) - 10}")

        self.stdout.write("")
        self.stdout.write(
            f"  Mapa oficial: {len(CAPITAIS_POR_UF)} UFs (deve haver no máximo uma capital por UF).",
        )
