from pathlib import Path

source_path = Path("noethys/Ctrl/CTRL_Grille.py")
source = source_path.read_text(encoding="utf-8")
old = (
    "                                    # Recherche du tarif à appliquer à chaque individu\n"
    "                                    if \"degr\" in methode_calcul :\n"
    "                                        # Si tarif dégressif différent pour chaque individu\n"
)
new = (
    "                                    # Recherche du tarif à appliquer à chaque individu\n"
    "                                    # Un palier nul reste un tarif valide : le recalcul doit pouvoir ramener\n"
    "                                    # explicitement les prestations restantes à 0.0.\n"
    "                                    montant_tarif_tmp = 0.0\n"
    "                                    if \"degr\" in methode_calcul :\n"
    "                                        # Si tarif dégressif différent pour chaque individu\n"
)
old_else = (
    "                                    else:\n"
    "                                        # Un palier nul reste un tarif valide : le recalcul doit pouvoir ramener\n"
    "                                        # explicitement les prestations restantes à 0.0.\n"
    "                                        montant_tarif_tmp = 0.0\n"
    "                                        # Si tarif unique pour chacun des individus\n"
)
new_else = (
    "                                    else:\n"
    "                                        # Si tarif unique pour chacun des individus\n"
)
if source.count(old) != 1 or source.count(old_else) != 1:
    raise SystemExit("Structure CTRL_Grille inattendue")
source = source.replace(old, new, 1).replace(old_else, new_else, 1)
source_path.write_text(source, encoding="utf-8")

for temporary in (
    Path("scripts/tmp_move_grid_family_count_default.py"),
    Path(".github/workflows/tmp-move-grid-family-count-default.yml"),
):
    if temporary.exists():
        temporary.unlink()
