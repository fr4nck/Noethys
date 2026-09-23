# -*- coding: utf-8 -*-
"""Génère un PDF de recette visuelle avec le vrai moteur Noedoc Convention."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import wx
from tests._fixtures_noethys_db import creer_base_association_simple, RedirectionGestionDB
from Utils import UTILS_Export_documents
from Utils import UTILS_Impression_convention as UIC


def main():
    sortie = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "artifacts" / "convention-reference.pdf"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    modele = NOETHYS / "Static" / "ModelesConventionExemples" / "modele_convention_pmsl_associative.ndc"

    app = wx.App(False)
    try:
        with creer_base_association_simple() as base:
            with RedirectionGestionDB(base.chemin):
                IDmodele = UTILS_Export_documents.Importer(fichier=str(modele))
                champs = {
                    "{ORGANISATEUR_NOM}": "PÊLE-MÊLE SPORTS ET LOISIRS",
                    "{ORGANISATEUR_RUE}": "4 RUE DES DEUX GARES",
                    "{ORGANISATEUR_CP}": "35130",
                    "{ORGANISATEUR_VILLE}": "LA GUERCHE DE BRETAGNE",
                    "{ORGANISATEUR_TEL}": "02.99.96.35.74.",
                    "{ORGANISATEUR_MAIL}": "direction@pelemele.org",
                    "{FAMILLE_NOM}": "Atout Sports Moutiers",
                    "{FAMILLE_VILLE}": "MOUTIERS",
                    "{CONVENTION_ADRESSE_STRUCTURE}": "Mairie de Moutiers\n1, Place St Martin\n35130 MOUTIERS",
                    "{CONVENTION_REPRESENTANT_NOM_COMPLET}": "Mme LE GALL Chantal",
                    "{CONVENTION_REPRESENTANT_FONCTION}": "Président(e)",
                    "{CONVENTION_SAISON}": "2026/2027",
                    "{CONVENTION_DATE_DEBUT}": "02/09/2026",
                    "{CONVENTION_DATE_FIN}": "25/06/2027",
                    "{CONVENTION_PLANNING_CRENEAUX}": (
                        "- Lundi de 19h30 à 20h30 : Encadrements sportifs adultes\n"
                        "- Mercredi de 17h30 à 19h00 : Encadrements sportifs enfants\n"
                        "- Jeudi de 10h00 à 11h00 : Encadrements sportifs adultes"
                    ),
                    "{CONVENTION_TARIF_HORAIRE_AFFICHE}": "",
                    "{CONVENTION_TARIF_ADULTE_AFFICHE}": "36,50 €",
                    "{CONVENTION_TARIF_ENFANT_AFFICHE}": "24,00 €",
                    "{CONVENTION_DATE_SIGNATURE}": "23/09/2026",
                    "{CONVENTION_LIEU_SIGNATURE}": "La Guerche de Bretagne",
                }
                UIC.GenererPDF(IDmodele, champs, nomDoc=str(sortie), afficherDoc=False)
    finally:
        app.Destroy()

    print(str(sortie))


if __name__ == "__main__":
    main()
