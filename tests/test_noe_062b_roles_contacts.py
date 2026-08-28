# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _charger_module(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TIERS = _charger_module("noethys/Utils/UTILS_Tiers.py", "UTILS_Tiers_noe062b_roles")


class FakeDB(object):
    def __init__(self):
        self.insertions = []
        self.suppressions = []
        self.requetes = []
        self.resultats = []

    def ReqInsert(self, table, donnees, commit=True):
        self.insertions.append((table, list(donnees), commit))
        return 42

    def ReqDEL(self, table, cle, ID, commit=True, IDestChaine=False):
        self.suppressions.append((table, cle, ID, commit, IDestChaine))
        return True

    def ExecuterReq(self, req):
        self.requetes.append(req)
        return 1

    def ResultatReq(self):
        return list(self.resultats)


def test_normaliser_role_contact_valide_identifiant_et_vocabulaire():
    data = TIERS.NormaliserRoleContact({"IDcontact": "7", "role": " facturation "})
    assert data == {"IDcontact": 7, "role": "facturation"}


def test_normaliser_role_contact_refuse_contact_ou_role_invalide():
    try:
        TIERS.NormaliserRoleContact({"role": "planning"})
        assert False, "rôle sans contact accepté"
    except ValueError:
        pass

    try:
        TIERS.NormaliserRoleContact({"IDcontact": 3, "role": "super_admin"})
        assert False, "rôle hors vocabulaire accepté"
    except ValueError:
        pass


def test_ajouter_role_contact_insere_un_lien_canonique():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)

    IDrole = gestion.AjouterRoleContact(7, "convention")

    assert IDrole == 42
    assert "WHERE IDcontact=7 AND role='convention'" in db.requetes[-1]
    table, paires, commit = db.insertions[0]
    assert table == "structures_roles_contacts"
    assert paires == [("IDcontact", 7), ("role", "convention")]
    assert commit is True


def test_ajouter_role_contact_est_idempotent():
    db = FakeDB()
    db.resultats = [(91,)]
    gestion = TIERS.GestionnaireTiers(db)

    assert gestion.AjouterRoleContact(7, "planning") == 91
    assert db.insertions == []


def test_lister_roles_contact_reste_borne_au_contact():
    db = FakeDB()
    db.resultats = [
        (5, 8, "facturation"),
        (6, 8, "planning"),
    ]
    gestion = TIERS.GestionnaireTiers(db)

    roles = gestion.ListerRolesContact(8)

    assert "WHERE IDcontact=8" in db.requetes[-1]
    assert [role["role"] for role in roles] == ["facturation", "planning"]
    assert all(role["IDcontact"] == 8 for role in roles)


def test_lister_roles_contact_refuse_identifiant_vide():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    try:
        gestion.ListerRolesContact(None)
        assert False, "IDcontact vide accepté"
    except ValueError:
        pass
    assert db.requetes == []


def test_supprimer_role_contact_ne_supprime_jamais_le_contact():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)

    assert gestion.SupprimerRoleContact(12) is True
    assert db.suppressions == [
        ("structures_roles_contacts", "IDrole_contact", 12, True, False),
    ]
