from django.db import models
from django.utils import timezone

from cadastros.models import Servidor
from cadastros.models import TimeStampedModel
from cadastros.models import Unidade
from cadastros.models import Viatura
from core.normalizers import normalize_spaces
from core.normalizers import normalize_upper
from roteiros.models import Roteiro


class Oficio(TimeStampedModel):
    STATUS_RASCUNHO = "RASCUNHO"
    STATUS_FINALIZADO = "FINALIZADO"
    STATUS_ARQUIVADO = "ARQUIVADO"
    STATUS_CHOICES = [
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_FINALIZADO, "Finalizado"),
        (STATUS_ARQUIVADO, "Arquivado"),
    ]

    CUSTEIO_UNIDADE_DPC = "UNIDADE_DPC"
    CUSTEIO_OUTRA_INSTITUICAO = "OUTRA_INSTITUICAO"
    CUSTEIO_ONUS_LIMITADO = "ONUS_LIMITADO"
    CUSTEIO_CHOICES = [
        (CUSTEIO_UNIDADE_DPC, "Unidade DPC"),
        (CUSTEIO_OUTRA_INSTITUICAO, "Outra instituição"),
        (CUSTEIO_ONUS_LIMITADO, "Ônus limitado"),
    ]

    numero = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    ano = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    data_criacao = models.DateField(default=timezone.localdate, db_index=True)
    protocolo = models.CharField(max_length=30, blank=True, default="", db_index=True)
    assunto = models.CharField(max_length=255, blank=True, default="")
    motivo = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)
    roteiro = models.ForeignKey(
        Roteiro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oficios",
    )
    solicitante = models.ForeignKey(
        Unidade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    custeio = models.CharField(
        max_length=30,
        choices=CUSTEIO_CHOICES,
        default=CUSTEIO_UNIDADE_DPC,
    )
    custeio_observacao = models.CharField(max_length=255, blank=True, default="")
    servidores = models.ManyToManyField(Servidor, blank=True, related_name="oficios")
    viatura = models.ForeignKey(
        Viatura,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oficios",
    )
    motorista = models.ForeignKey(
        Servidor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oficios_motorista",
    )

    class Meta:
        ordering = ["-data_criacao", "-created_at"]
        verbose_name = "Ofício"
        verbose_name_plural = "Ofícios"

    def __str__(self):
        return f"Ofício {self.numero_formatado}"

    @property
    def numero_formatado(self) -> str:
        if self.numero and self.ano:
            return f"{self.numero:03d}/{self.ano}"
        return "—"

    @classmethod
    def get_next_available_numero(cls, ano: int | None = None) -> int:
        resolved_year = ano or timezone.localdate().year
        maior_numero = cls.objects.filter(ano=resolved_year).aggregate(max_numero=models.Max("numero"))[
            "max_numero"
        ]
        return (maior_numero or 0) + 1

    def save(self, *args, **kwargs):
        self.protocolo = normalize_upper(self.protocolo)
        self.assunto = normalize_spaces(self.assunto)
        self.motivo = normalize_spaces(self.motivo)
        self.custeio_observacao = normalize_spaces(self.custeio_observacao)
        super().save(*args, **kwargs)
