#!/usr/bin/env python3
"""Exécute les contrôles légers avant tout packaging Windows."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECKS = (
    ("Dépendances", [sys.executable, "scripts/audit_dependency_usage.py", "noethys", "requirements.txt"], False),
    ("Compatibilité Python 3", [sys.executable, "scripts/audit_python3_compat.py", "noethys"], False),
    ("Parsing de dates", [sys.executable, "scripts/audit_fragile_date_parsing.py", "noethys"], False),
    ("Layout wx/AUI", [sys.executable, "scripts/audit_wx_layout_compat.py", "noethys"], False),
    ("Arguments numériques wx", [sys.executable, "scripts/audit_wx_numeric_arguments.py", "noethys"], False),
    ("Cycle de vie wx", [sys.executable, "scripts/audit_wx_lifecycle.py", "noethys"], False),
    ("Frontières bytes/texte", [sys.executable, "scripts/audit_bytes_text_boundaries.py", "noethys"], False),
    ("Frontières UTF-8", [sys.executable, "scripts/audit_utf8_boundaries.py", "noethys"], False),
    ("Frontières XML", [sys.executable, "scripts/audit_xml_encoding_boundaries.py", "noethys"], False),
    ("Frontières CSV", [sys.executable, "scripts/audit_csv_boundaries.py", "noethys"], False),
    ("Pillow / ReportLab", [sys.executable, "scripts/audit_pillow_reportlab_compat.py", "noethys"], False),
    ("Constantes Pillow", [sys.executable, "scripts/modernize_pillow_resampling.py", "noethys"], False),
    ("Ouvertures texte UTF-8", [sys.executable, "scripts/modernize_text_file_encodings.py", "noethys"], False),
    ("Chemins SQLite Unicode", [sys.executable, "scripts/modernize_sqlite_unicode_paths.py"], False),
    ("Imports dynamiques", [sys.executable, "scripts/audit_dynamic_imports.py", "noethys"], False),
    ("API modernes", [sys.executable, "scripts/audit_modern_api_compat.py", "noethys"], False),
    ("Codemod ouvertures UTF-8", [sys.executable, "scripts/smoke_text_encoding_codemod.py"], True),
    ("Codemod Pillow", [sys.executable, "scripts/smoke_pillow_resampling_codemod.py"], True),
    ("Conventions CSV UTF-8", [sys.executable, "scripts/smoke_csv_utf8_tableur.py"], True),
    ("Alignement packaging", [sys.executable, "scripts/smoke_packaging_alignment.py"], True),
    ("Imports critiques", [sys.executable, "scripts/smoke_import_dependencies.py"], True),
    ("Piles fonctionnelles", [sys.executable, "scripts/smoke_optional_feature_stacks.py"], True),
    ("Imports dynamiques littéraux", [sys.executable, "scripts/smoke_dynamic_imports.py"], True),
    ("Graphe du démarrage", [sys.executable, "scripts/smoke_startup_module_graph.py"], True),
    ("Cycle GestionDB SQLite", [sys.executable, "scripts/smoke_gestiondb_lifecycle.py"], True),
    ("Chemins Windows", [sys.executable, "scripts/smoke_windows_filesystem_paths.py"], True),
    ("Fichiers du dépôt UTF-8", [sys.executable, "scripts/smoke_repository_utf8.py"], True),
    ("Allers-retours UTF-8", [sys.executable, "scripts/smoke_utf8_roundtrip.py"], True),
    ("UTILS_Json UTF-8", [sys.executable, "scripts/smoke_utils_json_utf8.py"], True),
    ("Configuration UTF-8", [sys.executable, "scripts/smoke_config_utf8_recovery.py"], True),
    ("Ressources du package", [sys.executable, "scripts/smoke_packaged_resources.py"], True),
    ("Hooks runtime", [sys.executable, "scripts/smoke_runtime_hooks.py"], True),
    ("Compilation", [sys.executable, "-m", "compileall", "-q", "noethys"], True),
)


def main() -> int:
    warnings = 0
    for label, command, blocking in CHECKS:
        level = "bloquant" if blocking else "informatif"
        print(f"\n== {label} ({level}) ==")
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode == 0:
            continue
        if blocking:
            print(f"Échec bloquant du préflight : {label}", file=sys.stderr)
            return result.returncode
        warnings += 1
        print(
            f"Avertissement : l’audit {label} a retourné le code {result.returncode}, "
            "mais le packaging peut continuer.",
            file=sys.stderr,
        )

    if warnings:
        print(f"\nPréflight terminé avec {warnings} avertissement(s).")
    else:
        print("\nPréflight terminé sans erreur.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
