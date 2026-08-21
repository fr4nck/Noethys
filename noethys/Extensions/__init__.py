# -*- coding: utf-8 -*-

"""Infrastructure légère pour les extensions de Noethys Desktop.

Le chargement automatique de code tiers n'est volontairement pas activé ici.
Les extensions doivent être enregistrées explicitement afin de préserver la
stabilité, la sécurité et la compatibilité historique de l'application.
"""

from .registry import Extension, ExtensionRegistry, get_registry

__all__ = ["Extension", "ExtensionRegistry", "get_registry"]
