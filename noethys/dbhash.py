"""Compatibilité Python 3 pour l'ancien module ``dbhash``.

Le module Python 2 ``dbhash`` reposait sur Berkeley DB. Python 3 ne le fournit
plus ; ce shim expose l'API minimale attendue par Noethys via ``dbm``.
"""
from dbm import open

__all__ = ["open"]
