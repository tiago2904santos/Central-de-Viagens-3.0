from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from cadastros.geografia import dedupe_capitais_por_uf
from cadastros.geografia import eh_capital
from cadastros.geografia import nome_normalizado_duplicidade
from cadastros.models import Cidade
from roteiros.models import Roteiro
from roteiros.models import TrechoRoteiro


def _repoint_cidade_fks(from_city_id: int, to_city_id: int) -> None:
    if from_city_id == to_city_id:
        return
    Roteiro.objects.filter(origem_id=from_city_id).update(origem_id=to_city_id)
    Roteiro.objects.filter(destino_id=from_city_id).update(destino_id=to_city_id)
    TrechoRoteiro.objects.filter(origem_id=from_city_id).update(origem_id=to_city_id)
    TrechoRoteiro.objects.filter(destino_id=from_city_id).update(destino_id=to_city_id)


class Command(BaseCommand):
    help = (
        "Saneia base geográfica interna: capitais conforme mapa oficial e, opcionalmente, mescla duplicados óbvios."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Somente exibir alterações, sem gravar.")
        parser.add_argument(
            "--fix-capitais",
            action="store_true",
            dest="fix_capitais",
            help="Recalcular capital com eh_capital(nome, uf) para todos os municípios.",
        )
        parser.add_argument(
            "--fix-duplicados",
            action="store_true",
            dest="fix_duplicados",
            help="Mesclar duplicados nome+estado (prioriza registro com codigo_ibge).",
        )
        parser.add_argument(
            "--fix-duplicados-normalizados",
            action="store_true",
            dest="fix_duplicados_normalizados",
            help=(
                "Mesclar duplicados no mesmo estado cujo nome normalizado (sem acento) coincide; "
                "mantém o registro mais completo (codigo_ibge, coordenadas)."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        fix_cap = options["fix_capitais"]
        fix_dup = options["fix_duplicados"]
        fix_dup_norm = options["fix_duplicados_normalizados"]

        if not fix_cap and not fix_dup and not fix_dup_norm:
            self.stdout.write(
                self.style.WARNING(
                    "Informe --fix-capitais, --fix-duplicados e/ou --fix-duplicados-normalizados.",
                ),
            )
            return

        if fix_cap:
            self._fix_capitais(dry_run)
        if fix_dup:
            self._fix_duplicados(dry_run)
        if fix_dup_norm:
            self._fix_duplicados_normalizados(dry_run)

    def _fix_capitais(self, dry_run: bool) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Corrigir capitais (mapa oficial)"))
        alterados = 0
        for c in Cidade.objects.select_related("estado").iterator():
            uf = (c.uf or (c.estado.sigla if c.estado else "") or "").strip().upper()[:2]
            esperado = eh_capital(c.nome, uf)
            if c.capital != esperado:
                alterados += 1
                self.stdout.write(
                    f"  pk={c.pk} {c.nome}/{uf}: capital {c.capital} -> {esperado}",
                )
                if not dry_run:
                    c.capital = esperado
                    c.save(update_fields=["capital", "updated_at"])
        dedupe_extra = 0
        if not dry_run:
            dedupe_extra = dedupe_capitais_por_uf()
        self.stdout.write(f"  Registros a ajustar: {alterados}" + (" (dry-run)" if dry_run else ""))
        if dedupe_extra:
            self.stdout.write(f"  Dedupe por UF (capital duplicada): {dedupe_extra}")
        self.stdout.write("")

    def _fix_duplicados(self, dry_run: bool) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Mesclar duplicados (nome + estado)"))
        dup_rows = list(
            Cidade.objects.values("nome", "estado_id")
            .annotate(c=Count("id"))
            .filter(c__gt=1),
        )
        removidos = 0
        for row in dup_rows:
            nome = row["nome"]
            estado_id = row["estado_id"]
            grupo = list(
                Cidade.objects.filter(nome=nome, estado_id=estado_id).select_related("estado"),
            )
            grupo.sort(key=lambda x: (0 if x.codigo_ibge is not None else 1, x.pk))
            keeper = grupo[0]
            others = grupo[1:]
            self.stdout.write(
                f'  Grupo "{nome}" estado_id={estado_id}: manter pk={keeper.pk} ibge={keeper.codigo_ibge}',
            )
            for o in others:
                self.stdout.write(f"    mesclar/remover pk={o.pk} ibge={o.codigo_ibge}")
                if dry_run:
                    removidos += 1
                    continue
                upd_fields: list[str] = []
                if keeper.latitude is None and o.latitude is not None:
                    keeper.latitude = o.latitude
                    upd_fields.append("latitude")
                if keeper.longitude is None and o.longitude is not None:
                    keeper.longitude = o.longitude
                    upd_fields.append("longitude")
                if keeper.codigo_ibge is None and o.codigo_ibge is not None:
                    keeper.codigo_ibge = o.codigo_ibge
                    upd_fields.append("codigo_ibge")
                with transaction.atomic():
                    if upd_fields:
                        upd_fields.append("updated_at")
                        keeper.save(update_fields=upd_fields)
                    else:
                        keeper.save(update_fields=["updated_at"])
                    _repoint_cidade_fks(o.pk, keeper.pk)
                    o.delete()
                removidos += 1
        self.stdout.write(f"  Grupos com duplicidade: {len(dup_rows)}")
        self.stdout.write(f"  Registros duplicados a remover: {removidos}" + (" (dry-run)" if dry_run else ""))
        self.stdout.write("")

    def _fix_duplicados_normalizados(self, dry_run: bool) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Mesclar duplicados (nome normalizado + estado)"))
        by_group: dict[tuple[int, str], list[Cidade]] = defaultdict(list)
        for c in Cidade.objects.select_related("estado").iterator():
            key = (c.estado_id, nome_normalizado_duplicidade(c.nome))
            by_group[key].append(c)

        removidos = 0
        grupos = 0
        for (_estado_id, nome_norm), grupo in by_group.items():
            if len(grupo) <= 1:
                continue
            grupos += 1
            grupo.sort(
                key=lambda x: (
                    x.codigo_ibge is None,
                    x.latitude is None,
                    x.longitude is None,
                    x.pk,
                ),
            )
            keeper = grupo[0]
            others = grupo[1:]
            self.stdout.write(
                f'  Grupo norm="{nome_norm}" estado_id={keeper.estado_id}: '
                f"manter pk={keeper.pk} nome={keeper.nome!r} ibge={keeper.codigo_ibge}",
            )
            for o in others:
                self.stdout.write(
                    f"    remover pk={o.pk} nome={o.nome!r} ibge={o.codigo_ibge}",
                )
                if dry_run:
                    removidos += 1
                    continue
                upd_fields: list[str] = []
                if keeper.latitude is None and o.latitude is not None:
                    keeper.latitude = o.latitude
                    upd_fields.append("latitude")
                if keeper.longitude is None and o.longitude is not None:
                    keeper.longitude = o.longitude
                    upd_fields.append("longitude")
                if keeper.codigo_ibge is None and o.codigo_ibge is not None:
                    keeper.codigo_ibge = o.codigo_ibge
                    upd_fields.append("codigo_ibge")
                with transaction.atomic():
                    if upd_fields:
                        upd_fields.append("updated_at")
                        keeper.save(update_fields=upd_fields)
                    _repoint_cidade_fks(o.pk, keeper.pk)
                    o.delete()
                removidos += 1
        self.stdout.write(f"  Grupos com colisão normalizada: {grupos}")
        self.stdout.write(f"  Registros removidos: {removidos}" + (" (dry-run)" if dry_run else ""))
        self.stdout.write("")
