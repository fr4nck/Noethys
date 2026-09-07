#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def lire(chemin):
    return (ROOT / chemin).read_text(encoding="utf-8")


def source_fonction(chemin, nom_fonction, nom_classe=None):
    source = lire(chemin)
    arbre = ast.parse(source)
    noeuds = arbre.body
    if nom_classe is not None:
        classe = next(
            noeud for noeud in arbre.body
            if isinstance(noeud, ast.ClassDef) and noeud.name == nom_classe
        )
        noeuds = classe.body
    fonction = next(
        noeud for noeud in noeuds
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef))
        and noeud.name == nom_fonction
    )
    return ast.get_source_segment(source, fonction)


class RemplissageDialogDatesContractTests(unittest.TestCase):
    def test_les_deux_dialogues_passent_par_le_selecteur_de_periode_commun(self):
        parametres = lire("noethys/Dlg/DLG_Parametres_remplissage.py")
        attente = lire("noethys/Dlg/DLG_Attente.py")

        self.assertIn("CTRL_Grille_periode.CTRL(self)", parametres)
        self.assertIn("CTRL_Grille_periode.CTRL(self)", attente)

    def test_vacances_accepte_les_dates_natives_du_pilote_python3(self):
        maj = source_fonction(
            "noethys/Ctrl/CTRL_Grille_periode.py",
            "MAJ",
            nom_classe="Vacances",
        )

        self.assertIn("UTILS_Dates.DateEngEnDateDD(date_debut)", maj)
        self.assertIn("UTILS_Dates.DateEngEnDateDD(date_fin)", maj)
        self.assertNotIn("date_debut[:10]", maj)
        self.assertNotIn("date_fin[:10]", maj)

    def test_liste_attente_accepte_date_datetime_et_chaine_historique(self):
        conversion = source_fonction(
            "noethys/Ctrl/CTRL_Attente.py",
            "DateEngEnDateDD",
        )

        self.assertIn("isinstance(dateEng, datetime.datetime)", conversion)
        self.assertIn("return dateEng.date()", conversion)
        self.assertIn("return UTILS_Dates.DateEngEnDateDD(dateEng)", conversion)
        self.assertNotIn("dateEng[:10]", conversion)

    def test_boutons_repens_restent_branches_sur_les_actions_existantes(self):
        source = lire("noethys/Dlg/DLG_Remplissage_Repens.py")

        self.assertIn(
            "self.Bind(wx.EVT_TOOL, self.OnListeAttente, id=Legacy.ID_LISTE_ATTENTE)",
            source,
        )
        self.assertIn(
            "self.Bind(wx.EVT_TOOL, self.OnParametres, id=Legacy.ID_PARAMETRES)",
            source,
        )
        self.assertIn("self.GetParent().OuvrirListeAttente()", source)
        self.assertIn("DLG_Parametres_remplissage.Dialog(", source)

    def test_correctif_ne_change_pas_les_requetes_des_deux_parcours(self):
        grille = source_fonction(
            "noethys/Ctrl/CTRL_Grille_periode.py",
            "MAJ",
            nom_classe="Vacances",
        )
        attente = source_fonction(
            "noethys/Ctrl/CTRL_Attente.py",
            "Importation",
            nom_classe="CTRL",
        )

        self.assertIn("FROM vacances", grille)
        self.assertIn("WHERE annee=%d", grille)
        self.assertIn("FROM consommations", attente)
        self.assertIn("WHERE consommations.etat = '%s'", attente)


if __name__ == "__main__":
    unittest.main()
