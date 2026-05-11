"""
Resolve o executável do LibreOffice para conversão DOCX→PDF (útil no Windows sem GTK do WeasyPrint).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from django.conf import settings


def resolve_libreoffice_binary() -> str | None:
    env_path = (os.getenv("SOFFICE_PATH") or os.getenv("LIBREOFFICE_SOFFICE") or "").strip()
    if env_path and Path(env_path).is_file():
        return env_path

    explicit = (getattr(settings, "DOCUMENTOS_LIBREOFFICE_BINARY", None) or "").strip()
    if explicit and Path(explicit).is_file():
        return explicit

    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found and Path(found).is_file():
            return found

    if os.name == "nt":
        for candidate in (
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ):
            if candidate.is_file():
                return str(candidate)
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            programs = Path(local) / "Programs"
            if programs.is_dir():
                for child in sorted(programs.glob("LibreOffice*")):
                    exe = child / "program" / "soffice.exe"
                    if exe.is_file():
                        return str(exe)

    for candidate in (Path("/usr/bin/libreoffice"), Path("/usr/bin/soffice")):
        if candidate.is_file():
            return str(candidate)

    return None
