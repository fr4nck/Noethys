# -*- coding: utf-8 -*-
"""Chargements spécialisés de quelques dialogues lourds ou historiques.

Le paquet reste paresseux pour les imports ordinaires. Les adaptateurs ci-dessous
préservent les imports historiques tout en remplaçant uniquement le shell des
fenêtres qui nécessitent une stabilisation Windows.
"""

import importlib


_ADAPTATEURS = {
    "DLG_Impression_conso": ".DLG_Impression_conso_differe",
    "DLG_Preferences": ".DLG_Preferences_stable",
}


def __getattr__(name):
    module_name = _ADAPTATEURS.get(name)
    if module_name is not None:
        module = importlib.import_module(module_name, __name__)
        globals()[name] = module
        return module
    raise AttributeError(name)
