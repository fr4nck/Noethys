#!/usr/bin/env python3
"""Inventaire statique des commandes wxPython de Noethys Vanilla.

Ce script ne pretend pas qu'une commande est fonctionnelle parce qu'elle existe.
Il recense boutons, menus, outils et Bind, qualifie les liaisons evidentes et
produit la matrice de recette. Les comportements GUI/BDD non executes restent
BLOCKED avec HUMAN_RECIPE_REQUIRED.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_TESTABLE"}
COLUMNS = [
    "Écran / module",
    "Commande",
    "Déclencheur",
    "Précondition",
    "Résultat attendu",
    "Résultat obtenu",
    "Statut",
    "Type de défaut",
    "Gravité",
    "Trace / test associé",
]

STANDARD_WX_IDS = {
    "wx.ID_OK",
    "wx.ID_CANCEL",
    "wx.ID_CLOSE",
    "wx.ID_EXIT",
    "wx.ID_APPLY",
    "wx.ID_HELP",
    "wx.ID_SAVE",
    "wx.ID_OPEN",
    "wx.ID_NEW",
    "wx.ID_PRINT",
    "wx.ID_PREVIEW",
}

MENU_METHODS = {"Append", "AppendItem", "AppendCheckItem", "AppendRadioItem"}
TOOL_METHODS = {"AddTool", "AddSimpleTool", "AddCheckTool", "AddRadioTool"}
FIRST_PARTY_PACKAGES = {"Ctrl", "Dlg", "Ol", "Utils", "Data", "ObjectListView"}


@dataclass
class Command:
    path: str
    class_name: str
    function_name: str
    line: int
    kind: str
    source: str
    command_id: str
    label: str
    event: str = ""
    handler: str = ""
    result_obtained: str = ""
    status: str = "BLOCKED"
    defect_type: str = "HUMAN_RECIPE_REQUIRED"
    severity: str = ""
    trace: str = ""

    @property
    def scope_key(self) -> Tuple[str, str]:
        local_scope = "" if self.source.startswith("self.") else self.function_name
        return self.class_name, local_scope


@dataclass
class Binding:
    path: str
    class_name: str
    function_name: str
    line: int
    source: str
    command_id: str
    event: str
    handler: str

    @property
    def scope_key(self) -> Tuple[str, str]:
        local_scope = "" if self.source.startswith("self.") else self.function_name
        return self.class_name, local_scope


@dataclass
class Diagnostic:
    path: str
    line: int
    kind: str
    message: str


@dataclass
class ScanResult:
    commands: List[Command]
    diagnostics: List[Diagnostic]
    parse_errors: List[str]
    python_files: int
    handler_count: int
    binding_count: int


def expr_text(node: Optional[ast.AST]) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = expr_text(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return node.value
        return repr(node.value)
    if isinstance(node, ast.Call):
        name = expr_text(node.func)
        if name in {"_", "gettext", "u"} and node.args:
            return literal_text(node.args[0]) or expr_text(node.args[0])
        return name
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def literal_text(node: Optional[ast.AST]) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.strip()
    if isinstance(node, ast.Call) and expr_text(node.func) in {"_", "gettext", "u"} and node.args:
        return literal_text(node.args[0])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = literal_text(node.left)
        right = literal_text(node.right)
        return (left + right).strip() if left or right else ""
    return ""


def keyword_expr(call: ast.Call, *names: str) -> str:
    for kw in call.keywords:
        if kw.arg in names:
            return expr_text(kw.value)
    return ""


def extract_label(call: ast.Call) -> str:
    for name in ("label", "text", "caption", "shortHelp", "short_help", "helpString"):
        value = keyword_expr(call, name)
        if value:
            return value
    for arg in call.args:
        value = literal_text(arg)
        if value:
            return value
    return ""


def extract_id(call: ast.Call, kind: str) -> str:
    value = keyword_expr(call, "id", "toolId", "itemid")
    if value:
        return value
    if kind == "button" and len(call.args) >= 2:
        return expr_text(call.args[1])
    if kind in {"menu", "tool"} and call.args:
        return expr_text(call.args[0])
    return ""


def is_button_ctor(name: str) -> bool:
    short = name.rsplit(".", 1)[-1]
    if short in {"Button", "BitmapButton", "ToggleButton", "CommandLinkButton"}:
        return True
    lowered = name.lower()
    return "bouton" in lowered or "button" in lowered


def is_menu_item_ctor(name: str) -> bool:
    return name.endswith("MenuItem") or name == "wx.MenuItem"


def target_text(node: ast.AST) -> str:
    if isinstance(node, (ast.Name, ast.Attribute)):
        return expr_text(node)
    if isinstance(node, (ast.Tuple, ast.List)):
        return ",".join(target_text(x) for x in node.elts)
    return ""


def meaningful_body(node: ast.FunctionDef) -> List[ast.stmt]:
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    return body


def handler_is_empty(node: ast.FunctionDef) -> bool:
    body = meaningful_body(node)
    if not body:
        return True
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Return) and (stmt.value is None or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None)):
            continue
        return False
    return True


class FileVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.class_stack: List[str] = []
        self.function_stack: List[str] = []
        self.commands: List[Command] = []
        self.bindings: List[Binding] = []
        self.handlers: Dict[Tuple[str, str], ast.FunctionDef] = {}

    @property
    def class_name(self) -> str:
        return self.class_stack[-1] if self.class_stack else "<module>"

    @property
    def function_name(self) -> str:
        return self.function_stack[-1] if self.function_stack else "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.handlers[(self.class_name, node.name)] = node
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _add_command(self, call: ast.Call, source: str, kind: str) -> None:
        label = extract_label(call)
        command_id = extract_id(call, kind)
        fallback = source or command_id or f"{kind}@{getattr(call, 'lineno', 0)}"
        self.commands.append(
            Command(
                path=self.path,
                class_name=self.class_name,
                function_name=self.function_name,
                line=getattr(call, "lineno", 0),
                kind=kind,
                source=source,
                command_id=command_id,
                label=label or fallback,
            )
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call):
            call = node.value
            name = expr_text(call.func)
            source = target_text(node.targets[0]) if node.targets else ""
            if is_button_ctor(name):
                self._add_command(call, source, "button")
            elif is_menu_item_ctor(name):
                self._add_command(call, source, "menu")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.value, ast.Call):
            call = node.value
            name = expr_text(call.func)
            source = target_text(node.target)
            if is_button_ctor(name):
                self._add_command(call, source, "button")
            elif is_menu_item_ctor(name):
                self._add_command(call, source, "menu")
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        call = node.value if isinstance(node.value, ast.Call) else None
        if call is not None and isinstance(call.func, ast.Attribute):
            method = call.func.attr
            if method in MENU_METHODS:
                source = f"{expr_text(call.func.value)}#menu@{getattr(call, 'lineno', 0)}"
                self._add_command(call, source, "menu")
            elif method in TOOL_METHODS:
                source = f"{expr_text(call.func.value)}#tool@{getattr(call, 'lineno', 0)}"
                self._add_command(call, source, "tool")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "Bind" and len(node.args) >= 2:
            owner = expr_text(node.func.value)
            event = expr_text(node.args[0])
            handler = expr_text(node.args[1])
            source = ""
            if owner not in {"self", "wx.EvtHandler"}:
                source = owner
            elif len(node.args) >= 3:
                source = expr_text(node.args[2])
            source = keyword_expr(node, "source") or source
            command_id = keyword_expr(node, "id")
            self.bindings.append(
                Binding(
                    path=self.path,
                    class_name=self.class_name,
                    function_name=self.function_name,
                    line=getattr(node, "lineno", 0),
                    source=source,
                    command_id=command_id,
                    event=event,
                    handler=handler,
                )
            )
        self.generic_visit(node)


def iter_python_files(root: Path) -> Iterable[Path]:
    base = root / "noethys"
    for path in sorted(base.rglob("*.py")):
        parts = set(path.parts)
        if "__pycache__" in parts:
            continue
        yield path


def first_party_import_diagnostics(root: Path, path: Path, tree: ast.AST) -> List[Diagnostic]:
    result: List[Diagnostic] = []
    noethys = root / "noethys"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bits = alias.name.split(".")
                if bits and bits[0] in FIRST_PARTY_PACKAGES and len(bits) > 1:
                    candidate = noethys.joinpath(*bits).with_suffix(".py")
                    package_init = noethys.joinpath(*bits, "__init__.py")
                    if not candidate.exists() and not package_init.exists():
                        result.append(Diagnostic(str(path.relative_to(root)), node.lineno, "IMPORT_LOCAL_MISSING", alias.name))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            bits = node.module.split(".")
            if bits and bits[0] in FIRST_PARTY_PACKAGES:
                module_path = noethys.joinpath(*bits)
                module_file = module_path.with_suffix(".py")
                package_init = module_path / "__init__.py"
                if not module_file.exists() and not package_init.exists():
                    result.append(Diagnostic(str(path.relative_to(root)), node.lineno, "IMPORT_LOCAL_MISSING", node.module))
                elif package_init.exists():
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        candidate = module_path / f"{alias.name}.py"
                        if alias.name.startswith(("DLG_", "CTRL_", "OL_", "UTILS_", "DATA_")) and not candidate.exists():
                            result.append(Diagnostic(str(path.relative_to(root)), node.lineno, "IMPORT_MEMBER_MISSING", f"{node.module}.{alias.name}"))
    return result


def match_commands(commands: List[Command], bindings: List[Binding], handlers: Dict[Tuple[str, str], ast.FunctionDef]) -> None:
    by_source: Dict[Tuple[str, str, str], List[Binding]] = defaultdict(list)
    by_id: Dict[Tuple[str, str], List[Binding]] = defaultdict(list)
    for binding in bindings:
        if binding.source:
            cls, local = binding.scope_key
            by_source[(cls, local, binding.source)].append(binding)
            if binding.source.startswith("self."):
                by_source[(cls, "", binding.source)].append(binding)
        if binding.command_id:
            by_id[(binding.class_name, binding.command_id)].append(binding)

    for command in commands:
        cls, local = command.scope_key
        candidates: List[Binding] = []
        if command.source:
            candidates.extend(by_source.get((cls, local, command.source), []))
            if command.source.startswith("self."):
                candidates.extend(by_source.get((cls, "", command.source), []))
        if command.command_id:
            candidates.extend(by_id.get((cls, command.command_id), []))

        # Dedoublonnage en conservant l'ordre source.
        unique: List[Binding] = []
        seen = set()
        for item in candidates:
            key = (item.line, item.source, item.command_id, item.event, item.handler)
            if key not in seen:
                unique.append(item)
                seen.add(key)

        if unique:
            binding = sorted(unique, key=lambda x: x.line)[0]
            command.event = binding.event or "Bind"
            command.handler = binding.handler
            handler_name = binding.handler.rsplit(".", 1)[-1] if binding.handler else ""
            handler_node = handlers.get((command.class_name, handler_name))
            if handler_node is not None and handler_is_empty(handler_node):
                command.result_obtained = f"Handler {binding.handler} vide/pass détecté statiquement"
                command.status = "FAIL"
                command.defect_type = "HANDLER_EMPTY"
                command.severity = "P2"
                command.trace = f"{command.path}:{command.line}; handler:{handler_node.lineno}"
            else:
                command.result_obtained = f"Liaison statique vers {binding.handler or '<handler dynamique>'}; comportement métier non exécuté"
                command.status = "BLOCKED"
                command.defect_type = "HUMAN_RECIPE_REQUIRED"
                command.trace = f"{command.path}:{command.line}; bind:{binding.line}"
        elif command.command_id in STANDARD_WX_IDS:
            command.event = "wx standard ID"
            command.handler = "comportement implicite wx"
            command.result_obtained = "Commande standard détectée; fermeture/validation native non exécutée en audit headless"
            command.status = "BLOCKED"
            command.defect_type = "HUMAN_RECIPE_REQUIRED"
            command.trace = f"{command.path}:{command.line}"
        else:
            command.event = "aucun Bind explicite détecté"
            command.result_obtained = "Commande créée sans liaison explicite corrélable statiquement; peut être liée par ID, héritage ou code dynamique"
            command.status = "BLOCKED"
            command.defect_type = "STATIC_BIND_UNRESOLVED"
            command.trace = f"{command.path}:{command.line}"


def scan(root: Path) -> ScanResult:
    commands: List[Command] = []
    diagnostics: List[Diagnostic] = []
    parse_errors: List[str] = []
    handlers: Dict[Tuple[str, str, str], ast.FunctionDef] = {}
    bindings: List[Binding] = []
    python_files = 0

    for path in iter_python_files(root):
        python_files += 1
        rel = str(path.relative_to(root)).replace("\\", "/")
        try:
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source, filename=rel)
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append(f"{rel}: {exc}")
            continue
        visitor = FileVisitor(rel)
        visitor.visit(tree)
        commands.extend(visitor.commands)
        bindings.extend(visitor.bindings)
        for key, node in visitor.handlers.items():
            handlers[(rel, key[0], key[1])] = node
        diagnostics.extend(first_party_import_diagnostics(root, path, tree))

    per_file_handlers: Dict[str, Dict[Tuple[str, str], ast.FunctionDef]] = defaultdict(dict)
    for (path, class_name, name), node in handlers.items():
        per_file_handlers[path][(class_name, name)] = node
    per_file_bindings: Dict[str, List[Binding]] = defaultdict(list)
    for binding in bindings:
        per_file_bindings[binding.path].append(binding)
    per_file_commands: Dict[str, List[Command]] = defaultdict(list)
    for command in commands:
        per_file_commands[command.path].append(command)

    for path, file_commands in per_file_commands.items():
        match_commands(file_commands, per_file_bindings[path], per_file_handlers[path])

    commands.sort(key=lambda c: (c.path.lower(), c.class_name.lower(), c.line, c.label.lower()))
    diagnostics.sort(key=lambda d: (d.path.lower(), d.line, d.kind))
    return ScanResult(commands, diagnostics, parse_errors, python_files, len(handlers), len(bindings))


def known_rows() -> List[Dict[str, str]]:
    return [
        {
            "Écran / module": "Listes / navigation Vanilla",
            "Commande": "Voir tout",
            "Déclencheur": "Commande d'affichage de liste",
            "Précondition": "Liste concernée ouverte",
            "Résultat attendu": "La liste utile est affichée directement sans étape Voir tout",
            "Résultat obtenu": "Comportement connu à supprimer au profit de l'affichage direct",
            "Statut": "FAIL",
            "Type de défaut": "UX_COMMAND_REDUNDANT",
            "Gravité": "P2",
            "Trace / test associé": "KNOWN-UI-VOIR-TOUT; recette humaine à localiser précisément",
        },
        {
            "Écran / module": "Interface Vanilla",
            "Commande": "Thème système / sombre",
            "Déclencheur": "Thème Windows / préférence interface",
            "Précondition": "Windows configuré en thème sombre ou système",
            "Résultat attendu": "Vanilla reste en thème clair historique",
            "Résultat obtenu": "Point connu à auditer: Vanilla doit rester en clair",
            "Statut": "BLOCKED",
            "Type de défaut": "HUMAN_RECIPE_REQUIRED",
            "Gravité": "P3",
            "Trace / test associé": "KNOWN-UI-LIGHT-THEME; recette Windows requise",
        },
        {
            "Écran / module": "Liste d'attente",
            "Commande": "Bouton / commande Liste d'attente",
            "Déclencheur": "Clic utilisateur",
            "Précondition": "Contexte permettant l'accès à la liste d'attente",
            "Résultat attendu": "La commande ouvre ou exécute l'action de liste d'attente attendue",
            "Résultat obtenu": "Recette humaine antérieure: bouton observé sans effet",
            "Statut": "FAIL",
            "Type de défaut": "COMMAND_NO_EFFECT",
            "Gravité": "P2",
            "Trace / test associé": "KNOWN-ATTENTE-NO-EFFECT; noethys/Ctrl/CTRL_Attente.py à corréler",
        },
        {
            "Écran / module": "Liste des consommations",
            "Commande": "Fermer pendant chargement puis rouvrir",
            "Déclencheur": "Bouton Fermer ou croix Windows",
            "Précondition": "Chargement de la liste en cours sur base Docker de recette",
            "Résultat attendu": "Fermeture propre; réouverture immédiate sans crash ni traitement orphelin",
            "Résultat obtenu": "Sur maintenance/vanilla: crash Windows 0xc0000005 reproduit; correctif séparé dans PR #359",
            "Statut": "FAIL",
            "Type de défaut": "NATIVE_WX_LIFECYCLE_CRASH",
            "Gravité": "P1",
            "Trace / test associé": "PR #359; Application Error 1000 / 0xc0000005",
        },
        {
            "Écran / module": "Liste des consommations / questionnaires",
            "Commande": "Ouvrir / charger la liste",
            "Déclencheur": "Ouverture de la liste des consommations",
            "Précondition": "Base Docker de recette avec volume représentatif de réponses questionnaires",
            "Résultat attendu": "Chargement dans un délai compatible avec l'usage courant",
            "Résultat obtenu": "Chargement global des réponses questionnaires identifié comme piste de lenteur; mesure runtime non encore faite",
            "Statut": "BLOCKED",
            "Type de défaut": "PERFORMANCE_AUDIT_REQUIRED",
            "Gravité": "P2",
            "Trace / test associé": "UTILS_Questionnaires.GetReponses(type='individu'); HUMAN_RECIPE_REQUIRED",
        },
    ]


def command_to_row(command: Command) -> Dict[str, str]:
    module = f"{command.path} — {command.class_name}"
    precondition = "Fenêtre/module instancié"
    if "LIST" in command.event.upper() or "CONTEXT" in command.event.upper():
        precondition += "; sélection/contexte requis à valider"
    expected = f"Déclencher {command.handler or command.label} sans exception et atteindre le comportement métier attendu"
    return {
        "Écran / module": module,
        "Commande": command.label,
        "Déclencheur": command.event or command.kind,
        "Précondition": precondition,
        "Résultat attendu": expected,
        "Résultat obtenu": command.result_obtained,
        "Statut": command.status,
        "Type de défaut": command.defect_type,
        "Gravité": command.severity,
        "Trace / test associé": command.trace,
    }


def md_escape(value: object) -> str:
    text = str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    return text.strip()


def render_markdown(result: ScanResult, baseline_sha: str) -> str:
    command_rows = [command_to_row(c) for c in result.commands]
    extra_rows = known_rows()
    rows = command_rows + extra_rows
    counts = Counter(row["Statut"] for row in rows)
    severity_counts = Counter(row["Gravité"] for row in rows if row["Gravité"])
    defect_counts = Counter(row["Type de défaut"] for row in rows if row["Type de défaut"])

    lines: List[str] = []
    lines.append("# Audit fonctionnel systématique des commandes — Noethys Vanilla")
    lines.append("")
    lines.append(f"Baseline auditée : `maintenance/vanilla` / `{baseline_sha or 'SHA_NON_FOURNI'}`.")
    lines.append("")
    lines.append("## Portée et règle de preuve")
    lines.append("")
    lines.append(
        "Inventaire généré statiquement à partir des sources wxPython (`wx.Button`, `wx.BitmapButton`, boutons custom, "
        "`wx.MenuItem`, `Menu.Append*`, outils de barres, `Bind(...)`, handlers et actions de listes). "
        "Une liaison statique correcte ne vaut pas preuve fonctionnelle : tant que le comportement réel n'est pas "
        "exécuté de façon sûre, la commande reste `BLOCKED` avec `HUMAN_RECIPE_REQUIRED`."
    )
    lines.append("")
    lines.append("Aucune production n'est utilisée par cet audit. Les actions destructives, d'envoi, de facturation ou de publication doivent rester mockées, annulées ou exécutées uniquement sur données jetables de recette.")
    lines.append("")
    lines.append("## Synthèse")
    lines.append("")
    lines.append(f"- Fichiers Python analysés : **{result.python_files}**")
    lines.append(f"- Commandes wx recensées statiquement : **{len(result.commands)}**")
    lines.append(f"- Scénarios/observations connus ajoutés : **{len(extra_rows)}**")
    lines.append(f"- Lignes de la matrice : **{len(rows)}**")
    lines.append(f"- Bind recensés : **{result.binding_count}**")
    lines.append(f"- Fonctions/handlers recensés : **{result.handler_count}**")
    lines.append(f"- PASS : **{counts.get('PASS', 0)}**")
    lines.append(f"- FAIL : **{counts.get('FAIL', 0)}**")
    lines.append(f"- BLOCKED : **{counts.get('BLOCKED', 0)}**")
    lines.append(f"- NOT_TESTABLE : **{counts.get('NOT_TESTABLE', 0)}**")
    lines.append("")
    lines.append("Les PASS de la matrice sont volontairement rares au premier passage : le test structurel seul ne transforme jamais une commande en PASS.")
    lines.append("")
    lines.append("### Gravités détectées / connues")
    lines.append("")
    for severity in ("P0", "P1", "P2", "P3"):
        lines.append(f"- {severity} : **{severity_counts.get(severity, 0)}**")
    lines.append("")
    lines.append("### Types de défaut / blocage")
    lines.append("")
    for name, count in sorted(defect_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{name}` : {count}")
    lines.append("")
    lines.append("## Tests automatisés associés")
    lines.append("")
    lines.append("- `python -m compileall -q noethys` : compilation syntaxique de l'arbre source dans la CI d'audit.")
    lines.append("- `python -m unittest tests.test_vanilla_ui_command_audit` : parse AST exhaustif, invariants de matrice, corrélation Bind/source/ID sur cas synthétiques et contrôle des scénarios connus.")
    lines.append("- `python tools/audit_ui_commands.py --root . --output docs/VANILLA_UI_COMMAND_AUDIT.md` : régénération déterministe de cette matrice.")
    lines.append("")
    lines.append("## Diagnostics statiques hors matrice")
    lines.append("")
    if result.parse_errors:
        lines.append("### Erreurs de parsing")
        lines.append("")
        for item in result.parse_errors:
            lines.append(f"- `{md_escape(item)}`")
        lines.append("")
    else:
        lines.append("Aucune erreur de parsing AST détectée.")
        lines.append("")
    if result.diagnostics:
        lines.append("### Imports locaux suspects")
        lines.append("")
        for item in result.diagnostics:
            lines.append(f"- `{item.path}:{item.line}` — `{item.kind}` — `{md_escape(item.message)}`")
        lines.append("")
    else:
        lines.append("Aucun import first-party manquant détecté par le contrôle statique borné.")
        lines.append("")
    lines.append("## Matrice exhaustive des commandes recensées")
    lines.append("")
    lines.append("| " + " | ".join(COLUMNS) + " |")
    lines.append("| " + " | ".join("---" for _ in COLUMNS) + " |")
    for row in rows:
        lines.append("| " + " | ".join(md_escape(row.get(column, "")) for column in COLUMNS) + " |")
    lines.append("")
    lines.append("## Recette humaine restante")
    lines.append("")
    lines.append(
        "Toute ligne `BLOCKED` marquée `HUMAN_RECIPE_REQUIRED` doit être exécutée sur Windows avec la base Docker de recette, "
        "jamais sur la production. Pour chaque fenêtre pertinente : ouvrir, exercer la commande avec une précondition minimale, "
        "vérifier l'effet métier ou l'échec propre, fermer par le bouton puis par la croix Windows, et répéter l'ouverture/fermeture "
        "pour les fenêtres à chargement long ou contrôle virtuel."
    )
    lines.append("")
    lines.append("Pour `Supprimer`, `Envoyer`, `Facturer`, `Publier` et opérations équivalentes : mocks, transaction annulée ou données jetables uniquement.")
    lines.append("")
    lines.append("## Recommandations de PR séparées")
    lines.append("")
    lines.append("1. Conserver la PR #359 isolée pour le crash natif de fermeture/réouverture de la liste des consommations.")
    lines.append("2. Ouvrir une PR dédiée pour la commande Liste d'attente après localisation et reproduction minimale du bouton sans effet.")
    lines.append("3. Traiter `Voir tout` dans une PR UI Vanilla dédiée, sans mélanger d'autres corrections métier.")
    lines.append("4. Auditer puis borner le thème Vanilla clair dans une PR séparée uniquement si la recette Windows confirme l'écart.")
    lines.append("5. Auditer la performance de chargement des questionnaires dans une PR performance séparée, avec mesure sur base Docker représentative avant tout changement.")
    lines.append("")
    return "\n".join(lines)


def write_output(text: str, output: Optional[Path]) -> None:
    if output is None:
        print(text)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output")
    parser.add_argument("--baseline-sha", default="")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    result = scan(root)
    text = render_markdown(result, args.baseline_sha)
    write_output(text, Path(args.output) if args.output else None)
    if result.parse_errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
