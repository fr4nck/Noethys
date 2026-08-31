from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit("pattern not found in %s" % path)
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


# 1) Gestion : un élément de liste d'un type inattendu ne doit pas finir en
# UnboundLocalError sur `date`. On rejette explicitement le contrat invalide.
path = ROOT / "noethys/Utils/UTILS_Gestion.py"
replace_once(
    path,
    '''            elif type(donnees) == dict:\n                date = donnees["date"]\n                if type(date) in (str, six.text_type):\n                    date = UTILS_Dates.DateEngEnDateDD(date)\n\n            # Vérifie que la date n'est pas dans une période de gestion\n''',
    '''            elif type(donnees) == dict:\n                date = donnees["date"]\n                if type(date) in (str, six.text_type):\n                    date = UTILS_Dates.DateEngEnDateDD(date)\n            else:\n                raise TypeError("Type de donnée de gestion non supporté : %s" % type(donnees).__name__)\n\n            # Vérifie que la date n'est pas dans une période de gestion\n''',
)

# 2) Printer/Phoenix : l'absence inattendue de ControlBar ne doit pas produire
# un UnboundLocalError opaque. On rend l'échec explicite et localisé.
path = ROOT / "noethys/Utils/UTILS_Printer.py"
replace_once(
    path,
    '''        else:\n            for ctrl in self.GetChildren():\n                if "ControlBar" in str(ctrl):\n                    controlBar = ctrl\n\n        liste_controles = controlBar.GetChildren()\n''',
    '''        else:\n            controlBar = None\n            for ctrl in self.GetChildren():\n                if "ControlBar" in str(ctrl):\n                    controlBar = ctrl\n                    break\n            if controlBar is None:\n                raise RuntimeError("Barre de contrôle d'aperçu introuvable")\n\n        liste_controles = controlBar.GetChildren()\n''',
)

# 3) Anniversaires : seuls deux modes sont supportés. Un mode corrompu doit
# être rejeté avant l'utilisation de listeIndividus.
path = ROOT / "noethys/Dlg/DLG_Anniversaires.py"
replace_once(
    path,
    '''        if dictParametres["mode"] == "inscrits":\n\n            dictOuvertures = {}\n''',
    '''        elif dictParametres["mode"] == "inscrits":\n\n            dictOuvertures = {}\n''',
)
replace_once(
    path,
    '''            DB.ExecuterReq(req)\n            listeIndividus = DB.ResultatReq()\n\n        DB.Close()\n\n        if len(listeIndividus) == 0:\n''',
    '''            DB.ExecuterReq(req)\n            listeIndividus = DB.ResultatReq()\n        else:\n            DB.Close()\n            raise ValueError("Mode anniversaire inconnu : %s" % dictParametres["mode"])\n\n        DB.Close()\n\n        if len(listeIndividus) == 0:\n''',
)

# Tests ciblés : AST/source léger, sans importer wx ni les dépendances legacy.
test = ROOT / "tests/test_branch_contracts_batch_15.py"
test.write_text(r'''import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGETS = {
    ("Utils/UTILS_Gestion.py", "Verification", "date"),
    ("Utils/UTILS_Printer.py", "__init__", "controlBar"),
    ("Dlg/DLG_Anniversaires.py", "OnBoutonOk", "listeIndividus"),
}


class TestBatch15RealContracts(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        remaining = set()
        for relpath, function, name in TARGETS:
            path = NOETHYS / relpath
            for item in audit.scan_file(path, NOETHYS):
                key = (item["file"], item["function"], item["name"])
                if key in TARGETS:
                    remaining.add(key)
        self.assertEqual(remaining, set())

    def test_gestion_rejects_unsupported_items_explicitly(self):
        source = (NOETHYS / "Utils/UTILS_Gestion.py").read_text(encoding="utf-8")
        self.assertIn('raise TypeError("Type de donnée de gestion non supporté', source)

    def test_printer_requires_preview_control_bar_explicitly(self):
        source = (NOETHYS / "Utils/UTILS_Printer.py").read_text(encoding="utf-8")
        self.assertIn("controlBar = None", source)
        self.assertIn("if controlBar is None:", source)
        self.assertIn("Barre de contrôle d'aperçu introuvable", source)

    def test_anniversaires_rejects_unknown_mode_explicitly(self):
        source = (NOETHYS / "Dlg/DLG_Anniversaires.py").read_text(encoding="utf-8")
        self.assertIn('elif dictParametres["mode"] == "inscrits":', source)
        self.assertIn('raise ValueError("Mode anniversaire inconnu', source)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
