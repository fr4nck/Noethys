# -*- coding: utf-8 -*-
"""Chargements spécialisés de quelques dialogues lourds ou historiques.

Le paquet reste paresseux pour les imports ordinaires. Seuls les dialogues qui
ont réellement besoin d'un chargement spécialisé sont routés ici. Les
corrections de layout wxPython doivent rester dans leur module métier d'origine,
pas dans un shell de substitution.
"""


_ADAPTATEURS = {
    "DLG_Impression_conso": ".DLG_Impression_conso_differe",
}


def __getattr__(name):
    if name == "DLG_Impression_conso":
        # Import statique placé dans le getter : le chargement reste paresseux,
        # mais PyInstaller voit explicitement le module à embarquer.
        import Dlg.DLG_Impression_conso_differe as module

        globals()[name] = module
        return module
    raise AttributeError(name)
