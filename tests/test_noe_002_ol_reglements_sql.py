# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlite3
import unittest


OLD_QUERY = """
SELECT
    reglements.IDreglement, reglements.IDcompte_payeur, reglements.date,
    reglements.IDmode, modes_reglements.label,
    reglements.IDemetteur, emetteurs.nom,
    reglements.numero_piece, reglements.montant,
    payeurs.IDpayeur, payeurs.nom,
    reglements.observations, numero_quittancier, IDprestation_frais, reglements.IDcompte, date_differe,
    encaissement_attente,
    reglements.IDdepot, depots.date, depots.nom, depots.verrouillage,
    date_saisie, IDutilisateur,
    SUM(ventilation.montant) AS total_ventilation,
    reglements.IDprelevement,
    comptes_payeurs.IDfamille
FROM reglements
LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement
LEFT JOIN modes_reglements ON reglements.IDmode=modes_reglements.IDmode
LEFT JOIN emetteurs ON reglements.IDemetteur=emetteurs.IDemetteur
LEFT JOIN payeurs ON reglements.IDpayeur=payeurs.IDpayeur
LEFT JOIN depots ON reglements.IDdepot=depots.IDdepot
LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
GROUP BY reglements.IDreglement
ORDER BY reglements.IDreglement
"""

NEW_QUERY = """
SELECT
    reglements.IDreglement, reglements.IDcompte_payeur, reglements.date,
    reglements.IDmode, modes_reglements.label,
    reglements.IDemetteur, emetteurs.nom,
    reglements.numero_piece, reglements.montant,
    payeurs.IDpayeur, payeurs.nom,
    reglements.observations, numero_quittancier, IDprestation_frais, reglements.IDcompte, date_differe,
    encaissement_attente,
    reglements.IDdepot, depots.date, depots.nom, depots.verrouillage,
    date_saisie, IDutilisateur,
    ventilation_totaux.total_ventilation,
    reglements.IDprelevement,
    comptes_payeurs.IDfamille
FROM reglements
LEFT JOIN (
    SELECT IDreglement, SUM(montant) AS total_ventilation
    FROM ventilation
    GROUP BY IDreglement
) ventilation_totaux ON reglements.IDreglement = ventilation_totaux.IDreglement
LEFT JOIN modes_reglements ON reglements.IDmode=modes_reglements.IDmode
LEFT JOIN emetteurs ON reglements.IDemetteur=emetteurs.IDemetteur
LEFT JOIN payeurs ON reglements.IDpayeur=payeurs.IDpayeur
LEFT JOIN depots ON reglements.IDdepot=depots.IDdepot
LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
ORDER BY reglements.IDreglement
"""


class OLReglementsSQLTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE reglements (
                IDreglement INTEGER PRIMARY KEY,
                IDcompte_payeur INTEGER,
                date TEXT,
                IDmode INTEGER,
                IDemetteur INTEGER,
                numero_piece TEXT,
                montant REAL,
                IDpayeur INTEGER,
                observations TEXT,
                numero_quittancier TEXT,
                IDprestation_frais INTEGER,
                IDcompte INTEGER,
                date_differe TEXT,
                encaissement_attente INTEGER,
                IDdepot INTEGER,
                date_saisie TEXT,
                IDutilisateur INTEGER,
                IDprelevement INTEGER
            );
            CREATE TABLE ventilation (IDreglement INTEGER, montant REAL);
            CREATE TABLE modes_reglements (IDmode INTEGER PRIMARY KEY, label TEXT);
            CREATE TABLE emetteurs (IDemetteur INTEGER PRIMARY KEY, nom TEXT);
            CREATE TABLE payeurs (IDpayeur INTEGER PRIMARY KEY, nom TEXT);
            CREATE TABLE depots (IDdepot INTEGER PRIMARY KEY, date TEXT, nom TEXT, verrouillage INTEGER);
            CREATE TABLE comptes_payeurs (IDcompte_payeur INTEGER PRIMARY KEY, IDfamille INTEGER);
        """)
        self.db.execute("INSERT INTO modes_reglements VALUES (1, 'Carte')")
        self.db.execute("INSERT INTO emetteurs VALUES (2, 'Banque')")
        self.db.execute("INSERT INTO payeurs VALUES (3, 'Famille Test')")
        self.db.execute("INSERT INTO depots VALUES (4, '2026-08-19', 'Depot A', 0)")
        self.db.execute("INSERT INTO comptes_payeurs VALUES (10, 100)")
        self.db.execute("INSERT INTO comptes_payeurs VALUES (11, 101)")
        self.db.execute(
            "INSERT INTO reglements VALUES (1, 10, '2026-08-18', 1, 2, 'ABC', 20.0, 3, 'ok', 'Q1', NULL, 7, NULL, 0, 4, '2026-08-18', 9, NULL)"
        )
        self.db.execute(
            "INSERT INTO reglements VALUES (2, 11, '2026-08-19', 1, 2, 'DEF', 12.0, 3, '', 'Q2', NULL, 7, NULL, 0, NULL, '2026-08-19', 9, NULL)"
        )
        self.db.executemany(
            "INSERT INTO ventilation VALUES (?, ?)",
            [(1, 5.0), (1, 7.5), (1, 2.5)],
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_strict_query_preserves_legacy_result_shape_and_values(self):
        legacy = self.db.execute(OLD_QUERY).fetchall()
        strict = self.db.execute(NEW_QUERY).fetchall()
        self.assertEqual(legacy, strict)
        self.assertEqual(2, len(strict))
        self.assertEqual(26, len(strict[0]))
        self.assertEqual(15.0, strict[0][23])
        self.assertIsNone(strict[1][23])
        self.assertEqual(100, strict[0][25])
        self.assertEqual(101, strict[1][25])

    def test_strict_query_returns_one_row_per_reglement(self):
        rows = self.db.execute(NEW_QUERY).fetchall()
        self.assertEqual([1, 2], [row[0] for row in rows])


if __name__ == "__main__":
    unittest.main()
