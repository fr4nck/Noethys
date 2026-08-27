# -*- coding: utf-8 -*-
import datetime
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _charger_module(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TIERS = _charger_module("noethys/Utils/UTILS_Tiers.py", "UTILS_Tiers_noe062a")
SCHEMA = _charger_module("noethys/Data/DATA_Structures.py", "DATA_Structures_noe062a")


class FakeDB(object):
    def __init__(self):
        self.insertions = []
        self.maj = []
        self.requetes = []
        self.resultats = []

    def ReqInsert(self, table, donnees, commit=True):
        self.insertions.append((table, list(donnees), commit))
        return 42

    def ReqMAJ(self, table, donnees, cle, ID, IDestChaine=False, commit=True):
        self.maj.append((table, list(donnees), cle, ID, commit))
        return True

    def ExecuterReq(self, req):
        self.requetes.append(req)
        return 1

    def ResultatReq(self):
        return list(self.resultats)


def test_schema_structure_contient_uid_et_dates():
    champs = SCHEMA.GetChamps("structures")
    assert champs[0] == "IDstructure"
    assert "uid" in champs
    assert "type_structure" in champs
    assert "nom" in champs
    assert "date_creation" in champs
    assert "date_modification" in champs


def test_schema_contacts_et_relations_restent_additifs():
    noms = SCHEMA.GetNomsTables()
    assert "structures" in noms
    assert "structures_contacts" in noms
    assert "structures_relations" in noms
    assert "structures_payeurs" in noms


def test_normalisation_structure_cree_uid_stable_et_dates():
    date = datetime.date(2026, 8, 27)
    data = TIERS.NormaliserStructure({
        "type_structure": "association",
        "nom": "  Club test  ",
        "mail": " contact@example.org ",
    }, date=date, creation=True)

    assert data["uid"].startswith("STR-")
    assert len(data["uid"]) > 10
    assert data["nom"] == "Club test"
    assert data["mail"] == "contact@example.org"
    assert data["date_creation"] == "2026-08-27"
    assert data["date_modification"] == "2026-08-27"
    assert data["actif"] == 1


def test_normalisation_refuse_type_inconnu_et_nom_vide():
    try:
        TIERS.NormaliserStructure({"type_structure": "bidule", "nom": "X"}, creation=True)
        assert False, "type inconnu accepté"
    except ValueError:
        pass

    try:
        TIERS.NormaliserStructure({"type_structure": "ecole", "nom": "   "}, creation=True)
        assert False, "nom vide accepté"
    except ValueError:
        pass


def test_creation_structure_utilise_uniquement_le_schema_canonique():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    ID = gestion.CreerStructure({
        "type_structure": "mairie_collectivite",
        "nom": "Mairie de Test",
        "siret": "12345678900012",
        "champ_inconnu": "ne doit pas partir en base",
    }, date=datetime.date(2026, 8, 27))

    assert ID == 42
    table, paires, commit = db.insertions[0]
    assert table == "structures"
    champs = [champ for champ, valeur in paires]
    assert "uid" in champs
    assert "champ_inconnu" not in champs
    assert set(champs).issubset(set(SCHEMA.GetChamps("structures")))
    assert commit is True


def test_mise_a_jour_partielle_structure_ne_vide_pas_les_autres_champs():
    data = TIERS.NormaliserStructure({"actif": 0}, date=datetime.date(2026, 8, 27), creation=False)
    assert data == {"actif": 0, "date_modification": "2026-08-27"}

    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    assert gestion.ArchiverStructure(12, date=datetime.date(2026, 8, 27)) is True
    table, paires, cle, ID, commit = db.maj[0]
    assert table == "structures"
    assert cle == "IDstructure"
    assert ID == 12
    assert ("actif", 0) in paires
    assert not any(champ in ("nom", "mail", "rue", "siret") for champ, valeur in paires)
    assert commit is True


def test_contact_exige_structure_et_identite_minimale():
    try:
        TIERS.NormaliserContact({"nom": "Dupont"})
        assert False, "contact sans structure accepté"
    except ValueError:
        pass

    try:
        TIERS.NormaliserContact({"IDstructure": 1})
        assert False, "contact vide accepté"
    except ValueError:
        pass

    contact = TIERS.NormaliserContact({
        "IDstructure": 1,
        "fonction": " Direction ",
        "mail": " direction@example.org ",
        "contact_principal": True,
    })
    assert contact["fonction"] == "Direction"
    assert contact["mail"] == "direction@example.org"
    assert contact["contact_principal"] == 1
    assert contact["actif"] == 1


def test_mise_a_jour_partielle_contact_ne_vide_pas_identite():
    data = TIERS.NormaliserContact({"mail": " new@example.org "}, creation=False)
    assert data == {"mail": "new@example.org"}

    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    assert gestion.ArchiverContact(22) is True
    table, paires, cle, ID, commit = db.maj[0]
    assert table == "structures_contacts"
    assert paires == [("actif", 0)]
    assert cle == "IDcontact"
    assert ID == 22
    assert commit is True


def test_crud_minimal_contacts():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    ID = gestion.CreerContact({
        "IDstructure": 7,
        "nom": "Martin",
        "prenom": "Alice",
        "fonction": "Facturation",
    })
    assert ID == 42
    table, paires, _ = db.insertions[0]
    assert table == "structures_contacts"
    assert ("IDstructure", 7) in paires
    assert ("actif", 1) in paires


def test_lister_structures_filtre_actives_par_defaut():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    db.resultats = [tuple([3] + ["x"] * len(TIERS.CHAMPS_STRUCTURE))]
    resultats = gestion.ListerStructures()
    assert "WHERE actif=1" in db.requetes[-1]
    assert resultats[0]["IDstructure"] == 3


def test_lister_contacts_est_borne_a_la_structure():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    db.resultats = []
    assert gestion.ListerContacts(9) == []
    assert "WHERE IDstructure=9" in db.requetes[-1]
    assert "AND actif=1" in db.requetes[-1]
