# -*- coding: utf-8 -*-
"""Application prudente des ouvertures PMSL dans Noethys.

Le service sépare strictement simulation et écriture. Il réutilise GestionDB,
valide groupe/unité/activité, garantit l'idempotence métier et renvoie un ack
compatible avec la passerelle native PMSL.
"""
from __future__ import unicode_literals

import datetime

from noethys import GestionDB
from noethys.Utils.UTILS_PMSL_NoethysBridge import build_ack_item


class PMSLOpeningError(Exception):
    pass


class PMSLOpeningService(object):
    def __init__(self, db=None):
        self.db = db or GestionDB.DB()
        self._owns_db = db is None

    def close(self):
        if self._owns_db and self.db:
            self.db.Close()
            self.db = None

    def preview_action(self, action):
        payload = action.get("payload") or {}
        if payload.get("action") != "upsert_opening":
            return self._result(action, "blocked", reason="action_not_supported")
        date_value = self._date(payload.get("date"))
        unit_id = self._positive_int(payload.get("IDunite"))
        group_id = self._positive_int(payload.get("IDgroupe"))
        if not date_value or not unit_id or not group_id:
            return self._result(action, "blocked", reason="opening_incomplete")

        unit = self._one("SELECT IDunite, IDactivite FROM unites WHERE IDunite=%d" % unit_id)
        group = self._one("SELECT IDgroupe, IDactivite FROM groupes WHERE IDgroupe=%d" % group_id)
        if not unit:
            return self._result(action, "blocked", reason="unit_missing")
        if not group:
            return self._result(action, "blocked", reason="group_missing")
        if int(unit[1]) != int(group[1]):
            return self._result(action, "blocked", reason="activity_mismatch",
                                detail={"unit_activity_id": int(unit[1]), "group_activity_id": int(group[1])})
        activity_id = int(unit[1])

        association = self._one("SELECT IDunite_groupe FROM unites_groupes WHERE IDunite=%d AND IDgroupe=%d" % (unit_id, group_id))
        if not association:
            return self._result(action, "blocked", reason="unit_group_not_linked")

        existing = self._one(
            "SELECT IDouverture FROM ouvertures WHERE IDactivite=%d AND IDunite=%d AND IDgroupe=%d AND date='%s'"
            % (activity_id, unit_id, group_id, date_value)
        )
        assignment_ids = self._assignment_ids(payload)
        base = {
            "date": date_value,
            "IDactivite": activity_id,
            "IDunite": unit_id,
            "IDgroupe": group_id,
            "pmsl_assignment_ids": assignment_ids,
        }
        if existing:
            base["IDouverture"] = int(existing[0])
            return self._result(action, "unchanged", detail=base)
        return self._result(action, "create", detail=base)

    def preview_batch(self, batch):
        actions = batch.get("actions") or []
        items = [self.preview_action(action) for action in actions]
        counts = {"create": 0, "unchanged": 0, "blocked": 0}
        for item in items:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        return {
            "batch_uuid": batch.get("batch_uuid"),
            "source_instance": batch.get("source_instance"),
            "valid": counts.get("blocked", 0) == 0,
            "counts": counts,
            "items": items,
            "aucune_ecriture_effectuee": True,
        }

    def apply_batch(self, batch):
        preview = self.preview_batch(batch)
        if not preview["valid"]:
            raise PMSLOpeningError("Lot PMSL bloque par la simulation")
        ack_items = []
        try:
            for action, item in zip(batch.get("actions") or [], preview["items"]):
                detail = item.get("detail") or {}
                if item["status"] == "unchanged":
                    opening_id = detail.get("IDouverture")
                elif item["status"] == "create":
                    opening_id = self.db.ReqInsert("ouvertures", [
                        ("IDactivite", detail["IDactivite"]),
                        ("IDunite", detail["IDunite"]),
                        ("IDgroupe", detail["IDgroupe"]),
                        ("date", detail["date"]),
                    ], commit=False)
                    if not opening_id:
                        raise PMSLOpeningError("Echec de creation d'une ouverture Noethys")
                else:
                    raise PMSLOpeningError("Etat de simulation inattendu: %s" % item["status"])
                ack_items.append(build_ack_item(
                    action,
                    "applied",
                    opening_id=opening_id,
                    assignment_ids=detail.get("pmsl_assignment_ids") or [],
                    response={
                        "IDouverture": int(opening_id),
                        "pmsl_assignment_ids": detail.get("pmsl_assignment_ids") or [],
                        "operation": item["status"],
                    },
                    processed_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ))
            self.db.Commit()
        except Exception:
            try:
                if getattr(self.db, "connexion", None):
                    self.db.connexion.rollback()
            except Exception:
                pass
            raise
        return {"preview": preview, "ack_items": ack_items}

    def _one(self, query):
        self.db.ExecuterReq(query)
        rows = self.db.ResultatReq()
        return rows[0] if rows else None

    @staticmethod
    def _positive_int(value):
        try:
            value = int(value)
            return value if value > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _date(value):
        if not value:
            return None
        try:
            datetime.datetime.strptime(str(value), "%Y-%m-%d")
            return str(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _assignment_ids(payload):
        values = payload.get("pmsl_assignment_ids") or []
        if not isinstance(values, list):
            values = []
        if not values and payload.get("pmsl_assignment_id"):
            values = [payload.get("pmsl_assignment_id")]
        result = []
        for value in values:
            try:
                value = int(value)
                if value > 0 and value not in result:
                    result.append(value)
            except (TypeError, ValueError):
                pass
        result.sort()
        return result

    @staticmethod
    def _result(action, status, reason=None, detail=None):
        return {
            "pmsl_ref": action.get("pmsl_ref"),
            "status": status,
            "reason": reason,
            "detail": detail or {},
        }
