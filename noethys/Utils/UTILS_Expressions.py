#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Évaluation sûre d'expressions simples utilisées par Noethys.

Ce module n'exécute jamais du code Python arbitraire. Il interprète un AST
limité aux littéraux et opérations explicitement autorisés.
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

_COMPARAISONS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda gauche, droite: gauche in droite,
    ast.NotIn: lambda gauche, droite: gauche not in droite,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
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
    return _EvaluerNoeudArithmetique(arbre.body)


def _EvaluerNoeudArithmetique(noeud):
    if isinstance(noeud, ast.Constant):
        if isinstance(noeud.value, bool) or not isinstance(noeud.value, (int, float)):
            raise ValueError("Littéral non numérique interdit")
        return noeud.value

    if isinstance(noeud, ast.Num):
        return noeud.n

    if isinstance(noeud, ast.BinOp) and type(noeud.op) in _OPERATEURS_BINAIRES:
        gauche = _EvaluerNoeudArithmetique(noeud.left)
        droite = _EvaluerNoeudArithmetique(noeud.right)
        return _OPERATEURS_BINAIRES[type(noeud.op)](gauche, droite)

    if isinstance(noeud, ast.UnaryOp) and type(noeud.op) in _OPERATEURS_UNAIRES:
        return _OPERATEURS_UNAIRES[type(noeud.op)](_EvaluerNoeudArithmetique(noeud.operand))

    raise ValueError("Expression non autorisée : %s" % type(noeud).__name__)


def EvaluerExpression(expression, variables=None, fonctions=None, methodes=None):
    """Évalue une expression booléenne/simple avec environnement explicite.

    ``variables`` contient les seuls noms accessibles. ``fonctions`` contient
    les seuls appels de fonctions autorisés et ``methodes`` les seuls noms de
    méthodes autorisés sur des objets. Les attributs privés (préfixés par
    ``_``) et toute construction non explicitement gérée sont refusés.
    """
    if not isinstance(expression, str):
        raise TypeError("L'expression doit être une chaîne")
    variables = dict(variables or {})
    fonctions = dict(fonctions or {})
    methodes = set(methodes or ())
    arbre = ast.parse(expression, mode="eval")
    return _EvaluerNoeudExpression(arbre.body, variables, fonctions, methodes)


def _EvaluerNoeudExpression(noeud, variables, fonctions, methodes):
    if isinstance(noeud, ast.Constant):
        return noeud.value

    if isinstance(noeud, (ast.Tuple, ast.List)):
        valeurs = [_EvaluerNoeudExpression(item, variables, fonctions, methodes) for item in noeud.elts]
        return tuple(valeurs) if isinstance(noeud, ast.Tuple) else valeurs

    if isinstance(noeud, ast.Name):
        if noeud.id not in variables:
            raise ValueError("Nom non autorisé : %s" % noeud.id)
        return variables[noeud.id]

    if isinstance(noeud, ast.Attribute):
        if noeud.attr.startswith("_"):
            raise ValueError("Attribut privé interdit")
        objet = _EvaluerNoeudExpression(noeud.value, variables, fonctions, methodes)
        return getattr(objet, noeud.attr)

    if isinstance(noeud, ast.BoolOp):
        if isinstance(noeud.op, ast.And):
            for valeur in noeud.values:
                resultat = _EvaluerNoeudExpression(valeur, variables, fonctions, methodes)
                if not resultat:
                    return resultat
            return resultat
        if isinstance(noeud.op, ast.Or):
            for valeur in noeud.values:
                resultat = _EvaluerNoeudExpression(valeur, variables, fonctions, methodes)
                if resultat:
                    return resultat
            return resultat
        raise ValueError("Opérateur booléen interdit")

    if isinstance(noeud, ast.UnaryOp) and isinstance(noeud.op, ast.Not):
        return not _EvaluerNoeudExpression(noeud.operand, variables, fonctions, methodes)

    if isinstance(noeud, ast.Compare):
        gauche = _EvaluerNoeudExpression(noeud.left, variables, fonctions, methodes)
        for operateur, comparateur in zip(noeud.ops, noeud.comparators):
            type_operateur = type(operateur)
            if type_operateur not in _COMPARAISONS:
                raise ValueError("Comparaison interdite")
            droite = _EvaluerNoeudExpression(comparateur, variables, fonctions, methodes)
            if not _COMPARAISONS[type_operateur](gauche, droite):
                return False
            gauche = droite
        return True

    if isinstance(noeud, ast.Call):
        if noeud.keywords:
            raise ValueError("Arguments nommés interdits")
        arguments = [_EvaluerNoeudExpression(arg, variables, fonctions, methodes) for arg in noeud.args]
        if isinstance(noeud.func, ast.Name):
            if noeud.func.id not in fonctions:
                raise ValueError("Fonction non autorisée : %s" % noeud.func.id)
            return fonctions[noeud.func.id](*arguments)
        if isinstance(noeud.func, ast.Attribute):
            if noeud.func.attr not in methodes or noeud.func.attr.startswith("_"):
                raise ValueError("Méthode non autorisée : %s" % noeud.func.attr)
            objet = _EvaluerNoeudExpression(noeud.func.value, variables, fonctions, methodes)
            return getattr(objet, noeud.func.attr)(*arguments)
        raise ValueError("Appel interdit")

    raise ValueError("Expression non autorisée : %s" % type(noeud).__name__)
