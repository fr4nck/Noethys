import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Dlg" / "DLG_Badgeage_interface.py"


class TestBadgeageOpenConsumptionBatch20(unittest.TestCase):
    def test_selected_open_consumption_is_used_after_scan(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("if heure_debut == \"pointee\" and heure_fin == \"pointee\":")
        end = source.index("# On Vérifie que le badgeage de début", start)
        block = source[start:end]
        self.assertIn("conso_a_modifier = conso", block)
        self.assertIn("heureDebut = conso_a_modifier.heure_debut", block)
        self.assertIn("badgeage_debut = conso_a_modifier.badgeage_debut", block)
        self.assertNotIn("heureDebut = conso.heure_debut", block)
        self.assertNotIn("badgeage_debut = conso.badgeage_debut", block)

    def test_saisie_conso_receives_selected_consumption(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("conso=conso_a_modifier", source)


if __name__ == "__main__":
    unittest.main()
