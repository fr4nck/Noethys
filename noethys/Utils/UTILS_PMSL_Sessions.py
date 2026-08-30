# -*- coding: utf-8 -*-
"""Export des séances canoniques Noethys vers le contrat ``noethys-session/1``."""
from __future__ import unicode_literals

try:
    from noethys.Utils import UTILS_Interventions
    from noethys.Utils import UTILS_Interventions_Execution
except ImportError:  # lancement historique depuis le répertoire noethys
    from Utils import UTILS_Interventions
    from Utils import UTILS_Interventions_Execution


class PMSLSessionExportService(object):
    def __init__(self, db):
        self.db = db
        self.interventions = UTILS_Interventions.GestionnaireInterventions(db)
        self.execution = UTILS_Interventions_Execution.GestionnaireExecutionInterventions(db)

    def build_interventions(self, date_start=None, date_end=None, actifs_seulement=True):
        conditions = []
        if date_start:
            conditions.append("date>='%s'" % self._safe_date(date_start))
        if date_end:
            conditions.append("date<='%s'" % self._safe_date(date_end))
        if actifs_seulement:
            conditions.append("actif=1")
        req = "SELECT IDintervention FROM interventions"
        if conditions:
            req += " WHERE " + " AND ".join(conditions)
        req += " ORDER BY date, heure_debut, IDintervention;"
        if self.db.ExecuterReq(req) != 1:
            return []
        ids = [int(row[0]) for row in (self.db.ResultatReq() or [])]
        return [self.execution.ConstruireInterventionEchange(IDintervention) for IDintervention in ids]

    @staticmethod
    def _safe_date(value):
        value = str(value)
        if len(value) != 10 or value[4] != '-' or value[7] != '-':
            raise ValueError("date invalide: %s" % value)
        y, m, d = value.split('-')
        int(y), int(m), int(d)
        return value
