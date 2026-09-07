# -*- coding: utf-8 -*-
"""Contrats UI de la recherche individus/familles de l'accueil."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ctrl" / "CTRL_Recherche_individus.py"


class RechercheAccueilUIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texte = FICHIER.read_text(encoding="utf-8")
        cls.arbre = ast.parse(cls.texte)

    def _methode(self, nom):
        for noeud in ast.walk(self.arbre):
            if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)) and noeud.name == nom:
                return ast.get_source_segment(self.texte, noeud)
        self.fail("Méthode introuvable : %s" % nom)

    def test_recherche_vide_affiche_directement_toutes_les_donnees_chargees(self):
        recherche = self._methode("Recherche")
        branche_vide = recherche.split("if not texte:", 1)[1].split("resultats =", 1)[0]
        self.assertIn("self.listView.SetObjects(self.listView.donnees)", branche_vide)
        self.assertIn("self.parent.AfficherResultats()", branche_vide)
        self.assertNotIn("AfficherEtatVide", branche_vide)
        self.assertNotIn(".MAJ(", branche_vide)

    def test_etape_intermediaire_voir_tout_est_supprimee(self):
        self.assertNotIn("ctrl_voir_tout", self.texte)
        self.assertNotIn("def AfficherTout", self.texte)

    def test_chargement_metier_et_limite_de_recherche_restent_inchanges(self):
        maj = self._methode("MAJ")
        recherche = self._methode("Recherche")
        self.assertIn("self.ctrl_listview.MAJ(forceActualisation=True)", maj)
        self.assertIn("self.ctrl_recherche.Recherche()", maj)
        self.assertIn("LIMITE_RESULTATS_ACCUEIL = 30", self.texte)
        self.assertIn("resultats[:LIMITE_RESULTATS_ACCUEIL]", recherche)
        self.assertNotIn("ctrl_listview.MAJ", recherche)

    def test_actions_existantes_restent_disponibles(self):
        for marqueur in (
            "Nouvelle famille",
            "Envoyer un email",
            "Envoyer un SMS",
            "Modifier",
            "Calendrier",
            "Fiche individuelle",
            "Aperçu avant impression",
            "Exporter au format Excel",
        ):
            self.assertIn(marqueur, self.texte)

    def test_liste_reste_responsive_et_sans_grille_agressive(self):
        self.assertNotIn("wx.LC_HRULES", self.texte)
        self.assertNotIn("wx.LC_VRULES", self.texte)
        self.assertIn("UTILS_ColonnesResponsive.Installer", self.texte)
        self.assertIn('UTILS_UIMetrics.action_target("compact")', self.texte)


if __name__ == "__main__":
    unittest.main()
