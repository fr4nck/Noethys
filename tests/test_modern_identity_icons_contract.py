# -*- coding: utf-8 -*-
"""Contrat statique des pictogrammes de personnes et organisations."""

import ast
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHEMINS = ROOT / "noethys" / "Chemins.py"
IDENTITES = ROOT / "noethys" / "Utils" / "UTILS_Icones_identites.py"
CIVILITES = ROOT / "noethys" / "Data" / "DATA_Civilites.py"


class ModernIdentityIconsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chemins_text = CHEMINS.read_text(encoding="utf-8")
        cls.identites_text = IDENTITES.read_text(encoding="utf-8")
        cls.civilites_text = CIVILITES.read_text(encoding="utf-8")
        ast.parse(cls.chemins_text)
        ast.parse(cls.identites_text)
        ast.parse(cls.civilites_text)
        spec = importlib.util.spec_from_file_location("noethys_identity_icons_contract", IDENTITES)
        cls.identites = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.identites)

    def test_identity_layer_precedes_generic_icon_layer(self):
        pos_identity = self.chemins_text.index("UTILS_Icones_identites")
        pos_generic = self.chemins_text.index("UTILS_Icones_modernes")
        self.assertLess(pos_identity, pos_generic)

    def test_people_and_children_are_mapped(self):
        for filename in ("Homme.png", "Femme.png"):
            self.assertEqual(self.identites._identite_pour_chemin(filename), ("person", None))
        for filename in ("Garcon.png", "Fille.png"):
            self.assertEqual(self.identites._identite_pour_chemin(filename), ("child", None))
        self.assertEqual(self.identites._identite_pour_chemin("Personnes.png"), ("family", None))

    def test_family_actions_keep_the_entity_and_action(self):
        self.assertEqual(self.identites._identite_pour_chemin("Famille_ajouter.png"), ("family", "add"))
        self.assertEqual(self.identites._identite_pour_chemin("Famille_modifier.png"), ("family", "edit"))
        self.assertEqual(self.identites._identite_pour_chemin("Famille_supprimer.png"), ("family", "delete"))

    def test_organizations_are_visually_distinct_categories(self):
        expected = {
            "Association.png": "association",
            "Ecole.png": "school",
            "Mairie.png": "civic",
            "Commune.png": "civic",
            "Collectivite.png": "civic",
            "Organisme.png": "institution",
            "Institution.png": "institution",
            "Entreprise.png": "company",
        }
        for filename, kind in expected.items():
            self.assertEqual(self.identites._identite_pour_chemin(filename), (kind, None))

    def test_civilities_no_longer_collapse_all_organizations_to_one_icon(self):
        self.assertIn('(6, u"Collectivité", None, "Collectivite.png", None)', self.civilites_text)
        self.assertIn('(7, u"Association", None,  "Association.png", None)', self.civilites_text)
        self.assertIn('(8, u"Organisme", None, "Organisme.png", None)', self.civilites_text)
        self.assertIn('(9, u"Entreprise", None, "Entreprise.png", None)', self.civilites_text)

    def test_unknown_business_art_is_not_reinterpreted(self):
        self.assertIsNone(self.identites._identite_pour_chemin("LogoClubTresSpecifique.png"))

    def test_supported_sizes_include_dense_and_hidpi_variants(self):
        for size in (16, 20, 24, 32, 40, 48):
            path = "Images/{0}x{0}/Ecole.png".format(size)
            self.assertEqual(self.identites._taille_pour_chemin(path), size)


if __name__ == "__main__":
    unittest.main()
