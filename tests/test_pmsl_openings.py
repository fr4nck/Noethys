# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import unittest

from noethys.Utils.UTILS_PMSL_Openings import PMSLOpeningService


class FakeConnection(object):
    def __init__(self, db):
        self.db = db

    def rollback(self):
        self.db.rollback_calls += 1
        self.db.openings = dict(self.db._committed_openings)


class FakeDB(object):
    """Sous-ensemble GestionDB suffisant pour tester preview + transactions."""

    def __init__(self, units=None, groups=None, unit_groups=None, openings=None, fail_on_insert=None):
        self.units = units or {}
        self.groups = groups or {}
        self.unit_groups = unit_groups or {}
        self.openings = dict(openings or {})
        self._committed_openings = dict(self.openings)
        self.fail_on_insert = fail_on_insert
        self.insert_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0
        self._rows = []
        self.connexion = FakeConnection(self)

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

    def ReqInsert(self, table, values, commit=False):
        self.insert_calls += 1
        if self.fail_on_insert == self.insert_calls:
            raise RuntimeError("erreur SQL injectée")
        self.assert_no_commit(commit)
        data = dict(values)
        key = (int(data["IDactivite"]), int(data["IDunite"]), int(data["IDgroupe"]), data["date"])
        new_id = max([0] + list(self.openings.values())) + 1
        self.openings[key] = new_id
        return new_id

    def Commit(self):
        self.commit_calls += 1
        self._committed_openings = dict(self.openings)

    @staticmethod
    def assert_no_commit(commit):
        if commit:
            raise AssertionError("Le service doit grouper le lot dans une transaction unique")


class PMSLOpeningServiceTests(unittest.TestCase):
    def _action(self, unit_id, group_id, date_value="2026-10-04", ref="ref-1"):
        return {
            "pmsl_ref": ref,
            "payload": {
                "action": "upsert_opening",
                "IDunite": unit_id,
                "IDgroupe": group_id,
                "date": date_value,
                "pmsl_assignment_ids": [42, 43],
            },
        }

    def test_unit_without_explicit_group_restriction_accepts_same_activity_group(self):
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

    def test_apply_is_idempotent_after_commit(self):
        db = FakeDB(units={8: 6}, groups={8: 6})
        service = PMSLOpeningService(db=db)
        batch = {"batch_uuid": "batch-idempotent", "actions": [self._action(8, 8)]}
        first = service.apply_batch(batch)
        first_id = first["ack_items"][0]["opening_id"]
        self.assertEqual(1, db.insert_calls)
        self.assertEqual(1, db.commit_calls)
        second = service.apply_batch(batch)
        self.assertEqual(first_id, second["ack_items"][0]["opening_id"])
        self.assertEqual(1, db.insert_calls)
        self.assertEqual(2, db.commit_calls)
        self.assertEqual("unchanged", second["ack_items"][0]["response"]["operation"])

    def test_mid_batch_sql_failure_rolls_back_first_insert(self):
        db = FakeDB(units={8: 6, 9: 6}, groups={8: 6, 9: 6}, fail_on_insert=2)
        service = PMSLOpeningService(db=db)
        batch = {
            "batch_uuid": "batch-rollback",
            "actions": [
                self._action(8, 8, "2026-10-04", "ref-1"),
                self._action(9, 9, "2026-10-04", "ref-2"),
            ],
        }
        with self.assertRaises(RuntimeError):
            service.apply_batch(batch)
        self.assertEqual(2, db.insert_calls)
        self.assertEqual(0, db.commit_calls)
        self.assertEqual(1, db.rollback_calls)
        self.assertEqual({}, db.openings)


if __name__ == "__main__":
    unittest.main()
