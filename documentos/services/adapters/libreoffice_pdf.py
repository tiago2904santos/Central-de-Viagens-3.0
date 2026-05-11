from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def convert_docx_to_pdf_libreoffice(*, docx_bytes: bytes, libreoffice_binary: str) -> bytes:
    """
    Converte DOCX em PDF via LibreOffice em modo headless (sem unoserver).
    """
    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp)
        docx_path = tdir / "entrada.docx"
        docx_path.write_bytes(docx_bytes)
        subprocess.run(
            [
                libreoffice_binary,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tdir),
                str(docx_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        pdf_path = tdir / "entrada.pdf"
        if not pdf_path.exists():
            raise RuntimeError("LibreOffice não gerou o arquivo PDF esperado.")
        return pdf_path.read_bytes()


def convert_docx_to_pdf_unoserver(*, docx_bytes: bytes, unoserver_url: str) -> bytes:
    """
    Placeholder para integração HTTP com unoserver (mesma rede interna).
    Quando o endpoint institucional estiver disponível, implementar chamada real.
    """
    _ = (docx_bytes, unoserver_url)
    raise NotImplementedError(
        "Conversão via unoserver não configurada. Use LibreOffice local ou WeasyPrint.",
    )
