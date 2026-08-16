# -*- coding: utf-8 -*-
"""Orchestrateur PMSL <-> Noethys.

Simulation par défaut. En mode apply, un lot n'est écrit que si toute sa simulation
est valide, puis l'accusé est renvoyé à PMSL. Une panne réseau après commit local
est signalée explicitement : l'écriture Noethys n'est jamais présentée comme annulée.
"""
from __future__ import unicode_literals

try:
    from noethys.Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient
    from noethys.Utils.UTILS_PMSL_Openings import PMSLOpeningService, PMSLOpeningError
except ImportError:  # lancement historique depuis le répertoire noethys
    from Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient
    from Utils.UTILS_PMSL_Openings import PMSLOpeningService, PMSLOpeningError


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
        any_local_write = False
        for batch in batches:
            preview = self.opening_service.preview_batch(batch)
            item = {
                "batch_uuid": batch.get("batch_uuid"),
                "source_instance": batch.get("source_instance"),
                "preview": preview,
                "applied": False,
                "ack_sent": False,
                "sync_complete": False,
            }
            if apply and preview.get("valid"):
                applied = self.opening_service.apply_batch(batch)
                item["applied"] = True
                item["application"] = applied
                any_local_write = True
                try:
                    ack = self.client.ack(batch.get("batch_uuid"), applied.get("ack_items") or [])
                except Exception as exc:
                    # Le commit Noethys a déjà eu lieu. On conserve donc le résultat
                    # local et on marque uniquement l'accusé distant comme manquant.
                    # Un rejeu est sûr grâce à l'idempotence des ouvertures.
                    item["ack_error"] = str(exc)
                else:
                    item["ack_sent"] = True
                    item["sync_complete"] = True
                    item["ack"] = ack
            results.append(item)
        return {
            "protocol": pulled.get("protocol") if isinstance(pulled, dict) else None,
            "source_instance": self.client.source_instance,
            "mode": "apply" if apply else "preview",
            "batch_count": len(results),
            "results": results,
            "aucune_ecriture_effectuee": not any_local_write,
            "synchronisation_complete": all(item.get("sync_complete") for item in results) if apply and results else not apply,
        }


def run_sync(base_url, secret, source_instance, apply=False, limit=20):
    """Point d'entrée simple utilisable depuis UI, console ou tâche planifiée."""
    client = PMSLNoethysBridgeClient(base_url, secret, source_instance)
    service = PMSLSyncService(client)
    try:
        return service.run(apply=apply, limit=limit)
    finally:
        service.close()
