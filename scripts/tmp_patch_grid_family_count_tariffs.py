from pathlib import Path

source_path = Path("noethys/Ctrl/CTRL_Grille.py")
source = source_path.read_text(encoding="utf-8")
marker = (
    "                                    else:\n"
    "                                        # Si tarif unique pour chacun des individus\n"
)
replacement = (
    "                                    else:\n"
    "                                        # Un palier nul reste un tarif valide : le recalcul doit pouvoir ramener\n"
    "                                        # explicitement les prestations restantes à 0.0.\n"
    "                                        montant_tarif_tmp = 0.0\n"
    "                                        # Si tarif unique pour chacun des individus\n"
)
if source.count(marker) != 1:
    raise SystemExit("Structure CTRL_Grille inattendue")
source_path.write_text(source.replace(marker, replacement, 1), encoding="utf-8")

for temporary in (
    Path("tests/test_tmp_grid_family_count_triage.py"),
    Path("scripts/tmp_patch_grid_family_count_tariffs.py"),
    Path(".github/workflows/tmp-audit-grid-family-count-tariffs.yml"),
):
    if temporary.exists():
        temporary.unlink()
