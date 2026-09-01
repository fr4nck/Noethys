from pathlib import Path

source_path = Path('noethys/Dlg/DLG_Badgeage_interface.py')
source = source_path.read_text(encoding='utf-8')
old = '''                else:\n                    # Si on doit modifier une conso existante\n                    heureDebut = conso.heure_debut\n                    heureFin = heure\n                    badgeage_debut = conso.badgeage_debut\n                    badgeage_fin = maintenant\n'''
new = '''                else:\n                    # Si on doit modifier une conso existante\n                    heureDebut = conso_a_modifier.heure_debut\n                    heureFin = heure\n                    badgeage_debut = conso_a_modifier.badgeage_debut\n                    badgeage_fin = maintenant\n'''
if old not in source:
    raise SystemExit('badgeage open consumption pattern not found')
source = source.replace(old, new, 1)
source_path.write_text(source, encoding='utf-8')

test_path = Path('tests/test_badgeage_open_consumption_batch_20.py')
test_path.write_text('''import unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nSOURCE = ROOT / "noethys" / "Dlg" / "DLG_Badgeage_interface.py"\n\n\nclass TestBadgeageOpenConsumptionBatch20(unittest.TestCase):\n    def test_selected_open_consumption_is_used_after_scan(self):\n        source = SOURCE.read_text(encoding="utf-8")\n        start = source.index("if heure_debut == \\\"pointee\\\" and heure_fin == \\\"pointee\\\":")\n        end = source.index("# On Vérifie que le badgeage de début", start)\n        block = source[start:end]\n        self.assertIn("conso_a_modifier = conso", block)\n        self.assertIn("heureDebut = conso_a_modifier.heure_debut", block)\n        self.assertIn("badgeage_debut = conso_a_modifier.badgeage_debut", block)\n        self.assertNotIn("heureDebut = conso.heure_debut", block)\n        self.assertNotIn("badgeage_debut = conso.badgeage_debut", block)\n\n    def test_saisie_conso_receives_selected_consumption(self):\n        source = SOURCE.read_text(encoding="utf-8")\n        self.assertIn("conso=conso_a_modifier", source)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding='utf-8')
