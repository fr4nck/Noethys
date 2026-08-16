# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from noethys.Utils.UTILS_PMSL_Sync import PMSLSyncService
from noethys.Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient


class FakeClient(PMSLNoethysBridgeClient):
    def __init__(self):
        self.source_instance = "noethys-sport"
        self.acks = []

    def pull(self, limit=20):
        return {
            "protocol": "pmsl-noethys-native/1",
            "batches": [{
                "batch_uuid": "batch-1",
                "source_instance": self.source_instance,
                "actions": [{"pmsl_ref": "ref-1", "payload": {"action": "upsert_opening"}}],
            }],
        }

    def ack(self, batch_uuid, items):
        self.acks.append((batch_uuid, items))
        return {"accepted": True, "batch_uuid": batch_uuid}


class FakeOpeningService(object):
    def __init__(self, valid=True):
        self.valid = valid
        self.preview_calls = 0
        self.apply_calls = 0
        self.closed = False

    def preview_batch(self, batch):
        self.preview_calls += 1
        return {"valid": self.valid, "counts": {"create": 1 if self.valid else 0, "blocked": 0 if self.valid else 1}}

    def apply_batch(self, batch):
        self.apply_calls += 1
        return {"ack_items": [{"pmsl_ref": "ref-1", "state": "applied"}]}

    def close(self):
        self.closed = True


class PMSLSyncServiceTests(unittest.TestCase):
    def test_preview_never_applies_or_acks(self):
        client = FakeClient()
        openings = FakeOpeningService(valid=True)
        service = PMSLSyncService(client, opening_service=openings)
        result = service.run(apply=False)
        self.assertEqual("preview", result["mode"])
        self.assertTrue(result["aucune_ecriture_effectuee"])
        self.assertEqual(1, openings.preview_calls)
        self.assertEqual(0, openings.apply_calls)
        self.assertEqual([], client.acks)

    def test_apply_writes_then_acks(self):
        client = FakeClient()
        openings = FakeOpeningService(valid=True)
        service = PMSLSyncService(client, opening_service=openings)
        result = service.run(apply=True)
        self.assertEqual("apply", result["mode"])
        self.assertFalse(result["aucune_ecriture_effectuee"])
        self.assertEqual(1, openings.apply_calls)
        self.assertEqual(1, len(client.acks))
        self.assertTrue(result["results"][0]["ack_sent"])

    def test_blocked_batch_is_not_applied_or_acked(self):
        client = FakeClient()
        openings = FakeOpeningService(valid=False)
        service = PMSLSyncService(client, opening_service=openings)
        result = service.run(apply=True)
        self.assertEqual(0, openings.apply_calls)
        self.assertEqual([], client.acks)
        self.assertFalse(result["results"][0]["applied"])
        self.assertFalse(result["results"][0]["ack_sent"])


if __name__ == "__main__":
    unittest.main()
