#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique les gardes de lignes DB confirmées par la passe globale anti-bugs.

Les transformations sont volontairement exactes et idempotentes. Elles ne
modifient ni le schéma ni la sémantique SQL : elles empêchent seulement les
IndexError/UnboundLocalError quand une ligne attendue a disparu ou n'existe
pas encore, avec des replis neutres adaptés au contexte.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"


def replace_once(relative: str, old: str, new: str) -> bool:
    path = NOETHYS / relative
    source = path.read_text(encoding="utf-8")
    if new in source:
        return False
    if old not in source:
        raise RuntimeError(f"Motif de hardening introuvable : {relative}")
    updated = source.replace(old, new, 1)
    ast.parse(updated, filename=str(path))
    path.write_text(updated, encoding="utf-8")
    return True


def apply_guards() -> list[str]:
    changed = []
    replacements = [
        (
            "Ctrl/CTRL_Informations.py",
            '''            self.DB.ExecuterReq(req)\n            IDcaisse, num_allocataire, allocataire, titulaire_helios, code_comptable = self.DB.ResultatReq()[0]\n            dictDonneesFamille = {"IDcaisse":IDcaisse, "num_allocataire":num_allocataire, "allocataire":allocataire, "titulaire_helios":titulaire_helios, "code_comptable":code_comptable}\n''',
            '''            self.DB.ExecuterReq(req)\n            donneesFamille = self.DB.ResultatReq()\n            if donneesFamille:\n                IDcaisse, num_allocataire, allocataire, titulaire_helios, code_comptable = donneesFamille[0]\n            else:\n                IDcaisse = num_allocataire = allocataire = titulaire_helios = code_comptable = None\n            dictDonneesFamille = {"IDcaisse":IDcaisse, "num_allocataire":num_allocataire, "allocataire":allocataire, "titulaire_helios":titulaire_helios, "code_comptable":code_comptable}\n''',
        ),
        (
            "Dlg/DLG_Noedoc.py",
            '''    DB.ExecuterReq(req)\n    buffer = DB.ResultatReq()[0][0]\n    DB.Close()\n    if buffer == None : \n''',
            '''    DB.ExecuterReq(req)\n    donneesLogo = DB.ResultatReq()\n    DB.Close()\n    buffer = donneesLogo[0][0] if donneesLogo else None\n    if buffer == None : \n''',
        ),
        (
            "Ol/OL_Inscriptions.py",
            '''        DB.ExecuterReq(req)\n        nom, logo = DB.ResultatReq()[0]\n        DB.Close()\n        if logo != None :\n''',
            '''        DB.ExecuterReq(req)\n        donneesOrganisateur = DB.ResultatReq()\n        DB.Close()\n        if donneesOrganisateur:\n            nom, logo = donneesOrganisateur[0]\n        else:\n            nom, logo = u"", None\n        if logo != None :\n''',
        ),
        (
            "Ctrl/CTRL_Detail_aides.py",
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        self.IDcompte_payeur = listeDonnees[0][0]\n''',
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        self.IDcompte_payeur = listeDonnees[0][0] if listeDonnees else 0\n''',
        ),
        (
            "Ctrl/CTRL_Repartition.py",
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        self.IDcompte_payeur = listeDonnees[0][0]\n\n        for label, largeur, _poids in self.SPECS_COLONNES:\n''',
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        self.IDcompte_payeur = listeDonnees[0][0] if listeDonnees else 0\n\n        for label, largeur, _poids in self.SPECS_COLONNES:\n''',
        ),
        (
            "Dlg/DLG_Famille_factures.py",
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        temp, email_factures = listeDonnees[0]\n        if email_factures == None :\n''',
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        if listeDonnees:\n            temp, email_factures = listeDonnees[0]\n        else:\n            temp, email_factures = None, None\n        if email_factures == None :\n''',
        ),
        (
            "Dlg/DLG_Famille_factures.py",
            '''            listeDonnees = DB.ResultatReq()\n            DB.Close()\n            self.IDcompte_payeur = listeDonnees[0][0]\n            self.ctrl_listview.SetIDcompte_payeur(self.IDcompte_payeur)\n''',
            '''            listeDonnees = DB.ResultatReq()\n            DB.Close()\n            self.IDcompte_payeur = listeDonnees[0][0] if listeDonnees else 0\n            self.ctrl_listview.SetIDcompte_payeur(self.IDcompte_payeur)\n''',
        ),
        (
            "Dlg/DLG_Saisie_prelevement_lot.py",
            '''        listeDonnees = DB.ResultatReq()      \n        DB.Close() \n        creancier_rue, creancier_cp, creancier_ville, creancier_siret = listeDonnees[0]\n''',
            '''        listeDonnees = DB.ResultatReq()      \n        DB.Close() \n        if listeDonnees:\n            creancier_rue, creancier_cp, creancier_ville, creancier_siret = listeDonnees[0]\n        else:\n            creancier_rue = creancier_cp = creancier_ville = creancier_siret = u""\n''',
        ),
        (
            "Dlg/DLG_Saisie_reglement.py",
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        IDfamille, email_recus = listeDonnees[0]\n        if email_recus != None and self.nouveauReglement == True :\n''',
            '''        listeDonnees = DB.ResultatReq()\n        DB.Close()\n        if listeDonnees:\n            IDfamille, email_recus = listeDonnees[0]\n        else:\n            IDfamille, email_recus = None, None\n        if email_recus != None and self.nouveauReglement == True :\n''',
        ),
        (
            "Utils/UTILS_Locations.py",
            '''    DBT.ExecuterReq(req)\n    listeDonnees = DBT.ResultatReq()\n    stock_initial = listeDonnees[0][1]\n    if stock_initial == None :\n''',
            '''    DBT.ExecuterReq(req)\n    listeDonnees = DBT.ResultatReq()\n    if not listeDonnees:\n        if DB == None:\n            DBT.Close()\n        return {}\n    stock_initial = listeDonnees[0][1]\n    if stock_initial == None :\n''',
        ),
        (
            "Utils/UTILS_Organisateur.py",
            '''    listeDonnees = DB.ResultatReq()\n    DB.Close()\n    nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape, logo, logo_update = listeDonnees[0]\n''',
            '''    listeDonnees = DB.ResultatReq()\n    DB.Close()\n    if listeDonnees:\n        nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape, logo, logo_update = listeDonnees[0]\n    else:\n        nom = rue = cp = ville = tel = fax = mail = site = num_agrement = num_siret = code_ape = u""\n        logo, logo_update = None, None\n''',
        ),
        (
            "Utils/UTILS_Stats_individus.py",
            '''    # Récupère les distances entre les villes\n    dictDistances = {}\n    try :\n''',
            '''    # Récupère les distances entre les villes\n    dictDistances = {}\n    origine = None\n    try :\n''',
        ),
        (
            "Utils/UTILS_Stats_individus.py",
            '''    for key, valeurs in dictVilles.items() :\n        if key in dictDistances and key != origine :\n''',
            '''    for key, valeurs in dictVilles.items() :\n        if origine is not None and key in dictDistances and key != origine :\n''',
        ),
    ]
    for relative, old, new in replacements:
        if replace_once(relative, old, new):
            changed.append(relative)
    return changed


def main() -> int:
    changed = apply_guards()
    if changed:
        print("Gardes DB/runtime appliquées :")
        for path in sorted(set(changed)):
            print(f"- {path}")
    else:
        print("Gardes DB/runtime déjà appliquées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
