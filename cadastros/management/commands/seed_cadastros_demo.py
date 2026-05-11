"""
Cria 5 registos de demonstração por tipo de cadastro (unidades, cargos, combustíveis, servidores, viaturas).

Remove apenas registos anteriores deste comando (marcador ``[DEMO]`` no nome, placas ``XZD``).
A configuração do sistema (singleton) é atualizada com cidade sede Curitiba/PR se existir após importação IBGE.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from cadastros.models import Cargo
from cadastros.models import Cidade
from cadastros.models import Combustivel
from cadastros.models import ConfiguracaoSistema
from cadastros.models import Estado
from cadastros.models import Servidor
from cadastros.models import Unidade
from cadastros.models import Viatura


DEMO_TAG = "[DEMO]"
N = 5


class Command(BaseCommand):
    help = "Cria 5 unidades, 5 cargos, 5 combustíveis, 5 servidores e 5 viaturas de demonstração."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-config",
            action="store_true",
            help="Não atualizar ConfiguracaoSistema (cidade sede Curitiba).",
        )

    def handle(self, *args, **options):
        skip_config: bool = options["skip_config"]

        with transaction.atomic():
            self._limpar_demo_anterior()

            unidades: list[Unidade] = []
            for i in range(1, N + 1):
                unidades.append(
                    Unidade.objects.create(
                        nome=f"{DEMO_TAG} UNIDADE {i:02d}",
                        sigla=f"DU{i:02d}",
                    ),
                )

            cargos: list[Cargo] = []
            for i in range(1, N + 1):
                cargos.append(
                    Cargo.objects.create(
                        nome=f"{DEMO_TAG} CARGO {i:02d}",
                        is_padrao=(i == 1),
                    ),
                )

            combustiveis: list[Combustivel] = []
            for i in range(1, N + 1):
                combustiveis.append(
                    Combustivel.objects.create(
                        nome=f"{DEMO_TAG} COMBUSTIVEL {i:02d}",
                        is_padrao=(i == 1),
                    ),
                )

            servidores: list[Servidor] = []
            for i in range(1, N + 1):
                cpf = f"{i:011d}"  # 00000000001 … 00000000005
                servidores.append(
                    Servidor.objects.create(
                        nome=f"{DEMO_TAG} SERVIDOR {i:02d}",
                        cargo=cargos[i - 1],
                        cpf=cpf,
                        sem_rg=True,
                        telefone=f"4199999000{i}",
                        unidade=unidades[i - 1],
                    ),
                )

            placas = [f"XZD{i:04d}" for i in range(1001, 1001 + N)]
            for i in range(N):
                v = Viatura.objects.create(
                    placa=placas[i],
                    modelo=f"{DEMO_TAG} MODELO {i + 1:02d}",
                    combustivel=combustiveis[i],
                    tipo=Viatura.TIPO_CARACTERIZADA,
                )
                v.motoristas.add(servidores[i])

            if not skip_config:
                self._atualizar_config_curitiba()

        self.stdout.write(
            self.style.SUCCESS(
                f"Criados {N} unidades, {N} cargos, {N} combustíveis, {N} servidores e {N} viaturas {DEMO_TAG}.",
            ),
        )

    def _limpar_demo_anterior(self):
        Viatura.objects.filter(placa__startswith="XZD").delete()
        Servidor.objects.filter(nome__contains=DEMO_TAG).delete()
        Combustivel.objects.filter(nome__contains=DEMO_TAG).delete()
        Cargo.objects.filter(nome__contains=DEMO_TAG).delete()
        Unidade.objects.filter(nome__contains=DEMO_TAG).delete()

    def _atualizar_config_curitiba(self):
        est = Estado.objects.filter(sigla="PR").first()
        if not est:
            self.stdout.write(self.style.WARNING("PR não encontrado: configure cidade sede manualmente."))
            return
        cidade = Cidade.objects.filter(estado=est, nome="CURITIBA").first()
        if not cidade:
            self.stdout.write(
                self.style.WARNING("CURITIBA/PR não encontrada: importe a geografia IBGE ou configure manualmente."),
            )
            return
        cfg = ConfiguracaoSistema.get_singleton()
        cfg.cidade_sede_padrao = cidade
        cfg.uf = "PR"
        cfg.cidade_endereco = "CURITIBA"
        cfg.save()
        self.stdout.write(self.style.NOTICE("Configuração: cidade sede padrão = CURITIBA/PR."))
