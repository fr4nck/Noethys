#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Évaluation sûre d'expressions simples utilisées par Noethys.

Ce module n'exécute jamais du code Python arbitraire. Il interprète un AST
limité aux littéraux numériques et aux opérateurs arithmétiques explicitement
autorisés.
"""

import ast
import operator


_OPERATEURS_BINAIRES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_OPERATEURS_UNAIRES = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def EvaluerArithmetique(expression):
    """Évalue une expression arithmétique sans utiliser ``eval``.

    Sont acceptés : nombres, parenthèses, +, -, *, /, //, %, ** et signes
    unaires. Tout nom, attribut, appel de fonction, indexation ou autre nœud
    Python est rejeté avec ``ValueError``.
    """
    if not isinstance(expression, str):
        raise TypeError("L'expression doit être une chaîne")

    arbre = ast.parse(expression, mode="eval")
    return _EvaluerNoeud(arbre.body)


def _EvaluerNoeud(noeud):
    if isinstance(noeud, ast.Constant):
        if isinstance(noeud.value, bool) or not isinstance(noeud.value, (int, float)):
            raise ValueError("Littéral non numérique interdit")
        return noeud.value

    # Compatibilité avec les AST des anciennes versions de Python.
    if isinstance(noeud, ast.Num):
        return noeud.n

    if isinstance(noeud, ast.BinOp) and type(noeud.op) in _OPERATEURS_BINAIRES:
        gauche = _EvaluerNoeud(noeud.left)
        droite = _EvaluerNoeud(noeud.right)
        return _OPERATEURS_BINAIRES[type(noeud.op)](gauche, droite)

    if isinstance(noeud, ast.UnaryOp) and type(noeud.op) in _OPERATEURS_UNAIRES:
        return _OPERATEURS_UNAIRES[type(noeud.op)](_EvaluerNoeud(noeud.operand))

    raise ValueError("Expression non autorisée : %s" % type(noeud).__name__)
