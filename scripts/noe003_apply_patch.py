from pathlib import Path

path = Path("noethys/Dlg/DLG_Export_compta.py")
text = path.read_text(encoding="utf-8")

old_join = """        LEFT JOIN cotisations ON cotisations.IDprestation = prestations.IDprestation
        LEFT JOIN types_cotisations ON types_cotisations.IDtype_cotisation = cotisations.IDtype_cotisation
"""
new_join = """        LEFT JOIN (
            SELECT IDprestation, MIN(IDcotisation) AS IDcotisation
            FROM cotisations
            WHERE IDprestation IS NOT NULL
            GROUP BY IDprestation
        ) cotisation_unique ON cotisation_unique.IDprestation = prestations.IDprestation
        LEFT JOIN cotisations ON cotisations.IDcotisation = cotisation_unique.IDcotisation
        LEFT JOIN types_cotisations ON types_cotisations.IDtype_cotisation = cotisations.IDtype_cotisation
"""
old_group = "        GROUP BY prestations.IDprestation\n"

assert text.count(old_join) == 2, "Expected exactly two cotisation joins"
assert text.count(old_group) == 2, "Expected exactly two outer GROUP BY clauses"

updated = text.replace(old_join, new_join).replace(old_group, "")

assert updated.count("cotisation_unique ON cotisation_unique.IDprestation = prestations.IDprestation") == 2
assert "GROUP BY prestations.IDprestation" not in updated

path.write_text(updated, encoding="utf-8")
