import tempfile
from pathlib import Path

from django.test import SimpleTestCase
from django.test import override_settings

from documentos.services.libreoffice_resolve import resolve_libreoffice_binary


class LibreOfficeResolveTests(SimpleTestCase):
    @override_settings(DOCUMENTOS_LIBREOFFICE_BINARY="")
    def test_explicit_setting_empty_uses_discovery(self):
        _ = resolve_libreoffice_binary()
        # Result depends on machine; call must not raise.
        self.assertTrue(_ is None or Path(_).is_file())

    def test_explicit_path_wins(self):
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp:
            path = tmp.name
        try:
            with override_settings(DOCUMENTOS_LIBREOFFICE_BINARY=path):
                self.assertEqual(resolve_libreoffice_binary(), path)
        finally:
            Path(path).unlink(missing_ok=True)
