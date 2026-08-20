#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVEUR = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_serveur.py"
SYNC_HELPER = ROOT / "noethys" / "Utils" / "UTILS_Portail_contenus_synchro.py"


def test_serveur_actualise_les_contenus_avant_la_synchro_historique():
    serveur = SERVEUR.read_text(encoding="utf-8")
    helper = SYNC_HELPER.read_text(encoding="utf-8")

    assert "from Utils import UTILS_Portail_contenus_synchro" in serveur
    appel_preparation = serveur.index("UTILS_Portail_contenus_synchro.preparer_avant_synchro")
    appel_synchro = serveur.index("synchro.Synchro_totale()")
    assert appel_preparation < appel_synchro

    assert 'nom="last_update_pages"' in helper
    assert "DB.Commit()" in helper
    assert "Dernière version conservée" in helper
    assert "WHERE parametres IS NOT NULL" in helper
