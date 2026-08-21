#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Utils import UTILS_Portail_tarifs_bloc as BLOC
from Utils import UTILS_Portail_tarifs_synchro as SYNCHRO


class FakeDB(object):
    def __init__(self, lignes):
        self.lignes = list(lignes)
        self.maj = []
        self.commits = 0
        self.closed = False

    def ExecuterReq(self, requete):
        return True

    def ResultatReq(self):
        return list(self.lignes)

    def ReqMAJ(self, table, donnees, cle, valeur, commit=False):
        self.maj.append((table, donnees, cle, valeur, commit))
        return True

    def Commit(self):
        self.commits += 1

    def Close(self):
        self.closed = True


class FakeLog(object):
    def __init__(self):
        self.messages = []

    def EcritLog(self, message):
        self.messages.append(message)


def config(mode="automatique", inclus=None, exclus=None, titre="Tarifs"):
    return BLOC.serialiser_configuration({
        "mode": mode,
        "IDsactivites": inclus or [],
        "IDsactivites_exclues": exclus or [],
        "titre": titre,
    })


class PortailTarifsBlocTests(unittest.TestCase):

    def test_configuration_auto_est_le_defaut_et_dedoublonne_les_ids(self):
        brut = BLOC.serialiser_configuration({
            "IDsactivites_exclues": [7, "7", 4, "invalide"],
        })
        relu = BLOC.deserialiser_configuration(brut)
        self.assertEqual(relu["mode"], "automatique")
        self.assertEqual(relu["IDsactivites"], [])
        self.assertEqual(relu["IDsactivites_exclues"], [4, 7])
        self.assertEqual(relu["titre"], BLOC.TITRE_DEFAUT)
        self.assertTrue(BLOC.est_configuration_bloc_tarifs(brut))
        self.assertFalse(BLOC.est_configuration_bloc_tarifs('{"source":"autre"}'))

    def test_politique_selection_est_restituee_sans_exclusions_cachees(self):
        politique = BLOC.politique_depuis_configuration({
            "mode": "selection",
            "IDsactivites": [9, 2],
            "IDsactivites_exclues": [5],
        })
        self.assertEqual(politique, {
            "mode": "selection",
            "IDsactivites": [2, 9],
            "IDsactivites_exclues": [5],
        })

    def test_exclusion_temporairement_invisible_survit_a_un_enregistrement(self):
        politique = BLOC.fusionner_choix_catalogue(
            {
                "mode": "automatique",
                "IDsactivites_exclues": [7, 12],
            },
            IDs_catalogue=[1, 7, 9],
            IDs_coches=[1, 9],
            mode="automatique",
        )
        # 7 est encore visible et décochée ; 12 n'a momentanément plus de
        # tarif courant/futur. Les deux exclusions doivent être conservées.
        self.assertEqual(politique, {
            "mode": "automatique",
            "IDsactivites": [],
            "IDsactivites_exclues": [7, 12],
        })

    def test_selection_temporairement_invisible_survit_a_un_enregistrement(self):
        politique = BLOC.fusionner_choix_catalogue(
            {
                "mode": "selection",
                "IDsactivites": [2, 15],
            },
            IDs_catalogue=[2, 4],
            IDs_coches=[2, 4],
            mode="selection",
        )
        self.assertEqual(politique, {
            "mode": "selection",
            "IDsactivites": [2, 4, 15],
            "IDsactivites_exclues": [],
        })

    def test_synchro_regenere_un_bloc_tarifs_et_ignore_les_autres(self):
        db = FakeDB([
            (1, '{"source":"autre"}', "ancien"),
            (2, config(exclus=[3]), "ancien tarif"),
        ])
        appels = []

        def constructeur(DB, politique, titre):
            appels.append((politique, titre))
            return "nouveau tarif"

        etat = SYNCHRO.actualiser(db, constructeur=constructeur)
        self.assertEqual(etat, {"present": True, "modifies": 1, "erreurs": 0})
        self.assertEqual(appels, [({
            "mode": "automatique",
            "IDsactivites": [],
            "IDsactivites_exclues": [3],
        }, "Tarifs")])
        self.assertEqual(len(db.maj), 1)
        self.assertEqual(db.maj[0][2:4], ("IDelement", 2))
        self.assertEqual(db.maj[0][1], [("texte_html", "nouveau tarif")])
        self.assertFalse(db.maj[0][4])

    def test_synchro_inchangee_ne_force_pas_export(self):
        db = FakeDB([(2, config(), "identique")])
        appels_parametres = []
        etat = SYNCHRO.preparer_avant_synchro(
            db_factory=lambda: db,
            parametre_setter=lambda **kwargs: appels_parametres.append(kwargs),
            constructeur=lambda DB, politique, titre: "identique",
        )
        self.assertEqual(etat, {"present": True, "modifies": 0, "erreurs": 0})
        self.assertEqual(db.commits, 0)
        self.assertEqual(appels_parametres, [])
        self.assertTrue(db.closed)

    def test_nouveau_rendu_commit_et_marque_les_pages_modifiees(self):
        db = FakeDB([(2, config(), "ancien")])
        appels_parametres = []
        instant = datetime.datetime(2026, 8, 21, 11, 30, 0)
        etat = SYNCHRO.preparer_avant_synchro(
            db_factory=lambda: db,
            parametre_setter=lambda **kwargs: appels_parametres.append(kwargs),
            constructeur=lambda DB, politique, titre: "nouveau",
            maintenant=instant,
        )
        self.assertEqual(etat, {"present": True, "modifies": 1, "erreurs": 0})
        self.assertEqual(db.commits, 1)
        self.assertTrue(db.closed)
        self.assertEqual(appels_parametres, [{
            "mode": "set",
            "categorie": "portail",
            "nom": "last_update_pages",
            "valeur": "2026-08-21 11:30:00",
        }])

    def test_erreur_de_generation_conserve_le_dernier_html(self):
        db = FakeDB([(2, config(), "dernier rendu valide")])
        log = FakeLog()

        def panne(DB, politique, titre):
            raise RuntimeError("base indisponible")

        etat = SYNCHRO.actualiser(db, log=log, constructeur=panne)
        self.assertEqual(etat, {"present": True, "modifies": 0, "erreurs": 1})
        self.assertEqual(db.maj, [])
        self.assertTrue(log.messages)
        self.assertIn("Dernière version conservée", log.messages[0])


if __name__ == "__main__":
    unittest.main()
