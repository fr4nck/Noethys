#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smoke test non-GUI — vérifie que les modules utilitaires de base
de Noethys s'importent sans base de données ni affichage.

Seuls les modules sans dépendance wx/DB sont testés ici.
Les modules qui chaînent vers wx (UTILS_Fichiers, UTILS_Customize, etc.)
sont couverts par smoke_wx.py une fois wxPython installé.
"""
import sys
import os

# Reproduit la logique de Chemins.py : ajoute noethys/ au chemin
REP_NOETHYS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "noethys")
)
sys.path.insert(0, REP_NOETHYS)

# Chemins.py : gestion des chemins internes — pas de wx, pas de DB
import Chemins  # noqa: E402  (path setup above required)

# Modules purement Python, sans wx ni connexion DB
from Utils import UTILS_Divers   # noqa: E402  (copy only)
from Utils import UTILS_Decimal  # noqa: E402  (decimal only)

# Vérification fonctionnelle minimale
result = UTILS_Decimal.FloatToDecimal(3.14)
assert str(result) == "3.14", "FloatToDecimal inattendu : %s" % result

print("smoke_noethys OK")
