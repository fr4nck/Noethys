# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import unittest

from noethys.Utils.UTILS_PMSL_Openings import PMSLOpeningService


class FakeDB(object):
    """Sous-ensemble GestionDB suffisant pour tester la prévisualisation."""

    def __init__(self, units=None, groups=None, unit_groups=None, openings=None):
        self.units = units or {}
        self.groups = groups or {}
        self.unit_groups = unit_groups or {}
        self.openings = openings or {}
        self._rows = []

    def ExecuterReq(self, query):
        match = re.search(r"FROM unites WHERE IDunite=(\d+)", query)
        if match:
            unit_id = int(match.group(1))
            activity_id = self.units.get(unit_id)
            self._rows = [(unit_id, activity_id)] if activity_id is not None else []
            return

        match = re.search(r"FROM groupes WHERE IDgroupe=(\d+)", query)
        if match:
            group_id = int(match.group(1))
            activity_id = self.groups.get(group_id)
            self._rows = [(group_id, activity_id)] if activity_id is not None else []
            return

        match = re.search(r"FROM unites_groupes WHERE IDunite=(\d+)", query)
        if match:
            unit_id = int(match.group(1))
            self._rows = [(group_id,) for group_id in self.unit_groups.get(unit_id, [])]
            return

        match = re.search(
            r"FROM ouvertures WHERE IDactivite=(\d+) AND IDunite=(\d+) AND IDgroupe=(\d+) AND date='([^']+)'",
            query,
        )
        if match:
            key = (int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4))
            opening_id = self.openings.get(key)
            self._rows = [(opening_id,)] if opening_id is not None else []
            return

        raise AssertionError("Requête inattendue: %s" % query)

    def ResultatReq(self):
        return self._rows


class PMSLOpeningServiceTests(unittest.TestCase):
    def _action(self, unit_id, group_id, date_value="2026-10-04"):
        return {
            "pmsl_ref": "ref-1",
            "payload": {
                "action": "upsert_opening",
                "IDunite": unit_id,
                "IDgroupe": group_id,
                "date": date_value,
                "pmsl_assignment_ids": [42, 43],
            },
        }

    def test_unit_without_explicit_group_restriction_accepts_same_activity_group(self):
        # Cas observé dans une sauvegarde PMSL réelle : les couples (8, 8),
        # (9, 9), (11, 11), (12, 11) ont des ouvertures alors que la table
        # unites_groupes ne contient aucune ligne pour ces unités. Dans Noethys,
        # l'absence de ligne signifie « tous les groupes de l'activité ».
        db = FakeDB(units={8: 6}, groups={8: 6}, unit_groups={})
        service = PMSLOpeningService(db=db)
        result = service.preview_action(self._action(8, 8))
        self.assertEqual("create", result["status"])
        self.assertEqual(6, result["detail"]["IDactivite"])
        self.assertEqual([42, 43], result["detail"]["pmsl_assignment_ids"])

    def test_explicit_group_restriction_blocks_another_group(self):
        db = FakeDB(units={7: 5}, groups={7: 5, 10: 5}, unit_groups={7: [7]})
        service = PMSLOpeningService(db=db)
        result = service.preview_action(self._action(7, 10))
        self.assertEqual("blocked", result["status"])
        self.assertEqual("unit_group_not_linked", result["reason"])
        self.assertEqual([7], result["detail"]["allowed_group_ids"])

    def test_existing_opening_is_idempotent(self):
        # ID 5779 / 2026-10-03 est issu de la sauvegarde de recette utilisée
        # pour valider le contrat métier du bridge.
        openings = {(5, 7, 7, "2026-10-03"): 5779}
        db = FakeDB(units={7: 5}, groups={7: 5}, unit_groups={7: [7]}, openings=openings)
        service = PMSLOpeningService(db=db)
        result = service.preview_action(self._action(7, 7, "2026-10-03"))
        self.assertEqual("unchanged", result["status"])
        self.assertEqual(5779, result["detail"]["IDouverture"])

    def test_activity_mismatch_stays_blocking(self):
        db = FakeDB(units={8: 6}, groups={9: 7})
        service = PMSLOpeningService(db=db)
        result = service.preview_action(self._action(8, 9))
        self.assertEqual("blocked", result["status"])
        self.assertEqual("activity_mismatch", result["reason"])


if __name__ == "__main__":
    unittest.main()
