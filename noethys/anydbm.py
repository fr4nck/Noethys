"""Compatibilité Python 3 pour l'ancien module ``anydbm``.

Python 2 exposait ``anydbm`` ; Python 3 l'a remplacé par ``dbm``. Noethys
importe encore ce nom historique dans certains chemins de démarrage.
"""
from dbm import *  # noqa: F401,F403
