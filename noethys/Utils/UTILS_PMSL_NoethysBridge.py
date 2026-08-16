# -*- coding: utf-8 -*-
"""Client léger pour la passerelle native PMSL Équipe <-> Noethys.

Aucune dépendance externe : urllib + HMAC de la bibliothèque standard.
Le client ne modifie pas la base Noethys ; il transporte les lots et accusés.
"""
from __future__ import unicode_literals

import hashlib
import hmac
import json

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:  # pragma: no cover - compat Python 2 historique
    from urllib2 import Request, urlopen, HTTPError, URLError


class PMSLBridgeError(Exception):
    pass


class PMSLNoethysBridgeClient(object):
    PROTOCOL = "pmsl-noethys-native/1"

    def __init__(self, base_url, secret, source_instance, timeout=20):
        self.base_url = (base_url or "").rstrip("/")
        self.secret = secret or ""
        self.source_instance = source_instance or ""
        self.timeout = int(timeout)
        if not self.base_url:
            raise ValueError("base_url PMSL obligatoire")
        if len(self.secret) < 24:
            raise ValueError("secret PMSL trop court (24 caracteres minimum)")
        if not self.source_instance:
            raise ValueError("source_instance obligatoire")

    def pull(self, limit=20):
        """Récupère les lots sortants publiés par PMSL pour cette instance."""
        return self._post("pull", {
            "source_instance": self.source_instance,
            "limit": max(1, min(100, int(limit))),
        })

    def ack(self, batch_uuid, items):
        """Retourne à PMSL le résultat d'application d'un lot Noethys."""
        if not batch_uuid:
            raise ValueError("batch_uuid obligatoire")
        if not isinstance(items, list) or not items:
            raise ValueError("items doit etre une liste non vide")
        return self._post("ack", {"batch_uuid": batch_uuid, "items": items})

    def push(self, payload):
        """Envoie le référentiel/calendrier Noethys vers PMSL en prévisualisation."""
        if not isinstance(payload, dict):
            raise ValueError("payload doit etre un dictionnaire")
        return self._post("push", {
            "source_instance": self.source_instance,
            "payload": payload,
        })

    def _post(self, action, data):
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        key = self.secret.encode("utf-8") if not isinstance(self.secret, bytes) else self.secret
        signature = "sha256=" + hmac.new(key, body, hashlib.sha256).hexdigest()
        url = "%s/wp-json/pmsl-equipe/v1/noethys/%s" % (self.base_url, action)
        request = Request(url, data=body)
        request.add_header("Content-Type", "application/json; charset=utf-8")
        request.add_header("Accept", "application/json")
        request.add_header("X-PMSL-Signature", signature)
        try:
            response = urlopen(request, timeout=self.timeout)
            raw = response.read()
        except HTTPError as exc:
            raw = exc.read()
            raise PMSLBridgeError("HTTP %s: %s" % (exc.code, self._decode_error(raw)))
        except URLError as exc:
            raise PMSLBridgeError("Passerelle PMSL inaccessible: %s" % exc)
        try:
            decoded = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            result = json.loads(decoded)
        except (ValueError, UnicodeError) as exc:
            raise PMSLBridgeError("Réponse PMSL invalide: %s" % exc)
        if isinstance(result, dict) and result.get("code") and result.get("message"):
            raise PMSLBridgeError(result.get("message"))
        return result

    @staticmethod
    def _decode_error(raw):
        try:
            text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            data = json.loads(text)
            if isinstance(data, dict):
                return data.get("message") or text
            return text
        except Exception:
            try:
                return raw.decode("utf-8", "replace")
            except Exception:
                return str(raw)


def build_ack_item(action, state, opening_id=None, assignment_ids=None,
                   response=None, processed_at=None):
    """Construit un accusé conforme au contrat PMSL natif."""
    item = {
        "pmsl_ref": action.get("pmsl_ref"),
        "state": state,
        "response": response if isinstance(response, dict) else {},
    }
    if opening_id is not None:
        item["opening_id"] = int(opening_id)
    if assignment_ids:
        item["pmsl_assignment_ids"] = [int(value) for value in assignment_ids]
    if processed_at:
        item["processed_at"] = processed_at
    return item
