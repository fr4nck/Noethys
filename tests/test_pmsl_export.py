# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from noethys.Utils.UTILS_PMSL_Export import PMSLExportService
from noethys.Utils.UTILS_PMSL_ReturnSync import _validate_preview_response
from noethys.Utils.UTILS_PMSL_NoethysBridge import PMSLBridgeError


class FakeDB(object):
    def __init__(self):
        self.query = None

    def ExecuterReq(self, query):
        self.query = query

    def ResultatReq(self):
        if "FROM activites" in self.query:
            return [(5, u"Badminton")]
        if "FROM unites" in self.query:
            return [(7, 5, u"Séance")]
        if "FROM groupes" in self.query:
            return [(7, 5, u"Adultes")]
        if "FROM ouvertures" in self.query:
            return [(5779, 5, 7, 7, "2026-10-03")]
        return []


class FakeClient(object):
    def __init__(self):
        self.payloads = []

    def push(self, payload):
        self.payloads.append(payload)
        return {
            "accepted": True,
            "status": "preview",
            "requires_human_validation": True,
            "batch_uuid": "incoming-1",
            "line_count": 1,
        }


class PMSLExportTests(unittest.TestCase):
    def test_build_payload_contains_reference_and_calendar(self):
        service = PMSLExportService(db=FakeDB())
        payload = service.build_payload("2026-09-01", "2026-10-31")
        self.assertEqual("noethys_reference_calendar", payload["kind"])
        self.assertEqual(1, payload["version"])
        self.assertEqual({"activities": 1, "units": 1, "groups": 1, "openings": 1}, payload["counts"])
        self.assertEqual(5, payload["activities"][0]["IDactivite"])
        self.assertEqual(7, payload["units"][0]["IDunite"])
        self.assertEqual(7, payload["groups"][0]["IDgroupe"])
        self.assertEqual(5779, payload["openings"][0]["IDouverture"])
        self.assertEqual("2026-10-03", payload["openings"][0]["date"])

    def test_push_keeps_pmsl_in_preview_mode(self):
        service = PMSLExportService(db=FakeDB())
        client = FakeClient()
        result = service.push(client, "2026-09-01", "2026-10-31")
        self.assertEqual(1, len(client.payloads))
        response = _validate_preview_response(result["response"])
        self.assertTrue(response["accepted"])
        self.assertEqual("preview", response["status"])
        self.assertTrue(response["requires_human_validation"])
        self.assertEqual("incoming-1", response["batch_uuid"])

    def test_return_contract_rejects_non_preview_status(self):
        with self.assertRaises(PMSLBridgeError):
            _validate_preview_response({
                "accepted": True,
                "status": "applied",
                "requires_human_validation": True,
                "batch_uuid": "incoming-1",
            })

    def test_return_contract_rejects_missing_human_validation(self):
        with self.assertRaises(PMSLBridgeError):
            _validate_preview_response({
                "accepted": True,
                "status": "preview",
                "requires_human_validation": False,
                "batch_uuid": "incoming-1",
            })

    def test_return_contract_requires_batch_uuid(self):
        with self.assertRaises(PMSLBridgeError):
            _validate_preview_response({
                "accepted": True,
                "status": "preview",
                "requires_human_validation": True,
            })

    def test_invalid_date_is_rejected_before_query(self):
        service = PMSLExportService(db=FakeDB())
        with self.assertRaises(ValueError):
            service.build_payload("01/09/2026", "2026-10-31")


if __name__ == "__main__":
    unittest.main()
