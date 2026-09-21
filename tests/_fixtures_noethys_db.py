# -*- coding: utf-8 -*-
"""Fixture d'une base Noethys SQLite temporaire pour les tests.

Construit un sous-ensemble du schema reel (via GestionDB.CreationTable +
Data.DATA_Tables, le schema canonique) et y insere des donnees
synthetiques et anonymisees, structurellement proches d'un cas reel de
convention d'encadrement sportif mais sans aucune donnee personnelle ou
associative reelle.

N'importe jamais depuis le dossier "references" (sauvegarde de recette
reelle, hors depot, jamais utilisee par les tests).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

NOETHYS_DIR = Path(__file__).resolve().parents[1] / "noethys"
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

import GestionDB  # noqa: E402
from Data import DATA_Tables as Tables  # noqa: E402

TABLES_REQUISES = (
    "organisateur", "familles", "individus", "rattachements",
    "activites", "groupes", "unites", "consommations", "prestations",
    "agrements", "documents_modeles", "documents_objets",
)


class BaseTest:
    """Cree une base SQLite temporaire, la detruit a la fermeture."""

    def __init__(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix="noethys-test-db-")
        self.chemin = str(Path(self._tmpdir.name) / "test.dat")
        self.db = GestionDB.DB(nomFichier=self.chemin, suffixe=None, modeCreation=True)
        for nom_table in TABLES_REQUISES:
            self.db.CreationTable(nom_table, dicoDB=Tables.DB_DATA)
        self.db.Commit()

    def inserer(self, table, colonnes, lignes):
        placeholders = ", ".join(colonnes)
        for ligne in lignes:
            valeurs = ", ".join(_sql_valeur(v) for v in ligne)
            self.db.ExecuterReq(
                "INSERT INTO %s (%s) VALUES (%s);" % (table, placeholders, valeurs)
            )
        self.db.Commit()

    def fermer(self):
        self.db.Close()
        self._tmpdir.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.fermer()


def _sql_valeur(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    texte = str(v).replace("'", "''")
    return "'%s'" % texte


def creer_base_association_simple():
    """Structure anonymisee proche d'Atout Sports : deux creneaux hebdo recurrents."""
    base = BaseTest()

    base.inserer(
        "organisateur",
        ["IDorganisateur", "nom", "rue", "cp", "ville", "tel", "mail"],
        [(1, "Association Test Loisirs", "1 rue des Tests", "00000", "Testville", "00.00.00.00.00", "test@example.org")],
    )
    base.inserer("familles", ["IDfamille"], [(1,)])
    base.inserer(
        "individus",
        ["IDindividu", "nom", "prenom", "IDcivilite"],
        [
            (1, "STRUCTURE SPORTIVE TEST", "", 3),
            (2, "STRUCTURE SPORTIVE TEST", "Groupe A enfants", 3),
            (3, "STRUCTURE SPORTIVE TEST", "Groupe B adultes", 3),
            (4, "DUPUIS", "Jean", 1),
        ],
    )
    base.inserer(
        "rattachements",
        ["IDrattachement", "IDfamille", "IDindividu", "IDcategorie", "titulaire"],
        [
            (1, 1, 1, 1, 1),
            (2, 1, 2, 2, 0),
            (3, 1, 3, 2, 0),
            (4, 1, 4, 1, 0),
        ],
    )
    base.inserer(
        "activites",
        ["IDactivite", "nom"],
        [(10, "Encadrement sportif enfants"), (11, "Encadrement sportif adultes")],
    )
    base.inserer(
        "groupes",
        ["IDgroupe", "IDactivite", "nom"],
        [(20, 10, "Enfants"), (21, 11, "Adultes")],
    )
    base.inserer(
        "unites",
        ["IDunite", "IDactivite", "nom", "ordre", "type"],
        [(30, 10, "Enfant", 1, "Horaire"), (31, 11, "Adulte", 1, "Horaire")],
    )

    lignes_conso = []
    lignes_prestation = []
    IDprestation = 100
    IDconso = 1000
    # Groupe A enfants : mercredi 17h30-19h00, 24 euros/h -> 36.00 la seance
    for jour in ("2026-09-02", "2026-09-09", "2026-09-16"):
        lignes_prestation.append((IDprestation, "Encadrement sportif enfants", 36.00))
        lignes_conso.append((IDconso, 2, 10, jour, 30, "17:30", "19:00", "reservation", 20, IDprestation))
        IDprestation += 1
        IDconso += 1
    # Groupe B adultes : lundi 19h30-20h30, 36.50 euros/h -> 36.50 la seance
    for jour in ("2026-09-07", "2026-09-14", "2026-09-21"):
        lignes_prestation.append((IDprestation, "Encadrement sportif adultes", 36.50))
        lignes_conso.append((IDconso, 3, 11, jour, 31, "19:30", "20:30", "reservation", 21, IDprestation))
        IDprestation += 1
        IDconso += 1

    base.inserer(
        "prestations",
        ["IDprestation", "label", "montant"],
        lignes_prestation,
    )
    base.inserer(
        "consommations",
        ["IDconso", "IDindividu", "IDactivite", "date", "IDunite", "heure_debut", "heure_fin", "etat", "IDgroupe", "IDprestation"],
        lignes_conso,
    )
    return base
