from pathlib import Path

replacements = {
    "noethys/Ctrl/CTRL_Saisie_pays.py": [(
'''        if IDpays is not None:\n            pays = self.Recherche_Pays(IDpays=IDpays)\n        if nomPays is not None:\n            pays = self.Recherche_Pays(nomPays=nomPays)\n        self.IDpays = pays[0]\n''',
'''        if nomPays is not None:\n            pays = self.Recherche_Pays(nomPays=nomPays)\n        else:\n            pays = self.Recherche_Pays(IDpays=IDpays)\n        self.IDpays = pays[0]\n''')],
    "noethys/Ctrl/CTRL_Editeur_email.py": [(
'''        if self.ctrl_editeur.GetStyle(ip, attr):\n            r = rt.RichTextRange(ip, ip)\n            if self.ctrl_editeur.HasSelection():\n                r = self.ctrl_editeur.GetSelectionRange()\n\n        if attr.GetLeftIndent() >= 100:\n''',
'''        if not self.ctrl_editeur.GetStyle(ip, attr):\n            return\n        r = rt.RichTextRange(ip, ip)\n        if self.ctrl_editeur.HasSelection():\n            r = self.ctrl_editeur.GetSelectionRange()\n\n        if attr.GetLeftIndent() >= 100:\n''')],
    "noethys/Dlg/DLG_Saisie_texte_rappel.py": [(
'''        if self.ctrl_texte.GetStyle(ip, attr):\n            r = rt.RichTextRange(ip, ip)\n            if self.ctrl_texte.HasSelection():\n                r = self.ctrl_texte.GetSelectionRange()\n\n        if attr.GetLeftIndent() >= 100:\n''',
'''        if not self.ctrl_texte.GetStyle(ip, attr):\n            return\n        r = rt.RichTextRange(ip, ip)\n        if self.ctrl_texte.HasSelection():\n            r = self.ctrl_texte.GetSelectionRange()\n\n        if attr.GetLeftIndent() >= 100:\n''')],
    "noethys/Dlg/DLG_Planning_transports.py": [(
'''        dlg = DLG_Recherche_date(self)\n        if dlg.ShowModal():\n            newDate = dlg.GetDate()\n        dlg.Destroy()\n        self.parent.ctrl_planning.SetDate(newDate)\n''',
'''        dlg = DLG_Recherche_date(self)\n        if dlg.ShowModal() == wx.ID_OK:\n            newDate = dlg.GetDate()\n            dlg.Destroy()\n            self.parent.ctrl_planning.SetDate(newDate)\n        else:\n            dlg.Destroy()\n''')],
    "noethys/Dlg/DLG_Portail_renseignements.py": [(
'''    def SetValeur(self, champ="", valeur=None):\n        if champ == "adresse_auto" :\n            resultat = self.ctrl_adresse_auto.SetID(valeur)\n            self.OnChoix()\n        if champ == "rue_resid" :\n            resultat = True\n            self.ctrl_rue.SetValue(valeur)\n        if champ == "cp_resid" :\n            resultat = self.ctrl_ville.SetValueCP(valeur)\n        if champ == "ville_resid" :\n            resultat = True\n            self.ctrl_ville.SetValueVille(valeur)\n        return resultat\n''',
'''    def SetValeur(self, champ="", valeur=None):\n        if champ == "adresse_auto" :\n            resultat = self.ctrl_adresse_auto.SetID(valeur)\n            self.OnChoix()\n        elif champ == "rue_resid" :\n            resultat = True\n            self.ctrl_rue.SetValue(valeur)\n        elif champ == "cp_resid" :\n            resultat = self.ctrl_ville.SetValueCP(valeur)\n        elif champ == "ville_resid" :\n            resultat = True\n            self.ctrl_ville.SetValueVille(valeur)\n        else:\n            raise ValueError("Champ d'adresse inconnu : %s" % champ)\n        return resultat\n''')],
}

for filename, changes in replacements.items():
    path = Path(filename)
    text = path.read_text(encoding="utf-8")
    for old, new in changes:
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f"{filename}: remplacement ambigu/introuvable ({count})")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

Path("tests/test_small_ui_branch_contracts_batch_11.py").write_text(r'''import ast
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGETS = {
    "noethys/Ctrl/CTRL_Saisie_pays.py": {("SetValue", "pays")},
    "noethys/Ctrl/CTRL_Editeur_email.py": {("OnIndentLess", "r")},
    "noethys/Dlg/DLG_Saisie_texte_rappel.py": {("OnIndentLess", "r")},
    "noethys/Dlg/DLG_Planning_transports.py": {("OnChercherDate", "newDate")},
    "noethys/Dlg/DLG_Portail_renseignements.py": {("SetValeur", "resultat")},
}

class TestBatch11Contracts(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        for relpath, targets in TARGETS.items():
            findings = audit.scan_file(ROOT / relpath, ROOT / "noethys")
            remaining = {(x.get("function"), x.get("name")) for x in findings}
            self.assertTrue(targets.isdisjoint(remaining), (relpath, targets & remaining))

    def test_cancelled_date_search_does_not_use_unassigned_date(self):
        text = (ROOT / "noethys/Dlg/DLG_Planning_transports.py").read_text(encoding="utf-8")
        self.assertIn("if dlg.ShowModal() == wx.ID_OK:", text)
        self.assertIn("self.parent.ctrl_planning.SetDate(newDate)", text)

    def test_unknown_address_field_is_explicit(self):
        text = (ROOT / "noethys/Dlg/DLG_Portail_renseignements.py").read_text(encoding="utf-8")
        self.assertIn('raise ValueError("Champ d\'adresse inconnu : %s" % champ)', text)

if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
