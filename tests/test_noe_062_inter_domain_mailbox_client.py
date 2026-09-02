#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
sys.path.insert(0, str(NOETHYS))

from Utils import UTILS_Interdomain_Mailbox_Client as client


IDEMPOTENCE = "session-actual:test:r1:activity_users"
CORRELATION = "11111111-1111-1111-1111-111111111111"
DELIVERY_ID = "22222222-2222-2222-2222-222222222222"


def delivery(target="activity_users"):
    return {
        "mailbox_version": "inter-domain-mailbox-pull/1",
        "delivery_id": DELIVERY_ID,
        "target_domain": target,
        "idempotence_key": IDEMPOTENCE,
        "correlation_id": CORRELATION,
        "attempts": 1,
        "signed_delivery": {"envelope": {"x": 1}, "signature": "a" * 64},
    }


class FakeTransport:
    def __init__(self, deliveries=None, ack_error=None):
        self.deliveries = list(deliveries or [])
        self.acks = []
        self.ack_error = ack_error

    def Reclamer(self, limit=20):
        self.limit = limit
        return tuple(self.deliveries)

    def Acquitter(self, delivery_id, receipt):
        if self.ack_error:
            raise self.ack_error
        self.acks.append((delivery_id, dict(receipt)))
        return {"status": receipt["status"]}


class FakeResponse:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class MailboxClientTests(unittest.TestCase):
    def test_applied_delivery_is_acked_accepted(self):
        transport = FakeTransport([delivery()])
        receipt = {
            "status": "accepted",
            "idempotence_key": IDEMPOTENCE,
            "correlation_id": CORRELATION,
            "detail": "",
        }
        with patch.object(client.UTILS_Interdomain_Delivery, "RecevoirLivraisonSignee", return_value=receipt) as receive:
            summary = client.SynchroniserMailbox(object(), transport, {"kid": b"x" * 32}, limit=4)
        self.assertEqual(summary["accepted"], 1)
        self.assertEqual(summary["acked"], 1)
        self.assertEqual(transport.acks[0][1]["status"], "accepted")
        self.assertEqual(receive.call_count, 1)

    def test_technical_consumer_failure_becomes_retryable_ack(self):
        transport = FakeTransport([delivery()])
        with patch.object(client.UTILS_Interdomain_Delivery, "RecevoirLivraisonSignee", side_effect=RuntimeError("db offline")):
            summary = client.SynchroniserMailbox(object(), transport, {"kid": b"x" * 32})
        self.assertEqual(summary["retryable"], 1)
        self.assertEqual(transport.acks[0][1]["status"], "retryable")
        self.assertNotIn("Bearer", transport.acks[0][1].get("detail", ""))

    def test_ack_failure_is_not_swallowed_after_local_apply(self):
        transport = FakeTransport([delivery()], ack_error=client.MailboxTransportError("offline"))
        receipt = {
            "status": "accepted",
            "idempotence_key": IDEMPOTENCE,
            "correlation_id": CORRELATION,
            "detail": "",
        }
        with patch.object(client.UTILS_Interdomain_Delivery, "RecevoirLivraisonSignee", return_value=receipt):
            with self.assertRaises(client.MailboxTransportError):
                client.SynchroniserMailbox(object(), transport, {"kid": b"x" * 32})

    def test_other_domain_is_rejected_before_consumer(self):
        transport = FakeTransport([delivery(target="hr_employment")])
        with patch.object(client.UTILS_Interdomain_Delivery, "RecevoirLivraisonSignee") as receive:
            with self.assertRaises(client.MailboxPullError):
                client.SynchroniserMailbox(object(), transport, {"kid": b"x" * 32})
        receive.assert_not_called()

    def test_http_transport_requires_https_and_sends_bearer_only_in_header(self):
        with self.assertRaises(client.MailboxTransportError):
            client.TransportMailboxHTTP("http://example.invalid", "secret")
        seen = {}
        def opener(request, timeout):
            seen["url"] = request.full_url
            seen["auth"] = request.headers.get("Authorization")
            seen["body"] = request.data
            return FakeResponse({"deliveries": []})
        transport = client.TransportMailboxHTTP(
            "https://portal.example.test",
            "mbx1.token.secret-value-long-enough-for-test",
            opener=opener,
        )
        self.assertEqual(transport.Reclamer(limit=3), ())
        self.assertEqual(seen["auth"], "Bearer mbx1.token.secret-value-long-enough-for-test")
        self.assertNotIn(b"secret-value", seen["body"])
        self.assertTrue(seen["url"].endswith(client.CLAIM_PATH))


if __name__ == "__main__":
    unittest.main()
