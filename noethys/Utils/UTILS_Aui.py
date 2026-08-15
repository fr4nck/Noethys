# -*- coding: utf-8 -*-
"""Helpers de compatibilité pour les perspectives wxAUI.

Les perspectives sont persistées dans Config.json et peuvent provenir d'une
ancienne version de wxPython. Une chaîne devenue invalide ne doit pas empêcher
Noethys de démarrer : on tente la perspective demandée puis, si nécessaire, la
perspective par défaut fournie par l'appelant.
"""


def ChargerPerspective(manager, perspective, fallback=None):
    """Charge une perspective AUI avec repli sûr sur ``fallback``.

    Retourne le résultat de ``LoadPerspective``. Les erreurs de parsing ou
    assertions liées à une ancienne perspective sont considérées comme un
    échec de chargement, sans masquer les autres exceptions inattendues.
    """
    candidates = []
    for candidate in (perspective, fallback):
        if isinstance(candidate, str) and candidate.strip() and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        try:
            result = manager.LoadPerspective(candidate)
        except (AssertionError, TypeError, ValueError, RuntimeError):
            result = False
        if result is not False:
            return result

    return False
