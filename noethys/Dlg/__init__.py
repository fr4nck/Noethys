# -*- coding: utf-8 -*-
"""Chargements spécialisés de quelques dialogues lourds.

Le paquet reste vide pour les imports ordinaires. Seule la liste des
consommations utilise un attribut de module différé afin de conserver tous les
imports historiques sans imposer son gros moteur PDF au démarrage de Noethys.
"""

import importlib


def __getattr__(name):
    if name == "DLG_Impression_conso":
        module = importlib.import_module(".DLG_Impression_conso_differe", __name__)
        globals()[name] = module
        return module
    raise AttributeError(name)
