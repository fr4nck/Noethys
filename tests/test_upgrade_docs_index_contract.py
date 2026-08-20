from pathlib import Path


def test_upgrade_docs_index_lists_core_contracts():
    root = Path(__file__).resolve().parents[1]
    texte = (root / "docs" / "README_UPGRADE_NOETHYS.md").read_text(encoding="utf-8")
    for nom in ("UPGRADE_UI_UX_RULES.md", "DASHBOARD_MODERNISATION.md", "MAIL_MODULE_ARCHITECTURE.md"):
        assert nom in texte
