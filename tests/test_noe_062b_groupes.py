# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _charger_module(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TIERS = _charger_module("noethys/Utils/UTILS_Tiers.py", "UTILS_Tiers_noe062b_groupes")
SCHEMA = _charger_module("noethys/Data/DATA_Structures.py", "DATA_Structures_noe062b_groupes")


class FakeDB(object):
    def __init__(self):
        self.insertions = []
        self.maj = []
        self.requetes = []
        self.resultats = []

    def ReqInsert(self, table, donnees, commit=True):
        self.insertions.append((table, list(donnees), commit))
        return 51

    def ReqMAJ(self, table, donnees, cle, ID, IDestChaine=False, commit=True):
        self.maj.append((table, list(donnees), cle, ID, commit))
        return True

    def ExecuterReq(self, req):
        self.requetes.append(req)
        return 1

    def ResultatReq(self):
        return list(self.resultats)


def test_schema_groupe_reste_libre_et_rattache_a_une_structure():
    champs = SCHEMA.GetChamps("structures_groupes")
    assert champs == ("IDgroupe_structure", "IDstructure", "nom", "actif", "memo")
    assert "type_groupe" not in champs


def test_normaliser_groupe_exige_structure_et_nom():
    for donnees in (
        {"nom": "CM1"},
        {"IDstructure": 7, "nom": "   "},
    ):
        try:
            TIERS.NormaliserGroupe(donnees, creation=True)
            assert False, "groupe invalide accepté"
        except ValueError:
            pass

    groupe = TIERS.NormaliserGroupe({
        "IDstructure": 7,
        "nom": "  Section badminton  ",
        "memo": "  Créneau du mardi  ",
    })
    assert groupe == {
        "IDstructure": 7,
        "nom": "Section badminton",
        "actif": 1,
        "memo": "Créneau du mardi",
    }


def test_mise_a_jour_partielle_groupe_ne_vide_pas_le_libelle():
    assert TIERS.NormaliserGroupe({"memo": " Nouveau mémo "}, creation=False) == {
        "memo": "Nouveau mémo",
    }
    try:
        TIERS.NormaliserGroupe({"nom": " "}, creation=False)
        assert False, "nom vide accepté en modification"
    except ValueError:
        pass


def test_crud_groupe_utilise_uniquement_le_schema_canonique():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    ID = gestion.CreerGroupe({
        "IDstructure": 12,
        "nom": "CM2",
        "memo": "Classe de Mme Martin",
        "champ_inconnu": "ignoré",
    })

    assert ID == 51
    table, paires, commit = db.insertions[0]
    assert table == "structures_groupes"
    assert ("IDstructure", 12) in paires
    assert ("nom", "CM2") in paires
    assert ("actif", 1) in paires
    assert "champ_inconnu" not in [champ for champ, valeur in paires]
    assert set(champ for champ, valeur in paires).issubset(set(TIERS.CHAMPS_GROUPE))
    assert commit is True


def test_archivage_groupe_est_non_destructif():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    assert gestion.ArchiverGroupe(8) is True

    table, paires, cle, ID, commit = db.maj[0]
    assert table == "structures_groupes"
    assert paires == [("actif", 0)]
    assert cle == "IDgroupe_structure"
    assert ID == 8
    assert commit is True


def test_lire_groupe_reconstruit_un_dictionnaire_stable():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    db.resultats = [(4, 9, "Service jeunesse", 1, "Référent mairie")]

    groupe = gestion.LireGroupe(4)
    assert "WHERE IDgroupe_structure=4" in db.requetes[-1]
    assert groupe == {
        "IDgroupe_structure": 4,
        "IDstructure": 9,
        "nom": "Service jeunesse",
        "actif": 1,
        "memo": "Référent mairie",
    }


def test_lister_groupes_est_borne_a_la_structure_et_aux_actifs():
    db = FakeDB()
    gestion = TIERS.GestionnaireTiers(db)
    db.resultats = [(3, 15, "Section football", 1, "")]

    resultats = gestion.ListerGroupes(15)
    req = db.requetes[-1]
    assert "WHERE IDstructure=15" in req
    assert "AND actif=1" in req
    assert "ORDER BY nom" in req
    assert resultats[0]["IDgroupe_structure"] == 3
    assert resultats[0]["nom"] == "Section football"


def test_lister_groupes_refuse_un_rattachement_vide():
    gestion = TIERS.GestionnaireTiers(FakeDB())
    try:
        gestion.ListerGroupes(None)
        assert False, "liste de groupes sans structure acceptée"
    except ValueError:
        pass
