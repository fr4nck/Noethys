"""Compatibilité minimale des builtins Python 2 encore appelés par Noethys.

Le code historique contient encore quelques références directes à des noms
supprimés en Python 3. Ce hook restaure uniquement les équivalents sûrs et
sans état ; il ne modifie aucune donnée métier.
"""
from __future__ import annotations

import builtins

if not hasattr(builtins, "basestring"):
    builtins.basestring = str

if not hasattr(builtins, "long"):
    builtins.long = int

if not hasattr(builtins, "unicode"):
    builtins.unicode = str

if not hasattr(builtins, "unichr"):
    builtins.unichr = chr

if not hasattr(builtins, "xrange"):
    builtins.xrange = range

if not hasattr(builtins, "cmp"):
    def _cmp(a, b):
        try:
            return (a > b) - (a < b)
        except TypeError:
            a_text = str(a)
            b_text = str(b)
            return (a_text > b_text) - (a_text < b_text)

    builtins.cmp = _cmp
