import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit
from scripts import qualify_branch_assignment_gaps as qualify

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"

SPECS = (
    ("Dlg/DLG_Badgeage_importation.py", "Connexion", "scanner", "body_only"),
    ("Dlg/DLG_Saisie_contrat_periode_auto.py", "Generation", "listeDates", "body_only"),
    ("Dlg/DLG_Saisie_contrat_periode_auto.py", "Generation", "nom_auto", "body_only"),
    ("Dlg/DLG_Saisie_lot_ouvertures2.py", "Validation", "expression", "body_only"),
    ("Dlg/DLG_Liste_envoi_email.py", "OnBoutonOk", "tracks", "body_only"),
    ("Dlg/DLG_Individu_coords.py", "EnvoyerEmail", "ctrl", "body_only"),
    ("Ol/OL_Prelevements_sepa.py", "MemoriseReglementHistorique", "IDcategorie", "body_only"),
    ("Ol/OL_Prelevements_sepa.py", "MemoriseReglementHistorique", "categorie", "body_only"),
)

class CallContractSafeInvariantTests2(unittest.TestCase):
    def test_candidates_are_exactly_qualified(self):
        for relative, function, name, detail in SPECS:
            findings = audit.scan_file(NOETHYS / relative, NOETHYS)
            matches = [item for item in findings if item["function"] == function and item["name"] == name and item["detail"] == detail]
            self.assertEqual(len(matches), 1, (relative, function, name))
            self.assertIn(qualify.qualification_key(matches[0], NOETHYS), qualify.EXPLICIT_SAFE)

    def test_fixed_choice_domains_remain_explicit(self):
        badge = (NOETHYS / "Dlg/DLG_Badgeage_importation.py").read_text(encoding="utf-8")
        self.assertIn('("cs1504", _(u"Symbol CS1504"))', badge)
        self.assertIn('("opn-2001", _(u"Opticon OPN-2001"))', badge)
        self.assertIn('if (appareil == "cs1504") or (appareil == "opn-2001")', badge)

        contrat = (NOETHYS / "Dlg/DLG_Saisie_contrat_periode_auto.py").read_text(encoding="utf-8")
        self.assertIn('choices=[_(u"Annuelle"), _(u"Mensuelle"), _(u"Hebdomadaire")]', contrat)
        self.assertIn('self.ctrl_periodicite.SetSelection(1)', contrat)
        for value in (0, 1, 2):
            self.assertIn(f'dictParametres["periodicite"] == {value}', contrat)

    def test_radio_group_contracts_remain_explicit(self):
        lot = (NOETHYS / "Dlg/DLG_Saisie_lot_ouvertures2.py").read_text(encoding="utf-8")
        self.assertIn('self.radio_ajouter = wx.RadioButton', lot)
        self.assertIn('style=wx.RB_GROUP', lot)
        self.assertIn('self.radio_supprimer_expression = wx.RadioButton', lot)
        self.assertIn('self.radio_supprimer_tout = wx.RadioButton', lot)
        self.assertIn('expression = self.ctrl_expression.GetValue()', lot)
        self.assertIn('expression = None', lot)

        mail = (NOETHYS / "Dlg/DLG_Liste_envoi_email.py").read_text(encoding="utf-8")
        self.assertIn('self.radio_lignes_affichees = wx.RadioButton', mail)
        self.assertIn('self.radio_lignes_cochees = wx.RadioButton', mail)
        self.assertIn('self.radio_ligne_selectionnee = wx.RadioButton', mail)
        self.assertIn('tracks = self.listview.GetFilteredObjects()', mail)
        self.assertIn('tracks = self.listview.GetCheckedObjects()', mail)
        self.assertIn('tracks = self.listview.GetSelectedObjects()', mail)

    def test_bound_event_and_internal_mode_domains_remain_explicit(self):
        coords = (NOETHYS / "Dlg/DLG_Individu_coords.py").read_text(encoding="utf-8")
        self.assertIn('if event.GetId() in (801, 802)', coords)
        self.assertIn('if event.GetId() in (901, 902)', coords)
        self.assertIn('self.Bind(wx.EVT_MENU, self.EnvoyerEmail, id=event.GetId()+1)', coords)
        self.assertIn('self.Bind(wx.EVT_MENU, self.EnvoyerEmail, id=event.GetId()+2)', coords)

        sepa = (NOETHYS / "Ol/OL_Prelevements_sepa.py").read_text(encoding="utf-8")
        self.assertIn('def MemoriseReglementHistorique(self, mode="saisie"', sepa)
        for mode in ("saisie", "modification", "suppression"):
            self.assertIn(f'if mode == "{mode}"', sepa)

if __name__ == "__main__":
    unittest.main()
