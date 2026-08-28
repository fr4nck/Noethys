#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détecte les variables locales potentiellement non définies après un ``if``.

Le contrôle est volontairement conservateur : il signale une variable affectée
dans un branchement sans être garantie sur tous les chemins qui atteignent la
suite, lorsque son premier usage ultérieur est une lecture ou une suppression.
Les résultats restent des candidats à qualifier humainement. La couverture des
sources est bloquante.

La propagation des définitions suit les chemins qui peuvent réellement
continuer après un branchement. Une chaîne exhaustive ``if/elif/else`` qui
définit un nom dans toutes ses branches rend donc ce nom disponible ensuite,
y compris lorsque les ``elif`` sont représentés par des ``If`` imbriqués dans
``orelse`` par l'AST Python. Les cibles de compréhension restent dans leur
portée Python 3 et ne sont jamais prises pour des affectations locales de la
fonction englobante. Un ``del`` retire explicitement le nom de l'état garanti.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}


def iter_python_files(root=NOETHYS):
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def _visit_comprehension_runtime_order(visitor, node, value_nodes):
    """Visite une compréhension dans l'ordre de liaison utile à l'audit."""
    for generator in node.generators:
        visitor.visit(generator.iter)
        visitor.visit(generator.target)
        for condition in generator.ifs:
            visitor.visit(condition)
    for value_node in value_nodes:
        visitor.visit(value_node)


class NameEvents(ast.NodeVisitor):
    def __init__(self, name):
        self.name = name
        self.events = []

    def visit_Name(self, node):
        if node.id == self.name:
            if isinstance(node.ctx, ast.Load):
                mode = "load"
            elif isinstance(node.ctx, ast.Del):
                mode = "delete"
            else:
                mode = "store"
            self.events.append((node.lineno, mode))

    def visit_ListComp(self, node):
        _visit_comprehension_runtime_order(self, node, (node.elt,))

    def visit_SetComp(self, node):
        _visit_comprehension_runtime_order(self, node, (node.elt,))

    def visit_GeneratorExp(self, node):
        _visit_comprehension_runtime_order(self, node, (node.elt,))

    def visit_DictComp(self, node):
        _visit_comprehension_runtime_order(self, node, (node.key, node.value))

    def visit_FunctionDef(self, node):
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_Lambda(self, node):
        return

    def visit_ClassDef(self, node):
        return


def assigned_names(statements):
    names = set()

    class Stores(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                names.add(node.id)

        def _visit_comp(self, node, value_nodes):
            # Une cible ``for x in ...`` d'une compréhension ne définit pas
            # ``x`` dans la fonction englobante sous Python 3. On visite les
            # expressions mais jamais les cibles de générateur.
            for generator in node.generators:
                self.visit(generator.iter)
                for condition in generator.ifs:
                    self.visit(condition)
            for value_node in value_nodes:
                self.visit(value_node)

        def visit_ListComp(self, node):
            self._visit_comp(node, (node.elt,))

        def visit_SetComp(self, node):
            self._visit_comp(node, (node.elt,))

        def visit_GeneratorExp(self, node):
            self._visit_comp(node, (node.elt,))

        def visit_DictComp(self, node):
            self._visit_comp(node, (node.key, node.value))

        def visit_FunctionDef(self, node):
            return

        def visit_AsyncFunctionDef(self, node):
            return

        def visit_Lambda(self, node):
            return

        def visit_ClassDef(self, node):
            return

    visitor = Stores()
    for statement in statements:
        visitor.visit(statement)
    return names


def target_names(target):
    names = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    return names


def target_deleted_names(target):
    names = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Del):
            names.add(node.id)
    return names


def deleted_names(statement):
    if not isinstance(statement, ast.Delete):
        return set()
    result = set()
    for target in statement.targets:
        result.update(target_deleted_names(target))
    return result


def direct_definitions(statement):
    if isinstance(statement, ast.Assign):
        result = set()
        for target in statement.targets:
            result.update(target_names(target))
        return result
    if isinstance(statement, ast.AnnAssign):
        # ``x: Type`` n'assigne aucune valeur à ``x`` au runtime. Seule une
        # annotation accompagnée d'une valeur crée réellement la liaison.
        if statement.value is None:
            return set()
        return target_names(statement.target)
    if isinstance(statement, ast.AugAssign):
        # Si l'AugAssign atteint sa suite sans exception, sa cible est liée.
        return target_names(statement.target)
    if isinstance(statement, (ast.Import, ast.ImportFrom)):
        result = set()
        for alias in statement.names:
            result.add(alias.asname or alias.name.split(".")[0])
        return result
    return set()


def direct_definitions_in_sequence(statements):
    result = set()
    for statement in statements:
        result.update(direct_definitions(statement))
    return result


def block_terminates(statements):
    if not statements:
        return False
    last = statements[-1]
    if isinstance(last, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
        return True
    if isinstance(last, ast.If) and last.orelse:
        return block_terminates(last.body) and block_terminates(last.orelse)
    return False


def first_event(statements, name):
    visitor = NameEvents(name)
    for statement in statements:
        visitor.visit(statement)
    if not visitor.events:
        return None
    return min(enumerate(visitor.events), key=lambda item: (item[1][0], item[0]))[1]


def function_args(function):
    result = {arg.arg for arg in function.args.posonlyargs}
    result.update(arg.arg for arg in function.args.args)
    result.update(arg.arg for arg in function.args.kwonlyargs)
    if function.args.vararg:
        result.add(function.args.vararg.arg)
    if function.args.kwarg:
        result.add(function.args.kwarg.arg)
    return result


def _with_body_definitions(statement, predefined):
    """Définitions disponibles une fois tous les ``__enter__`` réussis."""
    defined = set(predefined)
    for item in statement.items:
        if item.optional_vars is not None:
            defined.update(target_names(item.optional_vars))
    return defined


def _with_continuing_definitions(statement, predefined):
    """Définitions garanties sur tous les chemins qui sortent du ``with``.

    ``with A() as a, B() as b`` équivaut à deux ``with`` imbriqués. Si l'entrée
    de ``B`` échoue et que ``A.__exit__`` supprime l'exception, l'exécution peut
    reprendre après le ``with`` avec ``a`` défini mais ``b`` absent. Seule la
    cible simple du premier manager est donc garantie pour un ``with`` multiple.

    Une cible déstructurée n'est pas propagée non plus : son unpacking peut
    échouer après ``__enter__`` puis être supprimé par ``__exit__``, laissant
    certaines liaisons absentes ou partielles.
    """
    defined = set(predefined)
    if statement.items:
        first = statement.items[0]
        if isinstance(first.optional_vars, ast.Name):
            defined.add(first.optional_vars.id)
    return defined


def guaranteed_definitions(statements, predefined):
    """Retourne les noms définis sur tous les chemins qui atteignent la suite.

    Les boucles ne propagent pas leurs affectations car leur corps peut ne jamais
    s'exécuter. Pour un ``if`` exhaustif, l'intersection des définitions des
    branches est garantie. Lorsqu'une branche termine le flot, seule la branche
    qui continue contribue. Un ``with`` générique ne propage pas les
    affectations de son corps, puisqu'un context manager peut supprimer une
    exception ; pour plusieurs managers, seule la cible simple ``as`` du premier
    est garantie après sortie. Un ``del`` retire immédiatement sa cible de
    l'ensemble défini.
    """
    defined = set(predefined)
    for statement in statements:
        if isinstance(statement, ast.Delete):
            defined.difference_update(deleted_names(statement))

        elif isinstance(statement, ast.If):
            body_defined = guaranteed_definitions(statement.body, defined)
            body_terminates = block_terminates(statement.body)

            if statement.orelse:
                else_defined = guaranteed_definitions(statement.orelse, defined)
                else_terminates = block_terminates(statement.orelse)
                if body_terminates and not else_terminates:
                    defined = else_defined
                elif else_terminates and not body_terminates:
                    defined = body_defined
                elif not body_terminates and not else_terminates:
                    defined = body_defined & else_defined
                else:
                    return defined

        elif isinstance(statement, ast.Try):
            body_defined = guaranteed_definitions(statement.body, defined)
            handler_states = [guaranteed_definitions(handler.body, defined) for handler in statement.handlers]
            handler_terminations = [block_terminates(handler.body) for handler in statement.handlers]

            continuing_states = []
            if not block_terminates(statement.body):
                if statement.orelse:
                    continuing_states.append(guaranteed_definitions(statement.orelse, body_defined))
                else:
                    continuing_states.append(body_defined)
            for state, terminates in zip(handler_states, handler_terminations):
                if not terminates:
                    continuing_states.append(state)

            if continuing_states:
                merged = set(continuing_states[0])
                for state in continuing_states[1:]:
                    merged.intersection_update(state)
                defined = merged

            if statement.finalbody:
                defined = guaranteed_definitions(statement.finalbody, defined)

        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            defined = _with_continuing_definitions(statement, defined)

        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            pass

        else:
            defined.update(direct_definitions(statement))

    return defined


def scan_sequence(statements, predefined, relpath, function_name, findings):
    defined = set(predefined)
    for index, statement in enumerate(statements):
        if isinstance(statement, ast.If):
            body_assigned = assigned_names(statement.body)
            else_assigned = assigned_names(statement.orelse)
            assigned_here = body_assigned | else_assigned
            following = statements[index + 1 :]

            # Ne pas raisonner seulement sur ``body - else`` : le même nom peut
            # apparaître dans les deux branches tout en restant non garanti dans
            # chacune (affectations imbriquées conditionnelles). La preuve utile
            # est l'état réellement garanti après le ``if`` sur tous les chemins
            # qui continuent.
            guaranteed_after_if = guaranteed_definitions([statement], defined)
            whole_if_terminates = block_terminates([statement])

            for name in sorted(assigned_here):
                if name in defined or name in guaranteed_after_if or whole_if_terminates:
                    continue

                in_body = name in body_assigned
                in_else = name in else_assigned
                if in_body and in_else:
                    detail = "partial_branches"
                elif in_body:
                    detail = "body_only"
                else:
                    detail = "else_only"

                event = first_event(following, name)
                if event and event[1] in {"load", "delete"}:
                    findings.append({
                        "kind": "branch_assignment_gap",
                        "priority": "high",
                        "file": relpath,
                        "function": function_name,
                        "if_line": statement.lineno,
                        "line": event[0],
                        "name": name,
                        "detail": detail,
                    })

            scan_sequence(statement.body, defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)

            body_defined = guaranteed_definitions(statement.body, defined)
            body_terminates = block_terminates(statement.body)
            if statement.orelse:
                else_defined = guaranteed_definitions(statement.orelse, defined)
                else_terminates = block_terminates(statement.orelse)
                if body_terminates and not else_terminates:
                    defined = else_defined
                elif else_terminates and not body_terminates:
                    defined = body_defined
                elif not body_terminates and not else_terminates:
                    defined = body_defined & else_defined

        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            loop_defined = defined | target_names(statement.target)
            scan_sequence(statement.body, loop_defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)

        elif isinstance(statement, ast.While):
            scan_sequence(statement.body, defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)

        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            body_defined = _with_body_definitions(statement, defined)
            scan_sequence(statement.body, body_defined, relpath, function_name, findings)
            defined = _with_continuing_definitions(statement, defined)

        elif isinstance(statement, ast.Try):
            scan_sequence(statement.body, defined, relpath, function_name, findings)
            for handler in statement.handlers:
                handler_defined = set(defined)
                if handler.name:
                    handler_defined.add(handler.name)
                scan_sequence(handler.body, handler_defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)
            scan_sequence(statement.finalbody, defined, relpath, function_name, findings)

            defined = guaranteed_definitions([statement], defined)

        defined.difference_update(deleted_names(statement))
        defined.update(direct_definitions(statement))


def _scan_loaded(tree, path, root=NOETHYS):
    relpath = str(path.relative_to(root)).replace("\\", "/")
    findings = []
    for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        scan_sequence(function.body, function_args(function), relpath, function.name, findings)
    return findings


def scan_file(path, root=NOETHYS):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    _source, tree = loaded
    return _scan_loaded(tree, path, root)


def build_report(root=NOETHYS):
    findings = []
    for path in iter_python_files(root):
        findings.extend(scan_file(path, root))
    unique = {}
    for item in findings:
        key = (item["file"], item["function"], item["if_line"], item["line"], item["name"])
        unique[key] = item
    findings = sorted(unique.values(), key=lambda item: (item["file"], item["line"], item["name"]))
    return {
        "count": len(findings),
        "kinds": dict(Counter(item["kind"] for item in findings)),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "findings": findings,
    }


def _coverage_session(root=NOETHYS):
    session = SourceAuditSession(iter_python_files(root))
    for path in session.paths:
        session.parse(path)
    return session


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args(argv)

    coverage = _coverage_session()
    coverage.report(prefix="Couverture audit affectations conditionnelles")
    coverage.require_complete()

    report = build_report()
    print(f"BRANCH_ASSIGNMENT_GAPS={report['count']}")
    for item in report["findings"]:
        print(f"- {item['file']}:{item['line']} {item['function']} — {item['name']} ({item['detail']})")
    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())