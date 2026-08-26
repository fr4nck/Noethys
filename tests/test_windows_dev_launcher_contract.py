# -*- coding: utf-8 -*-
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dev_windows.ps1"


class WindowsDevLauncherTests(unittest.TestCase):
    def test_le_hash_ne_depend_pas_de_get_file_hash(self):
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertNotIn("Get-FileHash", source)
        self.assertIn("function Get-NoethysFileSha256", source)
        self.assertIn("[System.Security.Cryptography.SHA256]::Create()", source)
        self.assertIn("[System.IO.File]::OpenRead($Path)", source)

    def test_les_ressources_de_hashage_sont_liberees(self):
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("$sha256.Dispose()", source)
        self.assertIn("$stream.Dispose()", source)

    def test_les_deux_fichiers_requirements_utilisent_le_repli(self):
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("$hash1 = Get-NoethysFileSha256 $ReqBuild", source)
        self.assertIn("$hash2 = Get-NoethysFileSha256 $ReqRuntime", source)


if __name__ == "__main__":
    unittest.main()
