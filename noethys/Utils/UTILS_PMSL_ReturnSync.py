# -*- coding: utf-8 -*-
"""Point d'entrée UI pour le flux retour Noethys -> PMSL."""
from __future__ import unicode_literals

try:
    from noethys.Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient
    from noethys.Utils.UTILS_PMSL_Export import PMSLExportService
except ImportError:  # lancement historique depuis le répertoire noethys
    from Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient
    from Utils.UTILS_PMSL_Export import PMSLExportService


def push_reference(base_url, secret, source_instance, date_start=None, date_end=None):
    """Construit puis pousse un snapshot Noethys vers PMSL en prévisualisation."""
    client = PMSLNoethysBridgeClient(base_url, secret, source_instance)
    service = PMSLExportService()
    try:
        result = service.push(
            client,
            date_start=(date_start or None),
            date_end=(date_end or None),
        )
    finally:
        service.close()
    response = result.get("response") or {}
    payload = result.get("payload") or {}
    return {
        "response": response,
        "counts": payload.get("counts") or {},
        "filters": payload.get("filters") or {},
        "kind": payload.get("kind"),
        "version": payload.get("version"),
    }
