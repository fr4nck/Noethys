"""Compatibilité SQLite pour le code historique Noethys sous Python 3.

Le code applicatif transmet encore parfois un chemin encodé en ``bytes`` à
``sqlite3.connect``. Sous les runtimes Python modernes, le chemin Windows doit
rester une chaîne Unicode. Ce hook ne modifie ni les données ni le schéma : il
normalise uniquement l'argument de connexion avant l'ouverture du fichier.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any

_original_connect = sqlite3.connect


def _connect_compat(database: Any, *args: Any, **kwargs: Any):
    if isinstance(database, bytes):
        database = os.fsdecode(database)
    return _original_connect(database, *args, **kwargs)


sqlite3.connect = _connect_compat
