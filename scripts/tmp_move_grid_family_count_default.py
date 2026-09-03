from pathlib import Path

source_path = Path("noethys/Ctrl/CTRL_Grille.py")
lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)

anchor = "nbreIndividus = len(listeIndividusPresents)"
branch_token = 'if "degr" in methode_calcul :'
default_assignment = "montant_tarif_tmp = 0.0"

anchor_index = next(i for i, line in enumerate(lines) if anchor in line)
branch_index = next(i for i in range(anchor_index + 1, len(lines)) if branch_token in lines[i])
assignment_index = next(i for i in range(branch_index + 1, len(lines)) if default_assignment in lines[i])

# Le repli historique se trouve dans le else non-degressif. Retire l'affectation
# et ses deux commentaires immediatement precedents, sans dependre des accents.
remove_from = assignment_index
comments_removed = 0
while remove_from > branch_index + 1 and comments_removed < 2:
    previous = lines[remove_from - 1]
    if previous.lstrip().startswith("#"):
        remove_from -= 1
        comments_removed += 1
    else:
        break
del lines[remove_from:assignment_index + 1]

# Recalcule l'ancre apres suppression, puis initialise avant le if degr/non-degr.
anchor_index = next(i for i, line in enumerate(lines) if anchor in line)
branch_index = next(i for i in range(anchor_index + 1, len(lines)) if branch_token in lines[i])
indent = lines[branch_index][: len(lines[branch_index]) - len(lines[branch_index].lstrip())]
lines[branch_index:branch_index] = [
    indent + "# Un palier nul reste un tarif valide lors du recalcul.\n",
    indent + default_assignment + "\n",
]

source_path.write_text("".join(lines), encoding="utf-8")
text = source_path.read_text(encoding="utf-8")
if text.count(default_assignment) < 1:
    raise SystemExit("montant_tarif_tmp non initialise")
print("montant_tarif_tmp place avant le branchement degr/non-degr")

for temporary in (
    Path("scripts/tmp_move_grid_family_count_default.py"),
    Path(".github/workflows/tmp-move-grid-family-count-default.yml"),
):
    if temporary.exists():
        temporary.unlink()
