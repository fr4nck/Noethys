# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CTRL_REPAS = ROOT / "noethys" / "Ctrl" / "CTRL_Commande_repas.py"
DLG_COLONNE = ROOT / "noethys" / "Dlg" / "DLG_Saisie_commandes_colonne.py"


class PMSLMealOrderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctrl_text = CTRL_REPAS.read_text(encoding="utf-8")
        cls.dlg_text = DLG_COLONNE.read_text(encoding="utf-8")

    def test_reserved_meal_dates_are_added_before_total_row(self):
        consumption_loop = self.ctrl_text.index(
            "for IDconso, date, IDgroupe, IDunite, IDindividu in listeDonnees :"
        )
        add_reserved_date = self.ctrl_text.index(
            'if date not in dictDonnees["liste_dates"] :',
            consumption_loop,
        )
        sort_dates = self.ctrl_text.index(
            'dictDonnees["liste_dates"].sort()',
            add_reserved_date,
        )
        append_total = self.ctrl_text.index(
            'dictDonnees["liste_dates"].append(_(u"Total"))',
            sort_dates,
        )

        self.assertLess(consumption_loop, add_reserved_date)
        self.assertLess(add_reserved_date, sort_dates)
        self.assertLess(sort_dates, append_total)

    def test_total_row_is_not_inserted_before_consumptions_are_loaded(self):
        openings_marker = self.ctrl_text.index("# Ouvertures")
        consumptions_marker = self.ctrl_text.index("# Consommations", openings_marker)
        between = self.ctrl_text[openings_marker:consumptions_marker]
        self.assertNotIn('append(_(u"Total"))', between)

    def test_animator_column_is_a_first_class_numeric_category(self):
        self.assertIn(
            '"numerique_animateurs" : _(u"Numérique (Animateurs)")',
            self.dlg_text,
        )
        self.assertIn(
            '("numerique_animateurs", PAGE_Vide(self))',
            self.dlg_text,
        )

    def test_delivery_point_wording_is_explicit(self):
        self.assertIn(
            "Cochez les unités à regrouper pour ce point de livraison",
            self.dlg_text,
        )


if __name__ == "__main__":
    unittest.main()
