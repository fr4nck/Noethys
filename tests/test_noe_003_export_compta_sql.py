# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlite3
import unittest


GET_VENTES_OLD = """
SELECT prestations.IDprestation, prestations.date, categorie, prestations.code_compta, tarifs.code_compta,
       prestations.label, prestations.montant,
       prestations.IDactivite, activites.nom, activites.abrege, activites.code_comptable, activites.code_analytique,
       prestations.IDtarif, noms_tarifs.nom, categories_tarifs.nom, prestations.IDfacture,
       prestations.forfait, prestations.IDcategorie_tarif,
       prestations.IDindividu, individus.nom, individus.prenom
FROM prestations
LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
LEFT JOIN tarifs ON prestations.IDtarif = tarifs.IDtarif
LEFT JOIN noms_tarifs ON tarifs.IDnom_tarif = noms_tarifs.IDnom_tarif
LEFT JOIN categories_tarifs ON prestations.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
WHERE prestations.date >= '2026-08-01' AND prestations.date <= '2026-08-31'
GROUP BY prestations.IDprestation
ORDER BY prestations.date
"""

GET_VENTES_STRICT = GET_VENTES_OLD.replace("GROUP BY prestations.IDprestation\n", "")

REGLEMENTS_MODES_OLD = """
SELECT reglements.IDreglement, reglements.IDcompte_payeur, reglements.date,
       reglements.IDmode, modes_reglements.label,
       reglements.numero_piece, reglements.montant,
       payeurs.IDpayeur, payeurs.nom,
       numero_quittancier, reglements.IDcompte, date_differe,
       encaissement_attente,
       reglements.IDdepot, depots.date, depots.nom,
       date_saisie, comptes_payeurs.IDfamille,
       modes_reglements.code_compta,
       comptes_bancaires.numero, comptes_bancaires.nom
FROM reglements
LEFT JOIN modes_reglements ON reglements.IDmode=modes_reglements.IDmode
LEFT JOIN payeurs ON reglements.IDpayeur=payeurs.IDpayeur
LEFT JOIN depots ON reglements.IDdepot=depots.IDdepot
LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = reglements.IDcompte
WHERE reglements.date >= '2026-08-01' AND reglements.date <= '2026-08-31'
GROUP BY reglements.IDreglement
ORDER BY modes_reglements.label
"""

REGLEMENTS_MODES_STRICT = REGLEMENTS_MODES_OLD.replace("GROUP BY reglements.IDreglement\n", "")

DEPOTS_OLD = """
SELECT depots.IDdepot, depots.date, depots.nom, depots.code_compta,
       reglements.IDmode, modes_reglements.label, modes_reglements.type_comptable,
       SUM(reglements.montant), COUNT(reglements.IDreglement),
       comptes_bancaires.numero, comptes_bancaires.nom
FROM depots
LEFT JOIN reglements ON reglements.IDdepot = depots.IDdepot
LEFT JOIN modes_reglements ON modes_reglements.IDmode = reglements.IDmode
LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = depots.IDcompte
WHERE depots.date >= '2026-08-01' AND depots.date <= '2026-08-31'
  AND modes_reglements.type_comptable = 'banque'
GROUP BY depots.IDdepot, reglements.IDmode
ORDER BY depots.date
"""

DEPOTS_STRICT = """
SELECT depots.IDdepot, depots.date, depots.nom, depots.code_compta,
       reglements_totaux.IDmode, modes_reglements.label, modes_reglements.type_comptable,
       reglements_totaux.montant, reglements_totaux.nbre_reglements,
       comptes_bancaires.numero, comptes_bancaires.nom
FROM depots
LEFT JOIN (
    SELECT IDdepot, IDmode, SUM(montant) AS montant, COUNT(IDreglement) AS nbre_reglements
    FROM reglements
    GROUP BY IDdepot, IDmode
) reglements_totaux ON reglements_totaux.IDdepot = depots.IDdepot
LEFT JOIN modes_reglements ON modes_reglements.IDmode = reglements_totaux.IDmode
LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = depots.IDcompte
WHERE depots.date >= '2026-08-01' AND depots.date <= '2026-08-31'
  AND modes_reglements.type_comptable = 'banque'
ORDER BY depots.date
"""

COTISATIONS_JOIN = """
SELECT prestations.IDprestation, types_cotisations.code_comptable
FROM prestations
LEFT JOIN cotisations ON cotisations.IDprestation = prestations.IDprestation
LEFT JOIN types_cotisations ON types_cotisations.IDtype_cotisation = cotisations.IDtype_cotisation
WHERE prestations.IDprestation = 1
"""


class ExportComptaSQLTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE prestations (
                IDprestation INTEGER PRIMARY KEY,
                date TEXT,
                categorie TEXT,
                code_compta TEXT,
                label TEXT,
                montant REAL,
                IDactivite INTEGER,
                IDtarif INTEGER,
                IDfacture INTEGER,
                forfait INTEGER,
                IDcategorie_tarif INTEGER,
                IDindividu INTEGER
            );
            CREATE TABLE activites (
                IDactivite INTEGER PRIMARY KEY,
                nom TEXT,
                abrege TEXT,
                code_comptable TEXT,
                code_analytique TEXT
            );
            CREATE TABLE individus (IDindividu INTEGER PRIMARY KEY, nom TEXT, prenom TEXT);
            CREATE TABLE tarifs (IDtarif INTEGER PRIMARY KEY, IDnom_tarif INTEGER, code_compta TEXT);
            CREATE TABLE noms_tarifs (IDnom_tarif INTEGER PRIMARY KEY, nom TEXT);
            CREATE TABLE categories_tarifs (IDcategorie_tarif INTEGER PRIMARY KEY, nom TEXT);

            CREATE TABLE reglements (
                IDreglement INTEGER PRIMARY KEY,
                IDcompte_payeur INTEGER,
                date TEXT,
                IDmode INTEGER,
                numero_piece TEXT,
                montant REAL,
                IDpayeur INTEGER,
                numero_quittancier TEXT,
                IDcompte INTEGER,
                date_differe TEXT,
                encaissement_attente INTEGER,
                IDdepot INTEGER,
                date_saisie TEXT
            );
            CREATE TABLE modes_reglements (
                IDmode INTEGER PRIMARY KEY,
                label TEXT,
                code_compta TEXT,
                type_comptable TEXT
            );
            CREATE TABLE payeurs (IDpayeur INTEGER PRIMARY KEY, nom TEXT);
            CREATE TABLE depots (
                IDdepot INTEGER PRIMARY KEY,
                date TEXT,
                nom TEXT,
                code_compta TEXT,
                IDcompte INTEGER
            );
            CREATE TABLE comptes_payeurs (IDcompte_payeur INTEGER PRIMARY KEY, IDfamille INTEGER);
            CREATE TABLE comptes_bancaires (IDcompte INTEGER PRIMARY KEY, numero TEXT, nom TEXT);

            CREATE TABLE cotisations (
                IDcotisation INTEGER PRIMARY KEY,
                IDprestation INTEGER,
                IDtype_cotisation INTEGER
            );
            CREATE TABLE types_cotisations (
                IDtype_cotisation INTEGER PRIMARY KEY,
                code_comptable TEXT
            );
        """)

        self.db.execute("INSERT INTO activites VALUES (1, 'Gym', 'GYM', '7061', 'A1')")
        self.db.execute("INSERT INTO individus VALUES (1, 'DUPONT', 'Alice')")
        self.db.execute("INSERT INTO noms_tarifs VALUES (1, 'Normal')")
        self.db.execute("INSERT INTO tarifs VALUES (1, 1, '7062')")
        self.db.execute("INSERT INTO categories_tarifs VALUES (1, 'Adulte')")
        self.db.execute("INSERT INTO prestations VALUES (1, '2026-08-10', 'conso', '7060', 'Seance', 12.0, 1, 1, 10, 0, 1, 1)")
        self.db.execute("INSERT INTO prestations VALUES (2, '2026-08-11', 'conso', NULL, 'Seance 2', 8.0, 1, 1, 10, 0, 1, 1)")

        self.db.execute("INSERT INTO modes_reglements VALUES (1, 'Carte', '5121', 'banque')")
        self.db.execute("INSERT INTO payeurs VALUES (1, 'Famille Test')")
        self.db.execute("INSERT INTO comptes_payeurs VALUES (10, 100)")
        self.db.execute("INSERT INTO comptes_bancaires VALUES (7, '123', 'Compte courant')")
        self.db.execute("INSERT INTO depots VALUES (5, '2026-08-15', 'Depot A', '5112', 7)")
        self.db.execute("INSERT INTO reglements VALUES (1, 10, '2026-08-10', 1, 'R1', 20.0, 1, 'Q1', 7, NULL, 0, 5, '2026-08-10')")
        self.db.execute("INSERT INTO reglements VALUES (2, 10, '2026-08-11', 1, 'R2', 15.0, 1, 'Q2', 7, NULL, 0, 5, '2026-08-11')")

        self.db.execute("INSERT INTO types_cotisations VALUES (1, '7561')")
        self.db.execute("INSERT INTO types_cotisations VALUES (2, '7562')")
        self.db.execute("INSERT INTO cotisations VALUES (1, 1, 1)")
        self.db.execute("INSERT INTO cotisations VALUES (2, 1, 2)")
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_get_ventes_group_by_is_redundant_with_primary_key_joins(self):
        legacy = self.db.execute(GET_VENTES_OLD).fetchall()
        strict = self.db.execute(GET_VENTES_STRICT).fetchall()
        self.assertEqual(legacy, strict)
        self.assertEqual(2, len(strict))

    def test_reglements_modes_group_by_is_redundant_with_primary_key_joins(self):
        legacy = self.db.execute(REGLEMENTS_MODES_OLD).fetchall()
        strict = self.db.execute(REGLEMENTS_MODES_STRICT).fetchall()
        self.assertEqual(legacy, strict)
        self.assertEqual(2, len(strict))

    def test_depots_subquery_preserves_grouped_result(self):
        legacy = self.db.execute(DEPOTS_OLD).fetchall()
        strict = self.db.execute(DEPOTS_STRICT).fetchall()
        self.assertEqual(legacy, strict)
        self.assertEqual(1, len(strict))
        self.assertEqual(35.0, strict[0][7])
        self.assertEqual(2, strict[0][8])

    def test_cotisations_join_can_duplicate_a_prestation(self):
        rows = self.db.execute(COTISATIONS_JOIN).fetchall()
        self.assertEqual(2, len(rows))
        self.assertEqual({"7561", "7562"}, {row[1] for row in rows})


if __name__ == "__main__":
    unittest.main()
