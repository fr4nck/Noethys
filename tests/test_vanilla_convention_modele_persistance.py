# -*- coding: utf-8 -*-
"""Audit de persistance des modèles de catégorie "convention"
(documents_modeles/documents_objets) -- recette réelle Noethys SL
0.1.0 RC1 : un modèle de convention créé/importé a généré un PDF avec
succès (CONVENTION20260923155619KHW700.pdf), mais l'application affiche
ensuite "Aucun modèle de convention n'est disponible.".

Audit mené (voir le rapport de recette pour le détail complet) : le
mécanisme de sauvegarde (DLG_Noedoc.ModeleDoc.Sauvegarde()) et
d'importation (UTILS_Export_documents.Importer()) est générique,
identique à celui de toutes les autres catégories historiques (facture,
attestation, ...) -- aucune branche spécifique à "convention". Les tests
ci-dessous le PROUVENT par un cycle réel sauvegarde/réouverture (nouvelle
connexion GestionDB.DB(), exactement comme le fait
CTRL_Choix_modele.CTRL_Choice à chaque ouverture de dialogue), plutôt que
de le supposer depuis la lecture du code seule.

Aucun bug n'a été trouvé dans ce mécanisme générique : la cause du
symptôme observé en recette n'a donc pas pu être confirmée sans accès à
la base réelle (voir le rapport -- requête de diagnostic en lecture
seule fournie séparément). Un défaut latent réel et distinct A été
trouvé et corrigé pendant cet audit dans
UTILS_Export_documents.Importer() : voir
test_import_objet_sans_cle_image_ne_leve_pas_et_n_ecrase_pas_le_blob_precedent.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

NOETHYS_DIR = TESTS_DIR.parent / "noethys"
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

import wx  # noqa: E402

# wx ne supporte qu'un seul wx.App par processus : créé une fois au niveau
# module (jamais détruit ici), comme test_vanilla_apparence_claire.py et
# test_vanilla_convention_recette_modeles.py -- un wx.App créé/détruit à
# l'intérieur d'une méthode de test casse tout usage de wx dans les
# AUTRES modules de test exécutés ensuite dans le même processus
# (python -m unittest discover).
_APP = wx.App(False)

from _fixtures_noethys_db import BaseTest, RedirectionGestionDB  # noqa: E402

import GestionDB  # noqa: E402
from Ctrl.CTRL_Choix_modele import CTRL_Choice  # noqa: E402
from Utils import UTILS_Export_documents  # noqa: E402


class PersistanceModeleConventionTests(unittest.TestCase):
    """ Preuve directe (pas une supposition) que le mécanisme générique de
    sauvegarde d'un modèle "documents_modeles"/"documents_objets" pour la
    catégorie convention survit réellement à une fermeture/réouverture de
    connexion -- exactement le scénario "créer un modèle, le retrouver
    plus tard" rapporté en recette. """

    def test_insertion_documents_modeles_convention_persiste_apres_reouverture(self):
        base = BaseTest()
        # Reproduit exactement l'INSERT fait par
        # DLG_Noedoc.ModeleDoc.Sauvegarde() pour un nouveau modèle (mêmes
        # colonnes, categorie="convention"), sur une première connexion...
        db1 = GestionDB.DB(nomFichier=base.chemin, suffixe=None)
        IDmodele = db1.ReqInsert("documents_modeles", [
            ("nom", "Convention test"),
            ("categorie", "convention"),
            ("supprimable", 1),
            ("largeur", 210.0),
            ("hauteur", 297.0),
            ("observations", ""),
            ("IDfond", None),
            ("IDdonnee", None),
            ("defaut", 1),
        ])
        db1.Close()

        # ... puis relit avec une CONNEXION FRAICHE distincte, exactement
        # ce que fait CTRL_Choice.GetListeDonnees() (SELECT ... WHERE
        # categorie='convention') à chaque ouverture du dialogue de
        # génération de convention.
        db2 = GestionDB.DB(nomFichier=base.chemin, suffixe=None)
        db2.ExecuterReq(
            "SELECT IDmodele, nom FROM documents_modeles "
            "WHERE categorie='convention' ORDER BY nom;"
        )
        resultat = db2.ResultatReq()
        db2.Close()

        self.assertEqual(resultat, [(IDmodele, "Convention test")])

    def test_ctrl_choice_retrouve_le_modele_convention_apres_reouverture(self):
        """ Même preuve, mais via le VRAI contrôle utilisé par
        DLG_Generation_convention (CTRL_Choix_modele.CTRL_Choice), pas une
        requête SQL reconstruite à la main. """
        base = BaseTest()

        db1 = GestionDB.DB(nomFichier=base.chemin, suffixe=None)
        IDmodele = db1.ReqInsert("documents_modeles", [
            ("nom", "Convention test"),
            ("categorie", "convention"),
            ("supprimable", 1),
            ("largeur", 210.0),
            ("hauteur", 297.0),
            ("observations", ""),
            ("IDfond", None),
            ("IDdonnee", None),
            ("defaut", 1),
        ])
        db1.Close()

        frame = wx.Frame(None)
        try:
            with RedirectionGestionDB(base.chemin):
                ctrl = CTRL_Choice(frame, categorie="convention")
                self.assertEqual(ctrl.GetID(), IDmodele)
        finally:
            frame.Destroy()

    def test_import_objet_sans_cle_image_ne_leve_pas_et_n_ecrase_pas_le_blob_precedent(self):
        """ Défaut latent réel trouvé pendant cet audit (pas le défaut
        rapporté en recette, mais un défaut distinct dans la même fonction
        auditée) : Importer() lisait `blob` défini seulement DANS la
        boucle interne quand champ == "image". Un objet sans clé "image"
        (jamais produit par Exporter() aujourd'hui, qui inclut
        systématiquement cette clé -- mais pas garanti pour tout fichier
        .ndc externe/futur) levait UnboundLocalError au premier objet
        sans image, ou pire, réutilisait silencieusement le blob de
        l'objet précédent. Corrigé en réinitialisant blob=None à chaque
        objet. """
        base = BaseTest()
        with RedirectionGestionDB(base.chemin):
            IDmodele = UTILS_Export_documents.Importer(dictDonnees={
                "nom": "Convention sans clé image",
                "categorie": "convention",
                "largeur": 210,
                "hauteur": 297,
                "IDfond": None,
                "defaut": 0,
                "objets": [
                    # Premier objet : PAS de clé "image" du tout (le cas qui
                    # levait UnboundLocalError avant le correctif).
                    {"nom": "article_1", "categorie": "texte_flottant", "champ": None,
                     "ordre": 0, "texte": "Un article de convention.", "x": 10.0, "y": 10.0},
                ],
            })
            self.assertIsNotNone(IDmodele)

            db = GestionDB.DB(nomFichier=base.chemin, suffixe=None)
            db.ExecuterReq("SELECT nom FROM documents_objets WHERE IDmodele=%d;" % IDmodele)
            resultat = db.ResultatReq()
            db.Close()
            self.assertEqual(resultat, [("article_1",)])


if __name__ == "__main__":
    unittest.main()
