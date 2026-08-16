# -*- coding: utf-8 -*-
"""Export lecture seule Noethys -> PMSL Équipe.

Construit un payload stable et minimal : activités, unités, groupes et ouvertures.
Aucune écriture locale n'est effectuée ; l'envoi se fait via le endpoint natif /push
qui crée uniquement un lot entrant en prévisualisation côté PMSL.
"""
from __future__ import unicode_literals

try:
    from noethys import GestionDB
except ImportError:  # lancement historique depuis le répertoire noethys
    import GestionDB


class PMSLExportService(object):
    def __init__(self, db=None):
        self.db = db or GestionDB.DB()
        self._owns_db = db is None

    def close(self):
        if self._owns_db and self.db:
            self.db.Close()
            self.db = None

    def build_payload(self, date_start=None, date_end=None):
        activities = self._rows("SELECT IDactivite, nom FROM activites ORDER BY IDactivite")
        units = self._rows("SELECT IDunite, IDactivite, nom FROM unites ORDER BY IDunite")
        groups = self._rows("SELECT IDgroupe, IDactivite, nom FROM groupes ORDER BY IDgroupe")

        where = []
        if date_start:
            where.append("date>='%s'" % self._safe_date(date_start))
        if date_end:
            where.append("date<='%s'" % self._safe_date(date_end))
        query = "SELECT IDouverture, IDactivite, IDunite, IDgroupe, date FROM ouvertures"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY date, IDouverture"
        openings = self._rows(query)

        return {
            "kind": "noethys_reference_calendar",
            "version": 1,
            "filters": {"date_start": date_start, "date_end": date_end},
            "activities": [
                {"IDactivite": int(row[0]), "nom": row[1]} for row in activities
            ],
            "units": [
                {"IDunite": int(row[0]), "IDactivite": int(row[1]), "nom": row[2]} for row in units
            ],
            "groups": [
                {"IDgroupe": int(row[0]), "IDactivite": int(row[1]), "nom": row[2]} for row in groups
            ],
            "openings": [
                {
                    "IDouverture": int(row[0]),
                    "IDactivite": int(row[1]),
                    "IDunite": int(row[2]),
                    "IDgroupe": int(row[3]),
                    "date": str(row[4]),
                }
                for row in openings
            ],
            "counts": {
                "activities": len(activities),
                "units": len(units),
                "groups": len(groups),
                "openings": len(openings),
            },
        }

    def push(self, client, date_start=None, date_end=None):
        payload = self.build_payload(date_start=date_start, date_end=date_end)
        response = client.push(payload)
        return {"payload": payload, "response": response}

    def _rows(self, query):
        self.db.ExecuterReq(query)
        return self.db.ResultatReq() or []

    @staticmethod
    def _safe_date(value):
        value = str(value)
        if len(value) != 10 or value[4] != '-' or value[7] != '-':
            raise ValueError("date invalide: %s" % value)
        y, m, d = value.split('-')
        int(y), int(m), int(d)
        return value
