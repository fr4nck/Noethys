# -*- coding: utf-8 -*-
"""Point d'entrée UI pour le flux retour Noethys -> PMSL."""
from __future__ import unicode_literals

try:
    from noethys.Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient, PMSLBridgeError
    from noethys.Utils.UTILS_PMSL_Export import PMSLExportService
except ImportError:  # lancement historique depuis le répertoire noethys
    from Utils.UTILS_PMSL_NoethysBridge import PMSLNoethysBridgeClient, PMSLBridgeError
    from Utils.UTILS_PMSL_Export import PMSLExportService


def _validate_preview_response(response):
    """Refuse tout retour PMSL qui ne garantit pas explicitement la prévisualisation."""
    if not isinstance(response, dict):
        raise PMSLBridgeError("Réponse PMSL invalide pour le flux retour.")
    if not response.get("accepted"):
        raise PMSLBridgeError("PMSL n'a pas accepté le référentiel Noethys.")
    if response.get("status") != "preview":
        raise PMSLBridgeError("PMSL n'a pas confirmé le statut preview du lot entrant.")
    if response.get("requires_human_validation") is not True:
        raise PMSLBridgeError("PMSL n'a pas confirmé la validation humaine obligatoire.")
    if not response.get("batch_uuid"):
        raise PMSLBridgeError("PMSL n'a pas renvoyé de batch_uuid pour le lot entrant.")
    return response


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
    response = _validate_preview_response(result.get("response") or {})
    payload = result.get("payload") or {}
    return {
        "response": response,
        "counts": payload.get("counts") or {},
        "filters": payload.get("filters") or {},
        "kind": payload.get("kind"),
        "version": payload.get("version"),
    }
