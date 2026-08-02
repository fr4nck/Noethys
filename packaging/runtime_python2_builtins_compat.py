"""Compatibilité minimale des builtins Python 2 encore appelés par Noethys.

Plusieurs modules historiques, notamment ObjectListView, utilisent encore
``basestring`` et ``long`` dans des chemins exécutés sous Python 3. Ce hook
restaure uniquement ces deux alias ; il ne modifie aucune donnée métier.
"""
from __future__ import annotations

import builtins

if not hasattr(builtins, "basestring"):
    builtins.basestring = str

if not hasattr(builtins, "long"):
    builtins.long = int
