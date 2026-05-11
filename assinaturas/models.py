import uuid

from django.db import models


class ConfiguracaoChaveAssinatura(models.Model):
    STORAGE_PKCS12 = "pkcs12"
    STORAGE_PKCS11 = "pkcs11"
    STORAGE_CHOICES = [
        (STORAGE_PKCS12, "PKCS#12"),
        (STORAGE_PKCS11, "PKCS#11"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=120)
    storage_kind = models.CharField(max_length=16, choices=STORAGE_CHOICES, default=STORAGE_PKCS12)
    alias = models.CharField(max_length=120, blank=True, default="")
    pkcs12_path = models.CharField(max_length=512, blank=True, default="")
    certificate_fingerprint_sha256 = models.CharField(max_length=64, blank=True, default="")
    ativo = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = "Configuração de chave de assinatura"
        verbose_name_plural = "Configurações de chaves de assinatura"

    def __str__(self) -> str:
        return self.nome


class AssinaturaDigital(models.Model):
    STATUS_PENDING = "pending"
    STATUS_VALID = "valid"
    STATUS_INVALID = "invalid"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendente"),
        (STATUS_VALID, "Válida"),
        (STATUS_INVALID, "Inválida"),
        (STATUS_FAILED, "Falhou"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artefato = models.ForeignKey(
        "documentos.DocumentoArtefato",
        on_delete=models.CASCADE,
        related_name="assinaturas_registro",
    )
    chave = models.ForeignKey(
        ConfiguracaoChaveAssinatura,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assinaturas_emitidas",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    signer_subject = models.CharField(max_length=512, blank=True, default="")
    signer_serial = models.CharField(max_length=255, blank=True, default="")
    hash_documento = models.CharField(max_length=64)
    hash_documento_assinado = models.CharField(max_length=64, blank=True, default="")
    signature_field_name = models.CharField(max_length=120, default="AssinaturaCentralViagens")
    appearance = models.JSONField(default=dict, blank=True)
    evidencias = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    validado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Assinatura digital"
        verbose_name_plural = "Assinaturas digitais"

    def __str__(self) -> str:
        return f"{self.status} — {self.artefato_id}"


class EventoAssinatura(models.Model):
    id = models.BigAutoField(primary_key=True)
    assinatura = models.ForeignKey(
        AssinaturaDigital,
        on_delete=models.CASCADE,
        related_name="eventos",
    )
    tipo = models.CharField(max_length=32, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Evento de assinatura"
        verbose_name_plural = "Eventos de assinatura"

    def __str__(self) -> str:
        return f"{self.tipo} @ {self.criado_em}"
