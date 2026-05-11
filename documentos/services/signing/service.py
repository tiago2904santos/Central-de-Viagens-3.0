from __future__ import annotations

from io import BytesIO
from typing import Any

from django.conf import settings


class ServicoAssinaturaPDF:
    """Assina bytes de PDF conforme `SIGNATURE_BACKEND` nos settings."""

    def assinar(self, pdf_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
        return assinar_pdf_final(pdf_bytes)


def assinar_pdf_final(pdf_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    backend = (getattr(settings, "SIGNATURE_BACKEND", "disabled") or "disabled").lower()
    if backend == "disabled":
        return pdf_bytes, {"backend": "disabled"}
    if backend == "pkcs12":
        return _assinar_pkcs12(pdf_bytes)
    raise ValueError(f"Backend de assinatura não suportado: {backend}")


def _assinar_pkcs12(pdf_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    path = getattr(settings, "SIGNATURE_PKCS12_PATH", None)
    if not path:
        raise RuntimeError("SIGNATURE_PKCS12_PATH não configurado.")
    password = getattr(settings, "SIGNATURE_PKCS12_PASSWORD", None) or ""

    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.signers import PdfSignatureMetadata
    from pyhanko.sign.signers import PdfSigner
    from pyhanko.sign.signers import SimpleSigner

    passphrase = password.encode("utf-8") if password else None
    simple = SimpleSigner.load_pkcs12(pfx_file=path, passphrase=passphrase)

    reader = PdfFileReader(BytesIO(pdf_bytes))
    writer = IncrementalPdfFileWriter(reader)
    meta = PdfSignatureMetadata(field_name="AssinaturaCentralViagens")
    pdf_signer = PdfSigner(signature_meta=meta, signer=simple)
    out = BytesIO()
    pdf_signer.sign_pdf(writer, output=out)
    return out.getvalue(), {"backend": "pkcs12"}
