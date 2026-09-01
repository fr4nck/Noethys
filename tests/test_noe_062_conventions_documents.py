# -*- coding: utf-8 -*-
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))


def _charger(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _charger(
    "tests/test_noe_062_conventions_avenants.py",
    "test_noe_062_conventions_avenants_base_documents",
)
DOCS = _charger(
    "noethys/Utils/UTILS_Conventions_Structures_Documents.py",
    "UTILS_Conventions_Structures_Documents_test",
)
REL = _charger(
    "noethys/Utils/UTILS_Relations_Structures.py",
    "UTILS_Relations_Structures_documents_test",
)


def _creer_documentable(db, avec_payeur=False):
    IDrelation = BASE._creer_relation(db)
    db.conn.execute(
        "UPDATE structures SET nom=?, nom_officiel=?, rue=?, cp=?, ville=?, mail=?, siret=? WHERE IDstructure=1",
        (
            "Club documentable",
            "Club documentable officiel",
            "1 rue du Stade",
            "35130",
            "La Guerche-de-Bretagne",
            "club@example.test",
            "12345678900011",
        ),
    )
    db.conn.commit()

    if avec_payeur:
        db.ReqInsert(
            "structures",
            [
                ("uid", "STR-payeur-doc"),
                ("type_structure", "mairie_collectivite"),
                ("nom", "Mairie financeuse"),
                ("nom_officiel", "Commune de Test"),
                ("rue", "2 place de la Mairie"),
                ("cp", "35130"),
                ("ville", "La Guerche-de-Bretagne"),
                ("actif", 1),
                ("date_creation", "2026-09-01"),
                ("date_modification", "2026-09-01"),
            ],
        )
        relations = REL.GestionnaireRelationsStructures(db)
        relations.CreerPayeur(
            {
                "IDrelation_structure": IDrelation,
                "type_payeur": "structure",
                "IDstructure_payeur": 2,
                "taux_prise_en_charge": 75,
                "reference": "BC-DOC-001",
            },
            date="2026-09-02",
        )

    gestion = DOCS.GestionnaireConventionsDocumentaires(db)
    IDconv = gestion.CreerConvention(
        {
            "uid": "CONV-DOC-001",
            "IDrelation_structure": IDrelation,
            "reference": "MAD-DOC-001",
            "date_debut": "2026-09-01",
            "date_fin": "2027-08-31",
            "objet": "Mise à disposition documentable",
        },
        date="2026-09-01",
    )
    return gestion, IDrelation, IDconv


def test_validation_documentaire_fige_beneficiaire_groupe_et_payeur():
    db = BASE._preparer_base()
    gestion, IDrelation, IDconv = _creer_documentable(db, avec_payeur=True)
    assert gestion.ValiderConvention(
        IDconv,
        complements={
            "contact_convention": {
                "nom": "Martin",
                "prenom": "Alice",
                "fonction": "Présidente",
                "mail": "alice@example.test",
            }
        },
        date="2026-09-03",
    ) is True

    snapshot = gestion.LireSnapshot(IDconv)
    assert snapshot["schema"] == DOCS.SCHEMA_SNAPSHOT_DOCUMENTABLE
    assert snapshot["beneficiaire"]["uid"] == "STR-benef"
    assert snapshot["beneficiaire"]["nom"] == "Club documentable"
    assert snapshot["beneficiaire"]["siret"] == "12345678900011"
    assert snapshot["payeurs"][0]["libelle_document"] == "Mairie financeuse"
    assert snapshot["payeurs"][0]["structure"]["uid"] == "STR-payeur-doc"


def test_document_regenere_reste_identique_apres_mutations_des_referentiels():
    db = BASE._preparer_base()
    gestion, IDrelation, IDconv = _creer_documentable(db, avec_payeur=True)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    premier = gestion.ConstruirePaquetDocumentaire(IDconv)

    db.conn.execute("UPDATE structures SET nom='NOM CHANGE', rue='99 rue Nouvelle' WHERE IDstructure=1")
    db.conn.execute("UPDATE structures SET nom='PAYEUR CHANGE' WHERE IDstructure=2")
    db.conn.execute("UPDATE structures_relations SET tarif=999, regle_adhesion='exoneree' WHERE IDrelation_structure=?", (IDrelation,))
    db.conn.execute("UPDATE structures_payeurs SET taux_prise_en_charge=12 WHERE IDrelation_structure=?", (IDrelation,))
    db.conn.commit()

    second = gestion.ConstruirePaquetDocumentaire(IDconv)
    assert second["champs"] == premier["champs"]
    assert second["snapshot_sha256"] == premier["snapshot_sha256"]
    assert second["empreinte_paquet_sha256"] == premier["empreinte_paquet_sha256"]
    assert second["champs"]["{BENEFICIAIRE_NOM}"] == "Club documentable"
    assert second["champs"]["{PAYEUR_NOM}"] == "Mairie financeuse"
    assert second["champs"]["{RELATION_TARIF}"] == "44"
    assert second["champs"]["{RELATION_REGLE_ADHESION}"] == "requise"


def test_brouillon_et_annule_ne_produisent_pas_document_officiel():
    db = BASE._preparer_base()
    gestion, IDrelation, IDconv = _creer_documentable(db)
    try:
        gestion.ConstruirePaquetDocumentaire(IDconv)
        assert False, "document officiel produit depuis un brouillon"
    except ValueError as err:
        assert "documentable" in str(err)

    gestion.AnnulerConvention(IDconv, date="2026-09-02")
    try:
        gestion.ConstruirePaquetDocumentaire(IDconv)
        assert False, "document officiel produit depuis une convention annulée"
    except ValueError as err:
        assert "documentable" in str(err)


def test_snapshot_altere_bloque_le_document():
    db = BASE._preparer_base()
    gestion, IDrelation, IDconv = _creer_documentable(db)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    db.conn.execute(
        "UPDATE structures_conventions SET snapshot_contractuel=? WHERE IDconvention_structure=?",
        (b'{"schema":"altered"}', IDconv),
    )
    db.conn.commit()
    try:
        gestion.ConstruirePaquetDocumentaire(IDconv)
        assert False, "snapshot altéré accepté"
    except ValueError as err:
        assert "Intégrité" in str(err)


def test_avenant_produit_un_type_document_avenant():
    db = BASE._preparer_base()
    gestion, IDrelation, IDconv = _creer_documentable(db)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    gestion.SignerConvention(IDconv, date="2026-09-04")
    IDavenant = gestion.CreerAvenant(
        IDconv,
        {
            "uid": "CONV-DOC-001-A1",
            "reference": "MAD-DOC-001-A1",
            "date_debut": "2027-01-01",
            "date_fin": "2027-08-31",
            "objet": "Avenant horaire",
        },
        date="2026-12-15",
    )
    gestion.ValiderConvention(IDavenant, date="2026-12-16")
    paquet = gestion.ConstruirePaquetDocumentaire(IDavenant)
    assert paquet["type_document"] == DOCS.DOCUMENT_AVENANT
    assert paquet["champs"]["{DOCUMENT_EST_AVENANT}"] == "1"
    assert paquet["champs"]["{CONVENTION_VERSION}"] == "2"
    assert paquet["champs"]["{CONVENTION_PARENT_ID}"] == str(IDconv)


def test_annexe_est_triee_dedupliquee_et_necrit_rien_en_base():
    db = BASE._preparer_base()
    gestion, IDrelation, IDconv = _creer_documentable(db)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    commits_avant = db.commits
    lignes = [
        {
            "identifiant_stable": "SEANCE-2",
            "date": "2026-09-09",
            "heure_debut": "10:30",
            "heure_fin": "11:15",
            "duree_minutes": 45,
            "groupe": "Groupe 1",
            "lieu": "Salle A",
        },
        {
            "identifiant_stable": "SEANCE-1",
            "date": "2026-09-02",
            "heure_debut": "10:30",
            "heure_fin": "11:15",
            "duree_minutes": 45,
            "groupe": "Groupe 1",
            "lieu": "Salle A",
        },
        {
            "identifiant_stable": "SEANCE-1",
            "date": "2026-09-02",
            "heure_debut": "10:30",
            "heure_fin": "11:15",
            "duree_minutes": 45,
            "groupe": "Groupe 1",
            "lieu": "Salle A",
        },
    ]
    paquet = gestion.ConstruirePaquetDocumentaire(IDconv, lignes_annexe=lignes)
    assert db.commits == commits_avant
    assert len(paquet["lignes_annexe"]) == 2
    assert paquet["lignes_annexe"][0]["identifiant_stable"] == "SEANCE-1"
    assert paquet["lignes_annexe"][1]["identifiant_stable"] == "SEANCE-2"
    assert paquet["champs"]["{ANNEXE_NB_SEANCES}"] == "2"
    assert paquet["champs"]["{ANNEXE_DUREE_TOTALE_MINUTES}"] == "90"


def test_plusieurs_payeurs_ninventent_pas_un_payeur_unique():
    db = BASE._preparer_base()
    gestion, IDrelation, IDconv = _creer_documentable(db, avec_payeur=True)
    db.ReqInsert(
        "structures",
        [
            ("uid", "STR-payeur-doc-2"),
            ("type_structure", "financeur"),
            ("nom", "Financeur B"),
            ("actif", 1),
            ("date_creation", "2026-09-01"),
            ("date_modification", "2026-09-01"),
        ],
    )
    relations = REL.GestionnaireRelationsStructures(db)
    relations.CreerPayeur(
        {
            "IDrelation_structure": IDrelation,
            "type_payeur": "structure",
            "IDstructure_payeur": 3,
            "taux_prise_en_charge": 25,
            "reference": "COFIN-002",
        },
        date="2026-09-02",
    )
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    paquet = gestion.ConstruirePaquetDocumentaire(IDconv)
    assert paquet["champs"]["{PAYEURS_NOMBRE}"] == "2"
    assert paquet["champs"]["{PAYEUR_NOM}"] == ""
    assert "Mairie financeuse" in paquet["champs"]["{PAYEURS_LIGNES_TEXTE}"]
    assert "Financeur B" in paquet["champs"]["{PAYEURS_LIGNES_TEXTE}"]


def test_snapshot_v1_reste_lisible_par_le_formateur():
    snapshot = {
        "schema": "noe-062-convention-v1",
        "convention": {
            "uid": "CONV-V1",
            "version": 1,
            "reference": "OLD",
            "date_debut": "2026-09-01",
            "date_fin": "2027-08-31",
        },
        "relation": {"uid": "REL-V1", "tarif": 44, "unite_tarif": "heure"},
        "payeurs": [],
    }
    convention = {
        "statut": "validee",
        "date_validation": "2026-09-03",
        "date_signature": None,
        "empreinte_sha256": "x" * 64,
    }
    champs, annexe = DOCS.ConstruireChampsFusion(snapshot, convention)
    assert champs["{DOCUMENT_SNAPSHOT_SCHEMA}"] == "noe-062-convention-v1"
    assert champs["{CONVENTION_REFERENCE}"] == "OLD"
    assert champs["{BENEFICIAIRE_NOM}"] == ""
    assert annexe == []
