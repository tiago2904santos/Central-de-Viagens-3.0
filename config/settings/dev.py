import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Respeita .env; se LOGIN_ENFORCED nao estiver definido, desliga login obrigatorio em dev (testes manuais / agentes).
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
if "LOGIN_ENFORCED" not in os.environ:
    os.environ["LOGIN_ENFORCED"] = "false"

from .base import *


DEBUG = True

# No Windows, WeasyPrint costuma faltar GTK; LibreOffice pode não estar instalado.
# Habilita PDF mínimo (fpdf2) como último recurso, salvo override explícito no .env.
if sys.platform == "win32" and "DOCUMENTOS_SIMPLE_PDF_FALLBACK" not in os.environ:
    DOCUMENTOS_SIMPLE_PDF_FALLBACK = True

required_db_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD"]
missing_db_vars = [name for name in required_db_vars if not os.getenv(name)]

if missing_db_vars:
    raise RuntimeError(
        f"Variaveis de banco ausentes no .env: {', '.join(missing_db_vars)}"
    )

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
