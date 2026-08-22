# -*- coding: utf-8 -*-
"""Chargements spécialisés de quelques dialogues lourds ou historiques.

Le paquet reste paresseux pour les imports ordinaires. Seuls les dialogues qui
ont réellement besoin d'un chargement spécialisé sont routés ici. Les
corrections de layout wxPython doivent rester dans leur module métier d'origine,
pas dans un shell de substitution.
"""

import importlib


_ADAPTATEURS = {
    "DLG_Impression_conso": ".DLG_Impression_conso_differe",
}


def __getattr__(name):
    module_name = _ADAPTATEURS.get(name)
    if module_name is not None:
        module = importlib.import_module(module_name, __name__)
        globals()[name] = module
        return module
    raise AttributeError(name)
