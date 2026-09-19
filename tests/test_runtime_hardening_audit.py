#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import json
import unittest
from pathlib import Path

from scripts import audit_runtime_hardening as hardening


class RuntimeHardeningAuditTests(unittest.TestCase):
    def test_full_runtime_triage_is_exported_for_the_hardening_pass(self):
        report = hardening.build_report()

        output = Path("tmp/runtime-hardening-audit.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.assertIn("RESULT_UNGUARDED", report["summary"])
        self.assertIn("RESULT_ASSIGN", report["summary"])
        self.assertIn("BARE_EXCEPT", report["summary"])
        self.assertTrue(all(value == 0 for value in report["zero_debt"].values()))

        # La passe globale a ramené à zéro la file réellement ambiguë : les
        # accès restants sont soit garantis par SQL, soit explicitement gardés,
        # soit des invariants d'entité à valider en recette. Toute nouvelle
        # classification ``review`` doit donc casser le contrat au lieu de se
        # perdre dans l'inventaire JSON.
        for kind in ("RESULT_UNGUARDED", "RESULT_ASSIGN"):
            reviews = report["summary"][kind]["classifications"].get("review", 0)
            self.assertEqual(reviews, 0, msg=f"Nouvelle alerte runtime à revoir : {kind}={reviews}")

    def test_historical_case_utils_procedures_1678_is_reclassified_as_dialog_selection(self):
        # Faux classement historique : entity_lookup_invariant alors que
        # l'index vient de dlg.GetSelections() sur la liste elle-même, dans
        # une compréhension de liste répartie sur deux lignes.
        report = hardening.build_report()
        target = next(
            item
            for item in report["findings"]["RESULT_ASSIGN"]
            if item["file"] == "Utils/UTILS_Procedures.py" and item["line_assign"] == 1678
        )
        self.assertEqual(target["classification"], "dialog_selection")


class ComprehensionSelectionIndexTests(unittest.TestCase):
    """`_comprehension_selection_index` doit reconnaître ``items[index] for
    index in dlg.GetSelections()`` que la clause ``for`` soit sur la même
    ligne que l'accès ou reportée à la ligne suivante par le formatage —
    c'est exactement la forme manquée sur Utils/UTILS_Procedures.py:1678."""

    def test_single_line_comprehension_is_recognised(self):
        source = "resultat = [listeInscriptions[index] for index in dlg.GetSelections()]\n"
        tree = ast.parse(source)
        self.assertTrue(
            hardening._comprehension_selection_index(tree, 1, "listeInscriptions")
        )

    def test_two_line_comprehension_is_recognised(self):
        # La clause for est repoussée à la ligne suivante : c'est la forme
        # historique manquée par la fenêtre de lignes précédente.
        source = (
            "resultat = [listeInscriptions[index]\n"
            "            for index in dlg.GetSelections()]\n"
        )
        tree = ast.parse(source)
        self.assertTrue(
            hardening._comprehension_selection_index(tree, 1, "listeInscriptions")
        )

    def test_getselection_singular_variant_is_also_recognised(self):
        source = (
            "resultat = [listeUnites[index]\n"
            "            for index in dlg.GetSelection()]\n"
        )
        tree = ast.parse(source)
        self.assertTrue(
            hardening._comprehension_selection_index(tree, 1, "listeUnites")
        )

    def test_plain_sql_lookup_without_comprehension_is_not_flagged(self):
        # Un vrai lookup SQL par ID suivi de result[0] : aucune compréhension,
        # aucune sélection wx — ne doit jamais devenir dialog_selection.
        source = (
            "listeDonnees = DB.ResultatReq()\n"
            "nom = listeDonnees[0][0]\n"
        )
        tree = ast.parse(source)
        self.assertFalse(
            hardening._comprehension_selection_index(tree, 2, "listeDonnees")
        )

    def test_comprehension_over_a_different_variable_is_not_flagged(self):
        # La compréhension existe mais indexe une AUTRE liste que celle
        # affectée par ResultatReq() : ne doit pas être confondue.
        source = (
            "resultat = [autreListe[index]\n"
            "            for index in dlg.GetSelections()]\n"
        )
        tree = ast.parse(source)
        self.assertFalse(
            hardening._comprehension_selection_index(tree, 1, "resultat")
        )


if __name__ == "__main__":
    unittest.main()
