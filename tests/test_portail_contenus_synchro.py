#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Utils import UTILS_Portail_contenus
from Utils import UTILS_Portail_contenus_synchro


class FakeDB(object):
    def __init__(self, lignes):
        self.lignes = list(lignes)
        self.maj = []

    def ExecuterReq(self, req):
        return True

    def ResultatReq(self):
        return self.lignes

    def ReqMAJ(self, table, donnees, cle, valeur, commit=False):
        self.maj.append((table, donnees, cle, valeur, commit))
        return True


class FakeLog(object):
    def __init__(self):
        self.messages = []

    def EcritLog(self, message):
        self.messages.append(message)


def config_rss():
    return UTILS_Portail_contenus.serialiser_parametres({
        "type": "rss",
        "url": "https://example.org/feed",
    })


def config_iframe():
    return UTILS_Portail_contenus.serialiser_parametres({
        "type": "iframe",
        "url": "https://example.org/widget",
    })


def test_actualisation_ne_touche_que_les_blocs_dynamiques():
    db = FakeDB([
        (1, config_iframe(), "iframe ancien"),
        (2, config_rss(), "rss ancien"),
        (3, "ancien parametre", "texte libre"),
    ])

    etat = UTILS_Portail_contenus_synchro.actualiser(
        db,
        constructeur=lambda config: "rss nouveau",
    )

    assert etat == {"present": True, "modifies": 1, "erreurs": 0}
    assert len(db.maj) == 1
    assert db.maj[0][2:4] == ("IDelement", 2)
    assert db.maj[0][1] == [("texte_html", "rss nouveau")]
    assert db.maj[0][4] is False


def test_panne_flux_conserve_le_cache_existant_et_ne_bloque_pas():
    db = FakeDB([(9, config_rss(), "derniere version valide")])
    log = FakeLog()

    def panne(config):
        raise OSError("serveur indisponible")

    etat = UTILS_Portail_contenus_synchro.actualiser(db, log=log, constructeur=panne)

    assert etat == {"present": True, "modifies": 0, "erreurs": 1}
    assert db.maj == []
    assert log.messages
    assert "Dernière version conservée" in log.messages[0]


def test_flux_inchange_ne_declenche_pas_ecriture():
    db = FakeDB([(4, config_rss(), "identique")])
    etat = UTILS_Portail_contenus_synchro.actualiser(
        db,
        constructeur=lambda config: "identique",
    )
    assert etat == {"present": True, "modifies": 0, "erreurs": 0}
    assert db.maj == []
