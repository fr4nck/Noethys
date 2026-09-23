# -*- coding: utf-8 -*-
"""Contrat de rendu : un modèle Convention (.ndc) utilisant les champs
HISTORIQUES Noedoc ({ORGANISATEUR_*}, {FAMILLE_*}) doit les voir résolus
dans le PDF généré, exactement comme pour les autres catégories de
documents (facture, devis, attestation...), en plus des champs propres
à la catégorie Convention ({CONVENTION_*}).

Avant correction : ModeleDoc.GetValeur() ne résout que les clés
réellement présentes dans le dict qu'on lui fournit -- toute clé absente
est silencieusement effacée du texte (DLG_Noedoc.ModeleDoc.GetValeur,
"texte = re.sub(r'\\{[A-Za-z0-9_-]*?\\}', '', texte)"). Comme
UTILS_Convention_champs.GetChampsConvention() ne construisait que des
{CONVENTION_*} et que UTILS_Impression_convention.GenererPDF() ne
fusionnait jamais modeleDoc.dictOrganisateur avec ce dict, un modèle
utilisant {ORGANISATEUR_NOM} ou {FAMILLE_NOM} voyait ces champs
disparaître du PDF généré, alors même qu'ils sont proposés par
DLG_Noedoc.Convention.champs et bien réels dans Noethys.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
NOETHYS_DIR = TESTS_DIR.parent / "noethys"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import wx  # noqa: E402

_APP = wx.App(False)

from _fixtures_noethys_db import (  # noqa: E402
    RedirectionGestionDB,
    creer_base_association_simple,
    creer_base_ecole_simple,
    inserer_modele_document,
)
from Dlg import DLG_Noedoc  # noqa: E402
from Utils import UTILS_Convention_champs as CC  # noqa: E402
from Utils import UTILS_Impression_convention as UIC  # noqa: E402
from reportlab.platypus import KeepTogether  # noqa: E402


def _AplatitStory(story):
    """ UIC._ConstruitStory regroupe le dernier objet flottant dans un
    KeepTogether : cet utilitaire de test retrouve la liste à plat des
    Paragraph, quel que soit ce groupement. """
    liste = []
    for item in story:
        if isinstance(item, KeepTogether):
            liste.extend(item._content)
        else:
            liste.append(item)
    return liste


CHAMPS_A_VERIFIER = (
    "{ORGANISATEUR_NOM}",
    "{FAMILLE_NOM}",
    "{FAMILLE_RUE}",
    "{FAMILLE_CP}",
    "{FAMILLE_VILLE}",
    "{CONVENTION_REPRESENTANT_NOM_COMPLET}",
    "{CONVENTION_SAISON}",
    "{CONVENTION_PLANNING_DETAIL}",
    "{CONVENTION_TARIF_HORAIRE}",
)


def _normaliser(texte):
    """ Les paragraphes ReportLab convertissent un "\\n" en "<br/>" et
    coupent le texte source sur "\\n\\n" (limite de paragraphe, perdue à
    la reconstitution) : pour vérifier qu'une valeur est bien présente
    dans le rendu, indépendamment de ces sauts de ligne/paragraphes, on
    compare un texte où tout saut de ligne (source ou "<br/>") est
    ramené à un simple espace. """
    texte = re.sub(r"(<br/>|\r?\n)+", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def _inserer_modele_champs_historiques(base):
    """ Modèle fictif dont le corps utilise réellement les champs
    historiques Noedoc en plus des champs Convention -- aucun texte
    d'article, aucune identité PMSL/Atout Sports/La Providence. """
    corps = "\n".join("%s : %s" % (champ, champ) for champ in CHAMPS_A_VERIFIER)
    objets = [
        {"nom": "Cadre principal", "categorie": "special", "champ": "cadre_principal",
         "ordre": 0, "x": 13, "y": 20, "largeur": 182, "hauteur": 250},
        {"nom": "Corps", "categorie": "bloc_texte", "ordre": 1,
         "x": 13, "y": 20, "largeur": 182, "texte": corps},
    ]
    return inserer_modele_document(base, "Modele champs historiques (test)", "convention", objets)


class ChampsHistoriquesResolusDansLeRenduTests(unittest.TestCase):
    def test_famille_organisateur_et_convention_sont_tous_resolus_dans_le_texte(self):
        # Base école (et non association) : elle a un taux horaire UNIQUE
        # (20€/h, déjà vérifié par ailleurs), donc {CONVENTION_TARIF_HORAIRE}
        # y est réellement déterminable -- la base association a deux taux
        # différents (adulte/enfant), qui remplissent
        # {CONVENTION_TARIF_ADULTE}/{CONVENTION_TARIF_ENFANT} mais laissent
        # volontairement {CONVENTION_TARIF_HORAIRE} vide (ambigu).
        with creer_base_ecole_simple() as base:
            # Adresse réellement déterminable pour la famille (le titulaire
            # de la fixture n'a pas d'adresse par défaut) : sans ça,
            # {FAMILLE_RUE}/{FAMILLE_CP}/{FAMILLE_VILLE} seraient vides
            # légitimement, ce qui ne prouverait rien sur le câblage.
            base.db.ExecuterReq(
                "UPDATE individus SET rue_resid='1 rue des Tests', cp_resid='00000', "
                "ville_resid='Testville' WHERE IDindividu=10;"
            )
            base.db.Commit()

            IDmodele = _inserer_modele_champs_historiques(base)

            with RedirectionGestionDB(base.chemin):
                # 1) Contrat précis : les valeurs calculées sont bien
                # substituées dans le texte du "story" (avant tout rendu
                # ReportLab), pour chacun des champs demandés.
                champs, _donnees = CC.GetChampsConvention(
                    IDfamille=2, date_debut="2026-08-01", date_fin="2027-07-31",
                    saison="2026-2027", listeIDindividus=[20, 21, 22],
                )
                modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
                dictRendu = dict(modeleDoc.dictOrganisateur)
                dictRendu.update(champs)
                cadre, objetsFlottants = UIC._SepareObjetsFixesEtFlottants(modeleDoc)
                story = UIC._ConstruitStory(modeleDoc, objetsFlottants, dictRendu)
                texte_rendu = _normaliser("\n".join(p.text for p in _AplatitStory(story)))

                for champ in CHAMPS_A_VERIFIER:
                    valeur = dictRendu.get(champ)
                    self.assertTrue(
                        valeur not in (None, u""),
                        "%s devrait être déterminable sur cette base de test" % champ,
                    )
                    self.assertIn(
                        _normaliser(str(valeur)), texte_rendu,
                        "%s=%r absent du texte rendu : le champ a été effacé au lieu d'être substitué" % (champ, valeur),
                    )
                    self.assertNotIn(
                        champ, texte_rendu,
                        "%s apparaît encore tel quel (non substitué) dans le texte rendu" % champ,
                    )

                # 2) Bout en bout : le pipeline public produit toujours un
                # PDF valide avec ces mêmes champs.
                chemin_pdf = tempfile.mktemp(suffix=".pdf")
                try:
                    resultat = UIC.Impression(
                        IDfamille=2, IDmodele=IDmodele, date_debut="2026-08-01", date_fin="2027-07-31",
                        saison="2026-2027", listeIDindividus=[20, 21, 22], nomDoc=chemin_pdf, afficherDoc=False,
                    )
                    self.assertIsInstance(resultat, dict, "génération échouée : %r" % (resultat,))
                    self.assertTrue(os.path.isfile(chemin_pdf))
                    self.assertGreater(os.path.getsize(chemin_pdf), 0)
                finally:
                    if os.path.isfile(chemin_pdf):
                        os.remove(chemin_pdf)

    def test_valeur_explicite_reste_prioritaire_sur_dictorganisateur(self):
        """ En cas de collision de clé entre dictOrganisateur et dictChamps
        (cas normalement improbable, {ORGANISATEUR_*} n'étant jamais
        produit par GetChampsConvention), dictChamps doit gagner -- vérifié
        directement sur GenererPDF plutôt que supposé. """
        with creer_base_association_simple() as base:
            IDmodele = inserer_modele_document(base, "Collision organisateur", "convention", [
                {"nom": "Cadre principal", "categorie": "special", "champ": "cadre_principal",
                 "ordre": 0, "x": 13, "y": 20, "largeur": 182, "hauteur": 250},
                {"nom": "Corps", "categorie": "bloc_texte", "ordre": 1,
                 "x": 13, "y": 20, "largeur": 182, "texte": "{ORGANISATEUR_NOM}"},
            ])
            with RedirectionGestionDB(base.chemin):
                modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
                self.assertIn("{ORGANISATEUR_NOM}", modeleDoc.dictOrganisateur)
                dictRendu = dict(modeleDoc.dictOrganisateur)
                dictRendu.update({"{ORGANISATEUR_NOM}": "VALEUR EXPLICITE DE TEST"})
                cadre, objetsFlottants = UIC._SepareObjetsFixesEtFlottants(modeleDoc)
                story = UIC._ConstruitStory(modeleDoc, objetsFlottants, dictRendu)
        texte_rendu = "\n".join(p.text for p in _AplatitStory(story))
        self.assertIn("VALEUR EXPLICITE DE TEST", texte_rendu)
        self.assertNotIn("Association Test Loisirs", texte_rendu)


if __name__ == "__main__":
    unittest.main()
