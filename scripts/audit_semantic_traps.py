#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie des pièges sémantiques transverses sans modifier le code applicatif.

L'audit privilégie le rappel : chaque signal reste à qualifier humainement avant
correction ou attribution à l'upstream. Les catégories visent des défauts qui
échappent facilement à une recherche textuelle simple : état partagé par défaut,
asymétrie validation/sauvegarde, cycle de vie modal et blocage de la boucle wx.
La couverture des sources analysées est bloquante.

Pour les valeurs mutables par défaut, la priorité haute est réservée aux cas où
la valeur partagée peut réellement être modifiée. Les motifs qui réaffectent le
paramètre avant mutation, trient seulement un conteneur vide ou échouent sur une
lecture obligatoire avant toute mutation sont conservés comme signaux qualifiés
faibles au lieu d'être présentés comme des défauts confirmés.
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
MUTATING_METHODS = {
    "append", "extend", "insert", "remove", "pop", "clear", "sort", "reverse",
    "update", "setdefault", "add", "discard", "difference_update",
    "intersection_update", "symmetric_difference_update",
}
EMPTY_DEFAULT_NON_GROWING_METHODS = {
    "remove", "pop", "clear", "sort", "reverse", "discard",
    "difference_update", "intersection_update",
}
UI_CALLBACK_PREFIXES = ("On", "Timer", "Handle", "Traitement", "Refresh", "MAJ")


def iter_python_files(root=NOETHYS):
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def _mutable_defaults(function):
    positional = list(function.args.posonlyargs) + list(function.args.args)
    defaults = [None] * (len(positional) - len(function.args.defaults)) + list(function.args.defaults)
    pairs = list(zip(positional, defaults))
    pairs.extend(zip(function.args.kwonlyargs, function.args.kw_defaults))
    result = {}
    for arg, default in pairs:
        if isinstance(default, ast.List):
            result[arg.arg] = {"type": "list", "empty": len(default.elts) == 0}
        elif isinstance(default, ast.Dict):
            result[arg.arg] = {"type": "dict", "empty": len(default.keys) == 0}
        elif isinstance(default, ast.Set):
            result[arg.arg] = {"type": "set", "empty": len(default.elts) == 0}
    return result


def _target_rebinds_name(target, name):
    if isinstance(target, ast.Name):
        return target.id == name
    if isinstance(target, (ast.Tuple, ast.List)):
        return any(_target_rebinds_name(item, name) for item in target.elts)
    return False


def _top_level_rebind_before(function, name, line):
    """Vrai si un statement séquentiel réaffecte le paramètre avant ``line``.

    Une affectation située dans un ``if``/``try`` n'est volontairement pas
    considérée comme garantie : il peut rester un chemin qui conserve la valeur
    par défaut partagée.
    """
    for statement in function.body:
        if getattr(statement, "lineno", line) >= line:
            break
        if isinstance(statement, ast.Assign):
            if any(_target_rebinds_name(target, name) for target in statement.targets):
                return True
        elif isinstance(statement, ast.AnnAssign):
            if _target_rebinds_name(statement.target, name):
                return True
    return False


def _subscript_loads_name(node, name):
    for child in ast.walk(node):
        if not isinstance(child, ast.Subscript) or not isinstance(child.ctx, ast.Load):
            continue
        if isinstance(child.value, ast.Name) and child.value.id == name:
            return True
    return False


def _required_top_level_subscript_read_before(function, name, line):
    """Repère une lecture ``name[...]`` séquentielle avant la mutation.

    On ne descend pas dans les structures de contrôle : une lecture dans un
    chemin conditionnel ne prouve pas que l'appel avec la valeur vide échoue
    avant la mutation. Les statements simples, eux, sont exécutés sur tout
    chemin qui atteint le statement suivant.
    """
    control_statements = (
        ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
        ast.With, ast.AsyncWith,
    )
    if hasattr(ast, "Match"):
        control_statements = control_statements + (ast.Match,)

    for statement in function.body:
        if getattr(statement, "lineno", line) >= line:
            break
        if isinstance(statement, control_statements):
            continue
        if _subscript_loads_name(statement, name):
            return True
    return False


class _MutationVisitor(ast.NodeVisitor):
    def __init__(self, name):
        self.name = name
        self.events = []

    def _record(self, node, operation):
        self.events.append((node.lineno, getattr(node, "col_offset", 0), operation, node))

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id == self.name and node.func.attr in MUTATING_METHODS:
                self._record(node, node.func.attr)
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == self.name:
                operation = "slice_mutation" if isinstance(target.slice, ast.Slice) else "item_mutation"
                self._record(node, operation)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        target = node.target
        if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == self.name:
            operation = "slice_mutation" if isinstance(target.slice, ast.Slice) else "item_mutation"
            self._record(node, operation)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        target = node.target
        if isinstance(target, ast.Name) and target.id == self.name:
            self._record(node, "augassign")
        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == self.name:
            operation = "slice_mutation" if isinstance(target.slice, ast.Slice) else "item_mutation"
            self._record(node, operation)
        self.generic_visit(node)

    def visit_Delete(self, node):
        for target in node.targets:
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == self.name:
                self._record(node, "item_mutation")
        self.generic_visit(node)

    # Les noms identiques dans un scope imbriqué ne désignent pas le paramètre.
    def visit_FunctionDef(self, node):
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_Lambda(self, node):
        return

    def visit_ClassDef(self, node):
        return


def _mutation_events(function, name):
    visitor = _MutationVisitor(name)
    for statement in function.body:
        visitor.visit(statement)
    return sorted(visitor.events, key=lambda item: (item[0], item[1]))


def _classify_mutable_default(function, name, default_info):
    """Retourne le signal le plus sévère concernant une valeur par défaut.

    Un résultat ``mutable_default_mutated`` signifie que l'appel sans argument
    peut réellement altérer l'objet créé lors de la définition de la fonction.
    Les motifs prouvés inertes ou détachés de cet objet restent visibles en
    ``mutable_default_qualified`` avec priorité basse.
    """
    qualified = None
    for line, _col, operation, _node in _mutation_events(function, name):
        if _top_level_rebind_before(function, name, line):
            if qualified is None:
                qualified = (line, "rebound_before_mutation")
            continue

        if default_info["empty"] and operation in EMPTY_DEFAULT_NON_GROWING_METHODS:
            if qualified is None:
                qualified = (line, "empty_default_non_growing:%s" % operation)
            continue

        if (
            default_info["empty"]
            and default_info["type"] == "dict"
            and operation == "item_mutation"
            and _required_top_level_subscript_read_before(function, name, line)
        ):
            if qualified is None:
                qualified = (line, "empty_default_fails_before_mutation")
            continue

        if default_info["empty"] and default_info["type"] == "list" and operation == "item_mutation":
            if qualified is None:
                qualified = (line, "empty_list_item_mutation_requires_existing_item")
            continue

        return {
            "kind": "mutable_default_mutated",
            "priority": "high",
            "line": line,
            "detail": operation,
        }

    if qualified is not None:
        return {
            "kind": "mutable_default_qualified",
            "priority": "low",
            "line": qualified[0],
            "detail": qualified[1],
        }
    return None


def _name_escapes(function, name):
    for node in ast.walk(function):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Name) and node.value.id == name:
            return True, node.lineno
    return False, 0


def _attribute_calls(function, method_name):
    found = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != method_name:
            continue
        owner = node.func.value
        if isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id == "self":
            found.append((owner.attr, node.lineno))
    return found


def _assigned_dialog_names(function):
    dialogs = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target = node.targets[0].id
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        callee = value.func
        text = ""
        if isinstance(callee, ast.Attribute):
            text = callee.attr
        elif isinstance(callee, ast.Name):
            text = callee.id
        if "Dialog" in text or text.startswith("DLG_") or text in {"MessageDialog", "TextEntryDialog", "SingleChoiceDialog", "MultiChoiceDialog"}:
            dialogs[target] = node.lineno
    return dialogs


def _method_calls_on_name(function, name, method):
    lines = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != method:
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id == name:
            lines.append(node.lineno)
    return lines


def _qualified_name(node):
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _scan_loaded(source, tree, path, root=NOETHYS):
    rel = str(path.relative_to(root)).replace("\\", "/")
    findings = []

    for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        for name, default_info in _mutable_defaults(function).items():
            mutable_finding = _classify_mutable_default(function, name, default_info)
            escapes, return_line = _name_escapes(function, name)
            if mutable_finding is not None:
                findings.append({
                    **mutable_finding,
                    "file": rel,
                    "function": function.name,
                    "parameter": name,
                    "default_type": default_info["type"],
                })
            elif escapes:
                findings.append({
                    "kind": "mutable_default_escape",
                    "priority": "medium",
                    "file": rel,
                    "function": function.name,
                    "line": return_line,
                    "parameter": name,
                    "default_type": default_info["type"],
                    "detail": "returned_directly",
                })

        validations = _attribute_calls(function, "Validation")
        saves = {name for name, _line in _attribute_calls(function, "Sauvegarde")}
        if validations and any(control in saves for control, _line in validations) and function.name.lower() in {"onboutonok", "onboutonvalider", "valider", "sauvegarder", "sauvegarde"}:
            for control, line in validations:
                if control not in saves:
                    findings.append({
                        "kind": "validation_save_mixed_api",
                        "priority": "low",
                        "file": rel,
                        "function": function.name,
                        "line": line,
                        "control": control,
                        "detail": "contrôles hétérogènes : Validation() et Sauvegarde() ne prouvent pas un contrat de persistance commun",
                    })

        for name, create_line in _assigned_dialog_names(function).items():
            shown = _method_calls_on_name(function, name, "ShowModal")
            destroyed = _method_calls_on_name(function, name, "Destroy")
            if shown and not destroyed:
                findings.append({
                    "kind": "modal_without_destroy",
                    "priority": "medium",
                    "file": rel,
                    "function": function.name,
                    "line": shown[0],
                    "dialog": name,
                    "detail": f"dialogue créé ligne {create_line}",
                })

        if function.name.startswith(UI_CALLBACK_PREFIXES):
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                if _qualified_name(node.func) in {"time.sleep", "sleep"}:
                    findings.append({
                        "kind": "blocking_sleep_ui_callback",
                        "priority": "high",
                        "file": rel,
                        "function": function.name,
                        "line": node.lineno,
                        "detail": _qualified_name(node.func),
                    })

    return findings


def scan_file(path, root=NOETHYS):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    source, tree = loaded
    return _scan_loaded(source, tree, path, root)


def build_report(root=NOETHYS):
    findings = []
    for path in iter_python_files(root):
        findings.extend(scan_file(path, root))
    findings.sort(key=lambda item: (item["priority"] != "high", item["kind"], item["file"], item["line"]))
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
    coverage.report(prefix="Couverture audit pièges sémantiques")
    coverage.require_complete()

    report = build_report()
    print(f"SEMANTIC_TRAPS={report['count']} — {report['kinds']} — {report['priorities']}")
    for item in report["findings"]:
        if item["priority"] == "high":
            print(f"- HIGH {item['kind']} {item['file']}:{item['line']} {item['function']}")
    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Rapport JSON exporté : {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
