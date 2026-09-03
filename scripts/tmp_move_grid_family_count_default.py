from pathlib import Path

source_path = Path("noethys/Ctrl/CTRL_Grille.py")
lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)

target_comment = "# Recherche du tarif à appliquer à chaque individu"
default_comment_1 = "# Un palier nul reste un tarif valide : le recalcul doit pouvoir ramener"
default_comment_2 = "# explicitement les prestations restantes à 0.0."
default_assignment = "montant_tarif_tmp = 0.0"

start = next(i for i, line in enumerate(lines) if target_comment in line)
indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]

# Retire l'ancien bloc de repli s'il est encore dans la branche non dégressive.
filtered = []
skip = 0
for line in lines:
    if skip:
        skip -= 1
        continue
    if default_comment_1 in line:
        skip = 2
        continue
    filtered.append(line)
lines = filtered

# Recalcule la position après suppression et place le repli avant le branchement degr/non-degr.
start = next(i for i, line in enumerate(lines) if target_comment in line)
insert_at = start + 1
block = [
    indent + default_comment_1 + "\n",
    indent + default_comment_2 + "\n",
    indent + default_assignment + "\n",
]
lines[insert_at:insert_at] = block
source_path.write_text("".join(lines), encoding="utf-8")

text = source_path.read_text(encoding="utf-8")
if text.count(default_assignment) < 1:
    raise SystemExit("montant_tarif_tmp non initialisé")
print("montant_tarif_tmp déplacé avant le branchement degr/non-degr")

for temporary in (
    Path("scripts/tmp_move_grid_family_count_default.py"),
    Path(".github/workflows/tmp-move-grid-family-count-default.yml"),
):
    if temporary.exists():
        temporary.unlink()
