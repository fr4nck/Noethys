# -*- coding: utf-8 -*-
import datetime
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _charger():
    path = ROOT / "noethys" / "Utils" / "UTILS_Locations_Recurrence.py"
    spec = importlib.util.spec_from_file_location("UTILS_Locations_Recurrence_test", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REC = _charger()


class FauxDB(object):
    def __init__(self, vacances=None, feries=None):
        self.vacances = list(vacances or [])
        self.feries = list(feries or [])
        self.resultat = []
        self.requetes = []
        self.fermee = False

    def ExecuterReq(self, req):
        self.requetes.append(req)
        if "FROM vacances" in req:
            self.resultat = self.vacances
        elif "FROM jours_feries" in req:
            self.resultat = self.feries
        else:
            raise AssertionError("requête inattendue: %s" % req)
        return 1

    def ResultatReq(self):
        return list(self.resultat)

    def Close(self):
        self.fermee = True


def _regle(debut, fin, **kwargs):
    donnees = {
        "date_debut": debut,
        "date_fin": fin,
        "heure_debut": "10:30",
        "heure_fin": "11:15",
        "jours_vacances": [],
        "jours_scolaires": [0],
        "semaines": 1,
        "feries": False,
    }
    donnees.update(kwargs)
    return donnees


def _dates(resultats):
    return [item["date_debut"].date().isoformat() for item in resultats]


def test_toutes_les_semaines_conserve_horaires_et_bornes_inclusives():
    resultats = REC.CalculerOccurrences(
        _regle(datetime.date(2026, 9, 7), datetime.date(2026, 9, 21)),
        calendrier=([], []),
    )
    assert _dates(resultats) == ["2026-09-07", "2026-09-14", "2026-09-21"]
    assert resultats[0]["date_debut"].time() == datetime.time(10, 30)
    assert resultats[0]["date_fin"].time() == datetime.time(11, 15)


def test_vacances_bascule_du_jeu_scolaire_vers_le_jeu_vacances():
    vacances = [("2026-10-19", "2026-11-01", "Toussaint", "2026")]
    regle = _regle(
        datetime.date(2026, 10, 12),
        datetime.date(2026, 10, 26),
        jours_scolaires=[0],
        jours_vacances=[],
    )
    assert _dates(REC.CalculerOccurrences(regle, calendrier=(vacances, []))) == ["2026-10-12"]

    regle["jours_vacances"] = [0]
    assert _dates(REC.CalculerOccurrences(regle, calendrier=(vacances, []))) == [
        "2026-10-12",
        "2026-10-19",
        "2026-10-26",
    ]


def test_ferie_fixe_est_exclu_ou_inclus_selon_le_drapeau_historique():
    feries = [("fixe", "Jour de l'an", 1, 1, 0)]
    regle = _regle(
        datetime.date(2027, 1, 1),
        datetime.date(2027, 1, 1),
        jours_scolaires=[4],
        feries=False,
    )
    assert REC.CalculerOccurrences(regle, calendrier=([], feries)) == []
    regle["feries"] = True
    assert _dates(REC.CalculerOccurrences(regle, calendrier=([], feries))) == ["2027-01-01"]


def test_frequence_une_semaine_sur_deux_preserve_le_compteur_historique():
    resultats = REC.CalculerOccurrences(
        _regle(
            datetime.date(2026, 9, 7),
            datetime.date(2026, 9, 28),
            semaines=2,
        ),
        calendrier=([], []),
    )
    assert _dates(resultats) == ["2026-09-07", "2026-09-21"]


def test_codes_5_et_6_restent_semaines_iso_paires_et_impaires():
    paire = REC.CalculerOccurrences(
        _regle(
            datetime.date(2026, 9, 7),
            datetime.date(2026, 9, 14),
            semaines=5,
        ),
        calendrier=([], []),
    )
    impaire = REC.CalculerOccurrences(
        _regle(
            datetime.date(2026, 9, 7),
            datetime.date(2026, 9, 14),
            semaines=6,
        ),
        calendrier=([], []),
    )
    assert _dates(paire) == ["2026-09-14"]  # semaine ISO 38
    assert _dates(impaire) == ["2026-09-07"]  # semaine ISO 37


def test_db_injectee_est_utilisee_sans_etre_fermee_par_le_moteur():
    db = FauxDB(
        vacances=[("2026-10-19", "2026-11-01", "Toussaint", "2026")],
        feries=[],
    )
    REC.CalculerOccurrences(
        _regle(datetime.date(2026, 10, 12), datetime.date(2026, 10, 19)),
        DB=db,
    )
    assert len(db.requetes) == 2
    assert db.fermee is False


def test_alias_noe_062_utilise_exactement_le_meme_moteur():
    regle = _regle(datetime.date(2026, 9, 7), datetime.date(2026, 9, 21))
    normal = REC.CalculerOccurrences(regle, calendrier=([], []))
    annexe = REC.CalculerOccurrencesAnnexe(regle, calendrier=([], []))
    assert annexe == normal


def test_dialog_locations_delegue_au_moteur_commun_sans_sql_duplique():
    source = (ROOT / "noethys" / "Dlg" / "DLG_Saisie_location.py").read_text(encoding="utf-8")
    debut = source.index("    def Calcule_occurences(self, dictDonnees={})")
    fin = source.index("\n\n\nif __name__", debut)
    methode = source[debut:fin]
    assert "UTILS_Locations_Recurrence.CalculerOccurrences(dictDonnees)" in methode
    assert "SELECT date_debut, date_fin, nom, annee FROM vacances" not in methode
    assert "SELECT type, nom, jour, mois, annee FROM jours_feries" not in methode
