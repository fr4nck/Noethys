# -*- coding: utf-8 -*-
"""Orchestrateur PMSL <-> Noethys.

Simulation par défaut. En mode apply, un lot n'est écrit que si toute sa simulation
est valide, puis l'accusé est renvoyé à PMSL.
"""
from __future__ import unicode_literals

from noethys.Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient
from noethys.Utils.UTILS_PMSL_Openings import PMSLOpeningService, PMSLOpeningError


class PMSLSyncService(object):
    def __init__(self, client, opening_service=None):
        if not isinstance(client, PMSLNoethysBridgeClient):
            raise TypeError("client PMSLNoethysBridgeClient requis")
        self.client = client
        self.opening_service = opening_service or PMSLOpeningService()
        self._owns_service = opening_service is None

    def close(self):
        if self._owns_service and self.opening_service:
            self.opening_service.close()

    def run(self, apply=False, limit=20):
        """Récupère les lots et les simule. N'écrit que si apply=True."""
        pulled = self.client.pull(limit=limit)
        batches = pulled.get("batches") or [] if isinstance(pulled, dict) else []
        results = []
        for batch in batches:
            preview = self.opening_service.preview_batch(batch)
            item = {
                "batch_uuid": batch.get("batch_uuid"),
                "source_instance": batch.get("source_instance"),
                "preview": preview,
                "applied": False,
                "ack_sent": False,
            }
            if apply and preview.get("valid"):
                applied = self.opening_service.apply_batch(batch)
                ack = self.client.ack(batch.get("batch_uuid"), applied.get("ack_items") or [])
                item["applied"] = True
                item["ack_sent"] = True
                item["ack"] = ack
            results.append(item)
        return {
            "protocol": pulled.get("protocol") if isinstance(pulled, dict) else None,
            "source_instance": self.client.source_instance,
            "mode": "apply" if apply else "preview",
            "batch_count": len(results),
            "results": results,
            "aucune_ecriture_effectuee": not apply,
        }


def run_sync(base_url, secret, source_instance, apply=False, limit=20):
    """Point d'entrée simple utilisable depuis UI, console ou tâche planifiée."""
    client = PMSLNoethysBridgeClient(base_url, secret, source_instance)
    service = PMSLSyncService(client)
    try:
        return service.run(apply=apply, limit=limit)
    finally:
        service.close()
